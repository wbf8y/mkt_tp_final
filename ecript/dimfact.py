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
	# Try staging parquet/csv first, then raw csv
	p_parquet = STAGING_DIR / f"{name}.parquet"
	p_csv = STAGING_DIR / f"{name}.csv"
	p_raw = RAW_DIR / f"{name}.csv"
	if p_parquet.exists():
		try:
			return pd.read_parquet(p_parquet)
		except Exception:
			pass
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
	p_parquet = KIMBALL_DIR / f"{name}.parquet"
	p_csv = KIMBALL_DIR / f"{name}.csv"
	# write parquet if possible
	try:
		df.to_parquet(p_parquet, index=False)
	except Exception:
		pass
	df.to_csv(p_csv, index=False)


def build_dimensions(data: dict) -> dict:
	dims = {}
	# dim_customer
	c = data.get('customer', pd.DataFrame())
	if not c.empty:
		cols = [x for x in ['customer_id','first_name','last_name','email','store_id','province_id'] if x in c.columns]
		dims['dim_customer'] = c[cols].drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_customer'] = pd.DataFrame()

	# dim_product
	p = data.get('product', pd.DataFrame())
	cat = data.get('product_category', pd.DataFrame())
	if not p.empty:
		cols = [x for x in ['product_id','product_name','product_category_id','price'] if x in p.columns]
		prod = p.copy()
		if not cat.empty and 'product_category_id' in prod.columns and 'product_category_id' in cat.columns:
			prod = prod.merge(cat[['product_category_id','product_category_name']].drop_duplicates(), on='product_category_id', how='left')
		keep = cols + [c for c in ['product_category_name'] if c in prod.columns]
		dims['dim_product'] = prod[keep].drop_duplicates().reset_index(drop=True)
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
		cols = [x for x in ['province_id','province_name','country'] if x in prov.columns]
		dims['dim_province'] = prov[cols].drop_duplicates().reset_index(drop=True)
	else:
		dims['dim_province'] = pd.DataFrame()

	# dim_channel
	ch = data.get('channel', pd.DataFrame())
	if not ch.empty:
		cols = [x for x in ['channel_id','channel_name','channel_type'] if x in ch.columns]
		dims['dim_channel'] = ch[cols].drop_duplicates().reset_index(drop=True)
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
			facts['fact_sales_order'] = df.drop_duplicates(subset=['order_id']).reset_index(drop=True)
		else:
			facts['fact_sales_order'] = df
	else:
		facts['fact_sales_order'] = pd.DataFrame()

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

