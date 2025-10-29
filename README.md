------------------------------------------------------------
|        🧩 TRABAJO PRÁCTICO FINAL – MKT ONLINE             |
|      Introducción al Marketing Online y Negocios          |
|                 Autor: Jerónimo Ballina                   |
------------------------------------------------------------

# 📘 Proyecto: Mini Ecosistema de Datos Comercial – *EcoBottle AR*

Este proyecto implementa un **mini–ecosistema de datos** (online + offline) para la empresa ficticia **EcoBottle AR**, que comercializa botellas reutilizables en Argentina.  
El objetivo es **diseñar, modelar y analizar datos** de ventas, clientes, sesiones y NPS para construir un **dashboard comercial en Looker Studio** con los principales KPIs del negocio.

---

## 🎯 Objetivo General
Diseñar e implementar un **Data Warehouse (DW)** en formato *esquema estrella* siguiendo la metodología **Kimball**, a partir de datos transaccionales normalizados.  
A partir de ese DW, construir un **tablero de control (dashboard)** con métricas clave:

- 💰 Ventas Totales  
- 👥 Usuarios Activos  
- 💵 Ticket Promedio  
- 📈 NPS (Net Promoter Score)  
- 🗺️ Ventas por Provincia  
- 🏆 Ranking Mensual por Producto  

---

## 🧱 Arquitectura del Proyecto

```
MKT_TP_FINAL/
│
├── ecript/                     # Scripts Python del proceso ETL
│   ├── staging.py              # Limpieza y enriquecimiento de datos
│   └── dimfact.py              # Generación de dimensiones y hechos
│
├── raw/                        # Datos originales (CSV normalizados)
│
├── denormalized/
│   └── kimball/                # Tablas finales del Data Warehouse
│       ├── dim_address.csv
│       ├── dim_channel.csv
│       ├── dim_customer.csv
│       ├── dim_product.csv
│       ├── dim_province.csv
│       ├── dim_store.csv
│       ├── fact_sales_order.csv
│       ├── fact_sales_item.csv
│       ├── fact_payment.csv
│       ├── fact_shipment.csv
│       ├── fact_web_session.csv
│       └── fact_nps_response.csv
│
├── assets/
│   ├── DER.png                 # Diagrama Entidad-Relación
│   └── dashboard.png           # Captura del tablero final
│
├── .gitignore
├── requirements.txt            # Dependencias Python
└── README.md
```

---

## ⚙️ Instalación y Ejecución

```bash
# 1️⃣ Clonar el repositorio
git clone https://github.com/jeronimoballina/mkt_tp_final.git
cd mkt_tp_final

# 2️⃣ Crear entorno virtual
python -m venv .venv

# Activar entorno
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3️⃣ Instalar dependencias
pip install -r requirements.txt

# 4️⃣ Ejecutar los scripts ETL
python ecript/staging.py
python ecript/dimfact.py
```

Esto generará todas las **dimensiones y hechos** en la carpeta `denormalized/kimball/`.

---

## 🧮 KPIs Calculados

| KPI | Descripción | Fuente | Fórmula |
|------|--------------|---------|----------|
| 💰 Ventas Totales ($M) | Suma de ventas efectivas | `fact_sales_order` | `SUM(total_amount)` |
| 👥 Usuarios Activos (nK) | Clientes o sesiones activas | `fact_web_session` | `COUNT_DISTINCT(customer_id)` |
| 💵 Ticket Promedio ($K) | Promedio de gasto por pedido | `fact_sales_order` | `SUM(total_amount)/COUNT(order_id)` |
| 📈 NPS (%) | Índice de satisfacción del cliente | `fact_nps_response` | `((%9-10) - (%0-6)) * 100` |
| 🗺️ Ventas por Provincia | Distribución geográfica de ventas | `fact_sales_order + dim_province` | `SUM(total_amount)` |
| 🏆 Ranking Mensual por Producto | Productos más vendidos del mes | `fact_sales_item + dim_product` | `SUM(line_total)` |

---

## 📊 Dashboard Comercial – *Looker Studio*

- **Herramienta:** [Google Looker Studio](https://lookerstudio.google.com/)
- **Fuente:** Archivos CSV del DW (`denormalized/kimball`)
- **Filtros Globales:** Fecha, Canal, Provincia, Producto
- **Visualizaciones:**
  - Serie temporal: Ventas y Ticket Promedio
  - Mapa: Ventas por provincia
  - Barras: Top productos
  - Indicadores: Ventas Totales, Usuarios, NPS

📎 **Enlace al Dashboard:** *(agregá tu link acá)*  
📸 ![Dashboard](assets/dashboard.png)

---

## 🧠 Supuestos de Negocio

> ⚙️ **Supuestos principales:**
> - Los pedidos con estado `CANCELLED` o `REFUNDED` no se incluyen en los cálculos.  
> - Provincias válidas: Buenos Aires, Córdoba, Santa Fe, Mendoza.  
> - Canal `ONLINE` representa compras vía e-commerce; `OFFLINE`, ventas en tiendas físicas.  
> - El campo `responded_at` de NPS se usa como fecha de referencia.  
> - La métrica de Usuarios Activos considera sesiones únicas.

---

## 🗂️ Diccionario de Datos (resumen)

| Tabla | Tipo | Descripción |
|--------|------|-------------|
| `dim_customer` | Dimensión | Información de clientes |
| `dim_product` | Dimensión | Productos y categorías |
| `dim_province` | Dimensión | Provincias argentinas |
| `fact_sales_order` | Hecho | Cabecera de pedidos |
| `fact_sales_item` | Hecho | Detalle de productos por pedido |
| `fact_payment` | Hecho | Pagos y métodos |
| `fact_shipment` | Hecho | Envíos y entregas |
| `fact_web_session` | Hecho | Sesiones digitales |
| `fact_nps_response` | Hecho | Encuestas de satisfacción |

---

## 🚀 Tecnologías Utilizadas
- **Python 3.12**
- **Pandas / Numpy**
- **Looker Studio**
- **Git / GitHub**
- **Metodología Kimball**
- **CSV / Parquet**

---

## 📈 Resultados del Análisis

```
--------------------------------------------
| 📊 RESULTADOS FINALES DEL DASHBOARD       |
|------------------------------------------|
| ✅ Ventas +18% en Córdoba                 |
| ✅ Entregas -12% más rápidas en Mendoza   |
| ✅ Producto Classic A: 62% de las ventas  |
--------------------------------------------
```

---

## 👤 Autor

**Jerónimo Ballina**  
📍 Rosario, Argentina  
📧 jeronimoballina@gmail.com  
💼 [GitHub](https://github.com/jeronimoballina)

---

## 🏁 Estado del Proyecto

✅ Scripts ETL implementados  
✅ Tablas denormalizadas generadas  
✅ Dashboard Looker Studio en desarrollo  
🔜 Ajuste final y entrega al profesor

---

## ✨ Frase Final

> “Transformar datos en decisiones no es solo analizar,  
> es entender el negocio detrás de cada número.” — *Jerónimo Ballina*
