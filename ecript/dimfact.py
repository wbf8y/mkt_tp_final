"""Construye tablas Dim y Fact en formato Kimball a partir de `denormalized/staging/`.

Lee primero `denormalized/staging/<name>.csv` o `.parquet`, y si no existe usa `raw/<name>.csv`.
Genera salida en `denormalized/kimball/` en CSV y, si está disponible, Parquet.
"""
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
STAGING_DIR = ROOT / "denormalized" / "staging"
RAW_DIR = ROOT / "raw"
KIMBALL_DIR = ROOT / "denormalized" / "kimball"
KIMBALL_DIR.mkdir(parents=True, exist_ok=True)


def read_table(name: str) -> pd.DataFrame:
	p_csv = STAGING_DIR / f"{name}.csv"
	p_raw = RAW_DIR / f"{name}.csv"
	if p_csv.exists():
		try:
			return pd.read_csv(p_csv)
		except Exception:
			pass
	if p_raw.exists():
		try:
			return pd.read_csv(p_raw)
		except Exception:
			pass
	return pd.DataFrame()


def write_table(df: pd.DataFrame, name: str):
	if df is None or df.empty:
		return
	p_csv = KIMBALL_DIR / f"{name}.csv"
	# prepare a copy for safe formatting
	tmp = df.copy()
	# format province_id to avoid trailing .0 in CSV
	if 'province_id' in tmp.columns:
		# coerce to numeric then to pandas nullable int, then to string (empty for NA)
		tmp['province_id'] = pd.to_numeric(tmp['province_id'], errors='coerce')
		try:
			tmp['province_id'] = tmp['province_id'].astype('Int64')
		except Exception:
			# fallback: convert floats that are whole numbers to int where possible
			tmp['province_id'] = tmp['province_id'].apply(lambda x: int(x) if pd.notna(x) and float(x).is_integer() else pd.NA)
		# convert to string and replace <NA> with empty
		tmp['province_id'] = tmp['province_id'].astype('string').fillna('')
	# write CSV
	tmp.to_csv(p_csv, index=False)


def build_dimensions(data: dict) -> dict:
	dims = {}
	# dim_customer
	c = data.get('customer', pd.DataFrame())
	if not c.empty:
		cols = [x for x in ['customer_id','first_name','last_name','email','store_id','province_id'] if x in c.columns]
		dims['dim_customer'] = c[cols].drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_customer'] = pd.DataFrame()

	# dim_product (normalize possible column names)
	p = data.get('product', pd.DataFrame())
	cat = data.get('product_category', pd.DataFrame())
	if not p.empty:
		df = p.copy()
		# detect id, name, category id, price columns
		id_col = next((c for c in ['product_id','id','sku'] if c in df.columns), None)
		name_col = next((c for c in ['product_name','name','title'] if c in df.columns), None)
		cat_col = next((c for c in ['product_category_id','category_id','product_category'] if c in df.columns), None)
		price_col = next((c for c in ['price','list_price','unit_price'] if c in df.columns), None)
		prod = pd.DataFrame()
		prod['product_id'] = df[id_col] if id_col else df.index.astype(str)
		prod['product_name'] = df[name_col] if name_col else pd.NA
		if cat_col:
			prod['product_category_id'] = df[cat_col]
		if price_col:
			prod['price'] = pd.to_numeric(df[price_col], errors='coerce')
		# enrich with category name if available (normalize cat columns)
		if not cat.empty:
			cat_df = cat.copy()
			cat_id_col = next((c for c in ['product_category_id','category_id','id'] if c in cat_df.columns), None)
			cat_name_col = next((c for c in ['product_category_name','name','category_name'] if c in cat_df.columns), None)
			if cat_id_col and cat_name_col:
				cat_df = cat_df[[cat_id_col, cat_name_col]].drop_duplicates()
				cat_df.columns = ['product_category_id','product_category_name']
				if 'product_category_id' in prod.columns:
					prod = prod.merge(cat_df, on='product_category_id', how='left')
		# final cleanup
		dims['dim_product'] = prod.drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_product'] = pd.DataFrame()

	# dim_store
	s = data.get('store', pd.DataFrame())
	if not s.empty:
		cols = [x for x in ['store_id','store_name','address_id','province_id'] if x in s.columns]
		dims['dim_store'] = s[cols].drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_store'] = pd.DataFrame()

	# dim_address
	a = data.get('address', pd.DataFrame())
	if not a.empty:
		cols = [x for x in ['address_id','address_line1','address_line2','city','postal_code','province_id'] if x in a.columns]
		dims['dim_address'] = a[cols].drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_address'] = pd.DataFrame()

	# dim_province
	prov = data.get('province', pd.DataFrame())
	if not prov.empty:
		cols = [x for x in ['province_id','name','code'] if x in prov.columns]
		dims['dim_province'] = prov[cols].drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_province'] = pd.DataFrame()

	# dim_channel
	ch = data.get('channel', pd.DataFrame())
	if not ch.empty:
		# Normalize possible column names: prefer channel_id, channel_name, channel_type
		df = ch.copy()
		# find id column
		id_col = next((c for c in ['channel_id', 'id'] if c in df.columns), None)
		name_col = next((c for c in ['channel_name', 'name', 'description', 'label'] if c in df.columns), None)
		type_col = next((c for c in ['channel_type', 'code', 'type'] if c in df.columns), None)
		# build normalized frame
		norm = pd.DataFrame()
		if id_col:
			norm['channel_id'] = df[id_col]
		else:
			# if no id, try to create one from index
			norm['channel_id'] = df.index.astype(str)
		if name_col:
			norm['channel_name'] = df[name_col]
		else:
			norm['channel_name'] = pd.NA
		if type_col:
			norm['channel_type'] = df[type_col]
		else:
			norm['channel_type'] = pd.NA
		dims['dim_channel'] = norm.drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_channel'] = pd.DataFrame()

	return dims


