# 📦 Inventory Aging Analyzer / Wiekowanie Zapasów

A professional bilingual (🇵🇱 Polish / 🇬🇧 English) Streamlit application for inventory aging analysis.

---

## Features

- **Bilingual UI** — switch between Polish and English at any time
- **File upload** — supports `.xlsx`, `.xls`, `.csv`
- **Flexible column mapping** — no hardcoded column names
- **Two aging methods** — by material index, or by material index + batch/lot
- **Default & custom aging buckets** — define your own day ranges
- **Full validation** — missing dates, negative quantities, missing batch numbers
- **Interactive dashboard** — KPI cards and Plotly charts
- **Excel export** — multi-sheet report with corporate formatting, conditional formatting, freeze panes, filters

---

## Project Structure

```
inventory_aging/
├── app.py                   # Main Streamlit app
├── requirements.txt
├── README.md
├── modules/
│   ├── __init__.py
│   ├── translations.py      # PL/EN translations
│   ├── data_loader.py       # File reading (xlsx, xls, csv)
│   ├── aging_engine.py      # Core aging calculation logic
│   ├── excel_export.py      # Excel report generation
│   ├── ui_components.py     # Charts and UI widgets
│   └── styling.py           # Custom CSS
└── utils/
    ├── __init__.py
    └── validators.py        # Data and config validation
```

---

## Installation

### 1. Clone or download the project

```bash
git clone <repo-url>
cd inventory_aging
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

## Usage Guide

### Step 1 — Upload a file
Upload your inventory file (`.xlsx`, `.xls`, or `.csv`) using the file uploader.

### Step 2 — Configure
In the **sidebar**:
- Select **language** (Polski / English)
- Choose **aging method**: by material index, or by material index + batch
- Set the **aging date** (calculation reference date)
- Choose **default** or **custom aging buckets**

In the **main area**:
- Map your file's columns to the required fields
- Mandatory: Material Index, Receipt Date, Material Name, Document Number, Quantity
- Optional: Value, Warehouse
- Conditional (batch aging only): Batch/Lot Number

### Step 3 — Calculate
Click **"Przelicz wiekowanie" / "Calculate Aging"**.

### Step 4 — Review results
Tabs:
- **Dashboard** — KPI cards + charts
- **Detailed Data** — all rows enriched with age, bucket, etc.
- **Quantity Summary** — pivot by material and bucket
- **Value Summary** — pivot by value (if value column mapped)
- **Warehouse Summary** — by warehouse (if warehouse column mapped)
- **Batch Summary** — by batch (if batch aging selected)
- **Validation** — list of data quality issues

### Step 5 — Download Excel
Click the download button to get a fully formatted `.xlsx` report with:
- All summary sheets
- Corporate formatting
- Conditional formatting (orange = >1 year, red = >2 years)
- Freeze panes and auto-filters

---

## Input File Format

Your file should contain at minimum:
| Column | Description |
|--------|-------------|
| Material Index | Unique material/SKU code |
| Receipt Date | Date stock was received (any parseable date format) |
| Material Name | Descriptive name |
| Document Number | GR/receipt document reference |
| Quantity | Stock balance (numeric) |

Optional columns: Value (numeric), Warehouse (text), Batch/Lot (text)

Column names can be anything — you map them in the app.

---

## Default Aging Buckets

| Bucket | Days |
|--------|------|
| 0–3 months | 0–90 |
| 3–6 months | 91–180 |
| 6–9 months | 181–270 |
| 9–12 months | 271–365 |
| 1–2 years | 366–730 |
| Above 2 years | 731+ |

---

## Requirements

- Python 3.10+
- streamlit >= 1.32
- pandas >= 2.0
- openpyxl >= 3.1
- xlrd >= 2.0
- xlsxwriter >= 3.1
- plotly >= 5.18
