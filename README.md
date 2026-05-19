# E-Commerce Price Analyzer 📊

Modern end-to-end data engineering platform for e-commerce market analysis, price monitoring, and opportunity detection using Python, PostgreSQL, MinIO, Docker, Machine Learning, and Metabase.

---

# 🚀 Project Overview

This project collects e-commerce product data from online marketplaces, processes and cleans the data through a multi-layer pipeline, stores it in a data lake and PostgreSQL, performs ML-based product matching, and visualizes insights through interactive dashboards.

The platform also includes a complete data governance layer with:
- schema validation
- data quality checks
- duplicate detection
- freshness monitoring
- logging & monitoring
- lineage documentation

---

# 🏗️ Architecture

```text
Scrapers
   ↓
MinIO Bronze Layer
   ↓
Transformation & Cleaning
   ↓
Silver Layer
   ↓
PostgreSQL Warehouse
   ↓
Gold Analytics Layer
   ↓
ML Product Matching
   ↓
Metabase Dashboards
```

---

# ⚙️ Technologies Used

- Python
- PostgreSQL
- MinIO
- Docker
- Metabase
- Pandas
- PySpark
- Sentence Transformers
- Scikit-learn
- Streamlit

---

# 📂 Project Structure

```text
ecommerce-price-analyzer/
│
├── scrapers/
│   ├── jumia.py
│   └── ...
│
├── pipelines/
│   ├── transformation.py
│   ├── load_to_db.py
│   ├── gold.py
│   └── matching.py
│
├── gouvernance/
│   ├── schema_validation.py
│   ├── quality_checks.py
│   ├── monitoring.py
│   ├── lineage.md
│   └── data_dictionary.md
│
├── ml/
│   └── train_model.py
│
├── utils/
│   └── minio_client.py
│
├── dashboard/
│
├── screenshots/
│
├── config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

# 🛢️ Data Lake Architecture

The project uses a Medallion Architecture:

| Layer | Description |
|---|---|
| Bronze | Raw scraped data |
| Silver | Cleaned and validated data |
| Gold | Business-ready analytics |

---

# 🔥 Features

## ✅ Data Ingestion
- Automated web scraping
- Multi-source ingestion
- Raw data storage in MinIO

## ✅ Data Transformation
- Cleaning and normalization
- Encoding fixes
- Outlier removal
- Duplicate handling

## ✅ Data Warehouse
- PostgreSQL integration
- Incremental loading
- SQL analytics

## ✅ Machine Learning
- Semantic product matching
- SentenceTransformer embeddings
- Cosine similarity scoring

## ✅ Governance & Quality
- Schema validation
- Duplicate detection
- Quality monitoring
- Freshness checks
- Data lineage
- Logging system

## ✅ Visualization
- Interactive dashboards with Metabase
- Governance dashboard
- Business KPIs
- Brand analytics

---

# 📊 Dashboards

## Business Dashboard
- Average price by brand
- Market domination
- Min vs max price
- Price distribution

## Governance Dashboard
- Duplicate products
- Missing values
- Invalid prices
- Data freshness
- Quality score

---

# 🧠 ML Matching Pipeline

The project uses:
- Sentence Transformers (`all-MiniLM-L6-v2`)
- Cosine similarity
- Semantic matching between marketplaces

This allows intelligent matching of similar products even with different naming conventions.

---

# 🛡️ Data Governance

Implemented governance features include:

- Data quality monitoring
- Duplicate prevention
- PostgreSQL integrity constraints
- Schema validation
- Logging & observability
- Freshness tracking
- Lineage documentation

---

# 🐳 Docker

## Build image

```bash
docker build -t ecommerce-pro .
```

## Run container

```bash
docker run -p 8501:8501 ecommerce-pro
```

---

# 📈 Example SQL Governance Queries

## Duplicate Detection

```sql
SELECT
name,
COUNT(*) AS duplicates
FROM products
GROUP BY name
HAVING COUNT(*) > 1;
```

## Quality Score

```sql
SELECT
ROUND(
(
COUNT(DISTINCT name)::numeric / COUNT(*)::numeric
) * 100,
2
) AS quality_score
FROM products;
```

---

# 🚀 Future Improvements

- Airflow orchestration
- Real-time streaming
- Automated anomaly detection
- CI/CD pipeline
- Kubernetes deployment
- Advanced recommendation engine

---

# 📸 Screenshots

## Metabase Dashboard

Add screenshots here:

```text
screenshots/dashboard.png
```

## Governance Dashboard

```text
screenshots/governance.png
```

---

# 👨‍💻 Author

Amine Elquammah

---

# ⭐ GitHub

If you found this project useful, feel free to star the repository.