def build_facts(data: dict) -> dict:
	facts = {}
	so = data.get('sales_order', pd.DataFrame())
	soi = data.get('sales_order_item', pd.DataFrame())
	pay = data.get('payment', pd.DataFrame())
	shp = data.get('shipment', pd.DataFrame())
	web = data.get('web_session', pd.DataFrame())
	nps = data.get('nps_response', pd.DataFrame())

	# fact_sales_order: keep orders with basic metrics
	if not so.empty:
		df = so.copy()
		# ensure order_id exists
		if 'order_id' in df.columns:
			# try to coerce totals
			for c in ['total','grand_total','amount']:
				if c in df.columns:
					df[c] = pd.to_numeric(df[c], errors='coerce')
			# derive province_id from store -> address -> customer (fallbacks)
			# from store: try direct province_id, otherwise use store.address_id -> address.province_id
			if 'store' in data and not data['store'].empty:
				store_df = data['store'].copy()
				# prefer existing province_id in store
				if 'province_id' in store_df.columns:
					store_map = store_df[['store_id','province_id']].drop_duplicates().rename(columns={'province_id':'store_province_id'})
				else:
					# try via address_id
					if 'address' in data and not data['address'].empty and 'address_id' in store_df.columns:
						addr_map = data['address'][['address_id','province_id']].drop_duplicates()
						store_map = store_df[['store_id','address_id']].drop_duplicates().merge(
							addr_map, left_on='address_id', right_on='address_id', how='left'
						).rename(columns={'province_id':'store_province_id'})
					else:
						store_map = store_df[['store_id']].drop_duplicates()
				# coerce id types to string to avoid float/int mismatch
				if 'store_id' in store_map.columns:
					store_map['store_id'] = store_map['store_id'].astype(str)
				if 'store_id' in df.columns:
					df['store_id'] = df['store_id'].astype(str)
					df = df.merge(store_map, on='store_id', how='left')
			# from shipping address
			if 'address' in data and not data['address'].empty:
				addr = data['address'][['address_id','province_id']].drop_duplicates()
				# shipping
				if 'shipping_address_id' in df.columns:
					addr_ship = addr.rename(columns={'address_id':'shipping_address_id', 'province_id':'shipping_province_id'})
					# coerce types
					addr_ship['shipping_address_id'] = addr_ship['shipping_address_id'].astype(str)
					df['shipping_address_id'] = df['shipping_address_id'].astype(str)
					df = df.merge(addr_ship, on='shipping_address_id', how='left')
				# billing
				if 'billing_address_id' in df.columns:
					addr_bill = addr.rename(columns={'address_id':'billing_address_id', 'province_id':'billing_province_id'})
					# coerce types
					addr_bill['billing_address_id'] = addr_bill['billing_address_id'].astype(str)
					df['billing_address_id'] = df['billing_address_id'].astype(str)
					df = df.merge(addr_bill, on='billing_address_id', how='left')
			# from customer (only if customer has province info)
			if 'customer' in data and not data['customer'].empty and 'customer_id' in data['customer'].columns and 'customer_id' in df.columns:
				cust_df = data['customer']
				if 'province_id' in cust_df.columns:
					cust_map = cust_df[['customer_id','province_id']].drop_duplicates().rename(columns={'province_id':'customer_province_id'})
					cust_map['customer_id'] = cust_map['customer_id'].astype(str)
					df['customer_id'] = df['customer_id'].astype(str)
					df = df.merge(cust_map, on='customer_id', how='left')
				# else: no customer province info available
			# choose province priority: store > shipping address > billing address > customer
			priority_cols = ['store_province_id','shipping_province_id','billing_province_id','customer_province_id']
			# create province_id column
			df['province_id'] = pd.NA
			for col in priority_cols:
				if col in df.columns:
					df['province_id'] = df['province_id'].fillna(df[col])
			# drop helper cols if present
			for col in priority_cols:
				if col in df.columns:
					df = df.drop(columns=[col])
			facts['fact_sales_order'] = df.drop_duplicates(subset=['order_id']).reset_index(drop=True)
		else:
			facts['fact_sales_order'] = so.copy()
	else:
		facts['fact_sales_order'] = pd.DataFrame()

	# Enrich fact_sales_order with province data if available
	if 'fact_sales_order' in facts and not facts['fact_sales_order'].empty:
		fso = facts['fact_sales_order']
		if 'province' in data and not data['province'].empty and 'province_id' in fso.columns:
			prov = data['province']
			# normalize province id column name
			prov_id_col = next((c for c in ['province_id','id'] if c in prov.columns), 'province_id')
			prov_name_col = next((c for c in ['name','province_name'] if c in prov.columns), 'name')
			prov_code_col = next((c for c in ['code','province_code'] if c in prov.columns), 'code')
			prov_map = prov[[prov_id_col, prov_name_col, prov_code_col]].drop_duplicates()
			prov_map.columns = ['province_id','province_name','province_code']
			# coerce types
			prov_map['province_id'] = prov_map['province_id'].astype(str)
			fso['province_id'] = fso['province_id'].astype(str)
			fso = fso.merge(prov_map, on='province_id', how='left')
			# convert province_id to numeric and then to nullable integer to avoid .0 in CSV
			if 'province_id' in fso.columns:
				fso['province_id'] = pd.to_numeric(fso['province_id'], errors='coerce')
				# use pandas nullable integer so missing values are preserved
				fso['province_id'] = fso['province_id'].astype('Int64')
			facts['fact_sales_order'] = fso

	# fact_sales_item
	if not soi.empty:
		df = soi.copy()
		# attempt to enrich with product info if available
		if 'product' in data and not data['product'].empty and 'product_id' in df.columns:
			df = df.merge(data['product'], on='product_id', how='left')
		if 'order_id' in df.columns and not so.empty:
			df = df.merge(so[['order_id','order_date']].drop_duplicates(), on='order_id', how='left')
		# compute line_total
		if 'quantity' in df.columns and 'price' in df.columns:
			df['line_total'] = pd.to_numeric(df['quantity'], errors='coerce') * pd.to_numeric(df['price'], errors='coerce')
		facts['fact_sales_item'] = df.reset_index(drop=True)
	else:
		facts['fact_sales_item'] = pd.DataFrame()

	# fact_payment
	facts['fact_payment'] = pay.reset_index(drop=True) if not pay.empty else pd.DataFrame()

	# fact_shipment
	facts['fact_shipment'] = shp.reset_index(drop=True) if not shp.empty else pd.DataFrame()

	# fact_web_session
	facts['fact_web_session'] = web.reset_index(drop=True) if not web.empty else pd.DataFrame()

	# fact_nps_response
	facts['fact_nps_response'] = nps.reset_index(drop=True) if not nps.empty else pd.DataFrame()

	return facts


def main():
	names = ['customer','product','product_category','store','address','province','channel','sales_order','sales_order_item','payment','shipment','web_session','nps_response']
	data = {n: read_table(n) for n in names}

	dims = build_dimensions(data)
	facts = build_facts(data)

	# write dims
	for k, df in dims.items():
		write_table(df, k)

	# write facts
	for k, df in facts.items():
		write_table(df, k)

	print('Kimball creado en:', KIMBALL_DIR)


if __name__ == '__main__':
	main()

