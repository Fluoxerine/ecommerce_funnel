# Ecommerce Funnel CRO Analysis

> Quantify funnel churn, locate conversion bottlenecks, output PIE-prioritized optimization strategy

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![scipy](https://img.shields.io/badge/SciPy-Stats-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)

## Key Findings

Analysis of 5,000 sessions across 5 funnel stages. **Overall conversion: 20.2%** (1,010 / 5,000).

The **highest churn stage is Browse -> Cart (40.11% step rate)**, not Cart -> Checkout as previously assumed.

Estimated revenue loss by stage:
| Churn Stage | Lost Sessions | Loss Rate | Est. Loss |
|-------------|---------------|-----------|-----------|
| Browse -> Cart | 2,388 | 59.9% | Y119,400 |
| Cart -> Checkout | 476 | 29.8% | Y47,600 |
| Checkout -> Confirm | 113 | 10.1% | Y13,560 |

**PIE Priority**: Fix Browse->Cart first (highest PIE score), then Cart recovery, then payment flow.

## Project Structure

```
├── python/              Analysis engine (8 modules)
│   ├── config.py, data_loader.py, data_cleaning.py
│   ├── funnel_analysis.py, churn_diagnostics.py
│   ├── visualization.py, import_to_mysql.py, main.py
├── sql/                 SQL scripts (8 files, sequential)
├── docs/                Documentation (4 docs)
├── operations/          CRO optimization strategy
├── tests/               Unit tests (pytest)
├── output/charts/       10 visualizations
└── notebook/            Original exploration notebook
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure MySQL password
cp .env.example .env
# Edit .env with your MySQL password

# 3. Run Python analysis
python python/main.py

# 4. MySQL import (optional, for SQL-side analysis & Power BI)
python python/import_to_mysql.py

# 5. Run tests
pytest tests/ -v
```

## Tech Stack

| Domain | Skills |
|--------|--------|
| Data Cleaning | Pandas — dedup, null handling, outlier filtering, funnel logic validation |
| Funnel Analysis | Session-level funnel + multi-dimension drill-down (channel/device/time/country) |
| Statistical Tests | SciPy — chi-square, t-test, Cohen's d effect size |
| Churn Quantification | Cart abandonment value + PIE priority framework |
| Visualization | Matplotlib (8) + Plotly (2 interactive) |
| Data Warehouse | MySQL 8.4 (Docker) — wide table + multi-dimension queries |
| Engineering | Docker, pytest, dotenv config management |
