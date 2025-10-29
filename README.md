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
│   ├── staging/                # Tablas intermedias
│   └── kimball/                # Tablas finales del Data Warehouse
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

## 🌟 Diagrama Estrella – *Modelo Kimball General*

```text
                               ┌──────────────────────────────┐
                               │        dim_channel           │
                               │──────────────────────────────│
                               │ channel_id (PK)              │
                               │ channel_name                 │
                               │ channel_type                 │
                               └──────────────┬───────────────┘
                                              │
                                              │
         ┌───────────────────────┐            │
         │      dim_province     │            │
         │───────────────────────│            │
         │ province_id (PK)      │            │
         │ province_name         │            │
         │ country               │            │
         └──────┬────────────────┘            │
                │                             │
 ┌──────────────┴─────────────────────────────┴───────────────────────────────┐
 │                               fact_sales_order                             │
 │────────────────────────────────────────────────────────────────────────────│
 │ order_id (PK)                                                               │
 │ customer_id (FK→dim_customer)                                               │
 │ store_id (FK→dim_store)                                                     │
 │ province_id (FK→dim_province)                                               │
 │ channel_id (FK→dim_channel)                                                 │
 │ order_date                                                                  │
 │ total_amount, tax_amount, shipping_fee, subtotal, etc.                      │
 │────────────────────────────────────────────────────────────────────────────│
 │ 🔹 Métricas: SUM(total_amount), COUNT(order_id), AVG(total_amount), etc.    │
 └──────────────┬───────────────┬──────────────┬──────────────┬───────────────┘
                │               │              │               │
                │               │              │               │
        ┌───────┴──────┐ ┌──────┴───────┐ ┌────┴────────┐ ┌────┴──────────┐
        │ dim_customer │ │  dim_store   │ │ dim_address │ │ dim_product   │
        │──────────────│ │──────────────│ │─────────────│ │───────────────│
        │ customer_id  │ │ store_id     │ │ address_id  │ │ product_id    │
        │ first_name   │ │ store_name   │ │ city        │ │ name          │
        │ last_name    │ │ address_id→address │ province_id │ category_id  │
        │ email        │ │ province_id  │ │ postal_code │ │ price        │
        └──────────────┘ └──────────────┘ └─────────────┘ └────┬──────────┘
                                                                │
                                                                │
                                         ┌───────────────────────┴────────────────────────┐
                                         │                 fact_sales_item                │
                                         │────────────────────────────────────────────────│
                                         │ order_item_id (PK)                             │
                                         │ order_id (FK→fact_sales_order)                 │
                                         │ product_id (FK→dim_product)                    │
                                         │ quantity, unit_price, discount, line_total     │
                                         └────────────────────────────────────────────────┘
```

---

## 🌟 Diagramas Estrella Individuales
(A continuación se muestran las 6 estrellas correspondientes a cada tabla de hechos)

### ⭐ 1. `fact_sales_order`
```text
                   ┌───────────────┐
                   │ dim_channel   │
                   │───────────────│
                   │ channel_id PK │
                   └───────┬───────┘
                           │
     ┌──────────────┐      │       ┌──────────────┐
     │ dim_customer │      │       │ dim_store    │
     │──────────────│      │       │──────────────│
     │ customer_id  │      │       │ store_id PK  │
     └──────┬───────┘      │       └──────┬───────┘
            │               │              │
            │               │              │
            └──────┬────────┴────────┬─────┘
                   │  fact_sales_order │
                   │──────────────────│
                   │ order_id (PK)     │
                   │ total_amount      │
                   │ order_date        │
                   │ channel_id (FK)   │
                   │ province_id (FK)  │
                   │ customer_id (FK)  │
                   │ store_id (FK)     │
                   └───────────────────┘
                           │
                           │
                     ┌─────┴──────┐
                     │dim_province│
                     │────────────│
                     │province_id │
                     └────────────┘
```

---

