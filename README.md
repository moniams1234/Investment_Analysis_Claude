# FIN APPS — Investment Analysis

> **Financial Insights. Better Decisions.**
>
> A premium Streamlit application for analysing new investments and capital projects:
> Profit forecast, Balance Sheet, Working Capital, Cash Flow, IRR, NPV, Payback, Discounted Payback and ROI — with a polished, corporate-finance UI.

![logo](assets/fin_apps_logo.png)

---

## ⚠️ Important — No predefined financial assumptions

This application **does not ship with any default financial values** taken from a prior Excel model.

The app opens with:
- empty project setup,
- empty working-capital days,
- empty tax rate, discount rate, depreciation period,
- empty yearly forecast table.

**Every assumption must be entered manually by the user.** A neutral example project is available via the sidebar (*Load example/demo project*) for demonstration only — it is never loaded automatically.

---

## ✨ Features

- **9 tabs**: Executive Summary, Project Setup, Forecast Input, Profit Forecast, Balance Sheet, Cash Flow, IRR / NPV / Payback, Charts & Dashboard, Excel Export
- **Editable yearly forecast** via `st.data_editor`
- For each cost line (Materials, Direct Labour, Manufacturing Overhead, SG&A) the user may enter **either a % of sales or an absolute value**.
  *If both are entered, the absolute Value overrides the % and an info message is shown.*
- Full set of investment metrics: **IRR, NPV, Standard Payback, Discounted Payback, ROI (avg / 3y / 5y)**
- Professional **Plotly** charts (no matplotlib): trends, waterfall, cumulative cash flow, ROI bars, working-capital stack, capex vs depreciation, IRR gauge, sensitivity tornado
- **Excel export** (openpyxl) — multi-sheet, branded, freeze panes, number formats, logo on the Executive Summary
- **Save / Load** project as JSON
- **Validation** for negative sales, missing assumptions, percentages >150%, divide-by-zero, etc.
- Premium dark-burgundy UI matching the FIN APPS brand (cyan + red accents)

---

## 🗂 Folder structure

```
FIN_APPS_INVESTMENT_ANALYSIS/
├── app.py                       # Streamlit entry point
├── requirements.txt
├── README.md
├── assets/
│   └── fin_apps_logo.png        # brand logo (header / sidebar / Excel cover)
├── modules/
│   ├── calculations.py          # P&L, BS, CF, IRR, NPV, payback, ROI
│   ├── excel_export.py          # branded openpyxl workbook
│   ├── charts.py                # Plotly charts (brand palette)
│   ├── ui_components.py         # KPI cards, recommendation, validators
│   ├── styling.py               # custom CSS + chart template
│   ├── validation.py            # input sanity checks
│   └── helpers.py               # formatting + JSON I/O
├── data/
│   └── sample_project.json      # neutral demo only — NOT loaded by default
└── exports/                     # generated files (gitignored in practice)
```

---

## 🚀 Installation

```bash
git clone <your-repo-url> FIN_APPS_INVESTMENT_ANALYSIS
cd FIN_APPS_INVESTMENT_ANALYSIS
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at <http://localhost:8501>.

---

## ☁️ Deployment — Streamlit Community Cloud

1. Push the repository to GitHub.
2. Go to <https://share.streamlit.io> → **New app** → select your repo / branch / `app.py`.
3. Streamlit Cloud reads `requirements.txt` automatically.
4. (Optional) Add `.streamlit/config.toml` to lock the theme.

The app also runs unchanged on Hugging Face Spaces, Render, Railway, Azure App Service or any Docker host.

---

## 🧮 Calculation methodology

### Profit forecast (per year)
```
Material   = Material Value      if entered else Sales × Material %
Labour     = Labour Value        if entered else Sales × Labour %
MOH        = MOH Value           if entered else Sales × MOH %
SG&A       = SG&A Value          if entered else Sales × SG&A %

Gross Profit = Sales − Material
EBITDA       = Gross Profit − Labour − MOH − SG&A
Depreciation = Depreciable Capex / Useful Life       (only during useful life)
EBIT         = EBITDA − Depreciation
Taxes        = max(EBIT, 0) × Tax Rate
Net Income   = EBIT − Taxes
```

### Balance sheet
```
Receivables = Sales         / 365 × Receivable Days
Inventory   = Material Cost / 365 × Inventory  Days
Payables    = Material Cost / 365 × Payable    Days
NWC         = Receivables + Inventory − Payables
Net FA      = Gross FA − Accumulated Depreciation
Net Inv.    = Net FA + NWC
```

### Cash flow
```
Year 0:  −Capex
Year t:  Net Income + Depreciation − ΔNWC
Final year: + Residual Value (+ NWC recovery if enabled)
```

### Investment metrics
- **IRR** — `numpy_financial.irr` on the project cash-flow series
- **NPV** — Σ CFₜ / (1+r)ᵗ at the WACC / discount rate entered by the user
- **Payback** — first year where cumulative CF ≥ 0, fractional via linear interpolation
- **Discounted Payback** — identical logic on discounted cash flows
- **ROI** by year = EBIT / Average Investment; aggregated as Average / 3-year / 5-year

---

## 🎨 Branding

| Token | Value |
|---|---|
| Primary background | `#2B0000` → `#3B0000` |
| Panels / cards | `#450909` / `#5A1010` |
| Cyan accent (FIN) | `#7ED6FF` / `#8BCBFF` |
| Red accent (APPS) | `#FF2B4D` / `#D91C3C` |
| Text | `#FFFFFF` / `#D9D9D9` |
| Borders | `rgba(255,255,255,0.08)` |

The same palette drives every chart and the Excel export header styling, so PDF/Excel deliverables stay visually consistent with the dashboard.

---

## 📤 Excel export

The **Excel Export** tab generates a fully formatted `.xlsx` workbook:

| Sheet | Contents |
|---|---|
| Executive Summary | KPI table + brand logo + project meta |
| Assumptions | All Project Setup parameters |
| Forecast Input | The raw editable yearly inputs |
| P&L | Sales → Net Income with margins |
| Balance Sheet | Fixed assets + working capital |
| Cash Flow | Operational CF + cumulative |
| IRR & ROI | Summary metrics + ROI by year |
| Charts | Pointer back to the web dashboard |

Each sheet uses: branded burgundy headers, cyan/red accent fonts, freeze panes, number formats (`#,##0` / `0.0%`), bordered cells, auto-sized columns. The Executive Summary embeds the FIN APPS logo.

---

## 🧪 Validation & error handling

- Negative sales → warning
- IRR not computable (no sign change) → IRR shown as `—`, no crash
- Tax / discount rate out of [0, 1] → error
- Working-capital days < 0 → error
- Percentage fields > 150% → warning (likely entered as 35 instead of 0.35)
- Both % and Value entered → Value wins + info message
- Division by zero is guarded in every margin / ROI calculation

---

## 🧩 Bonus / extension points

- Sensitivity tornado (±10% on Sales, Materials, Discount Rate, Capex) — included
- Scenario analysis (base / best / worst), Monte Carlo, and PDF export are scaffolded conceptually and can be added by duplicating the calculation pipeline with adjusted inputs
- Save / Load project (JSON) — included in the sidebar

---

© FIN APPS. Built with Streamlit, Plotly and openpyxl.