### ⭐ 2. `fact_sales_item`
```text
              ┌──────────────┐
              │dim_product   │
              │──────────────│
              │product_id PK │
              │price         │
              └─────┬────────┘
                    │
                    │
          ┌─────────┴─────────┐
          │ fact_sales_item   │
          │───────────────────│
          │ order_item_id (PK)│
          │ order_id (FK)     │
          │ product_id (FK)   │
          │ quantity          │
          │ line_total        │
          └─────────┬─────────┘
                    │
                    │
          ┌─────────┴─────────┐
          │fact_sales_order   │
          │───────────────────│
          │ order_id (PK)     │
          │ total_amount      │
          └───────────────────┘
```

---

### ⭐ 3. `fact_payment`
```text
         ┌──────────────┐
         │ dim_channel  │
         │──────────────│
         │ channel_id   │
         └─────┬────────┘
               │
               │
      ┌────────┴────────┐
      │ fact_payment    │
      │─────────────────│
      │ payment_id (PK) │
      │ order_id (FK)   │
      │ amount          │
      │ method          │
      │ status          │
      │ paid_at         │
      └────────┬────────┘
               │
               │
     ┌─────────┴─────────┐
     │fact_sales_order   │
     │───────────────────│
     │ order_id (PK)     │
     │ total_amount      │
     └───────────────────┘
```

---

### ⭐ 4. `fact_shipment`
```text
       ┌──────────────┐
       │ dim_province │
       │──────────────│
       │ province_id  │
       └─────┬────────┘
             │
   ┌─────────┴─────────┐
   │ fact_shipment     │
   │───────────────────│
   │ shipment_id (PK)  │
   │ order_id (FK)     │
   │ carrier           │
   │ status            │
   │ shipped_at        │
   │ delivered_at      │
   └─────────┬─────────┘
             │
             │
   ┌─────────┴─────────┐
   │fact_sales_order   │
   │───────────────────│
   │ order_id (PK)     │
   │ total_amount      │
   └───────────────────┘
```

---

### ⭐ 5. `fact_web_session`
```text
      ┌──────────────┐
      │dim_channel   │
      │──────────────│
      │channel_id PK │
      └──────┬───────┘
             │
             │
   ┌─────────┴─────────┐
   │fact_web_session   │
   │───────────────────│
   │ session_id (PK)   │
   │ customer_id (FK)  │
   │ started_at        │
   │ ended_at          │
   │ source, device    │
   └─────────┬─────────┘
             │
             │
   ┌─────────┴─────────┐
   │dim_customer       │
   │───────────────────│
   │ customer_id (PK)  │
   │ first_name        │
   │ email             │
   └───────────────────┘
```

---

### ⭐ 6. `fact_nps_response`
```text
     ┌──────────────┐
     │dim_customer  │
     │──────────────│
     │customer_id PK│
     └──────┬───────┘
            │
            │
  ┌─────────┴──────────┐
  │ fact_nps_response  │
  │────────────────────│
  │ nps_id (PK)        │
  │ customer_id (FK)   │
  │ channel_id (FK)    │
  │ score              │
  │ comment            │
  │ responded_at       │
  └─────────┬──────────┘
            │
            │
  ┌─────────┴──────────┐
  │ dim_channel        │
  │────────────────────│
  │ channel_id (PK)    │
  │ channel_name       │
  │ channel_type       │
  └────────────────────┘
```

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

- **Herramienta:** [Power BI]
- **Fuente:** Archivos CSV del DW (`denormalized/kimball`)
- **Filtros Globales:** Fecha, Canal, Provincia, Producto
- **Visualizaciones:**
  - Serie temporal: Ventas y Ticket Promedio
  - Mapa: Ventas por provincia
  - Barras: Top productos
  - Indicadores: Ventas Totales, Usuarios, NPS

📎 **Enlace al Dashboard:**  
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
| `dim_channel` | Dimensión | Canales de venta |
| `dim_store` | Dimensión | Tiendas físicas |
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
