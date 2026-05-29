"""
FIN APPS — Investment Analysis
Premium Streamlit application for investment / project analysis.
Run:  streamlit run app.py
"""
from __future__ import annotations
import base64
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.styling import inject_css, PALETTE
from modules.helpers import (
    empty_forecast_df, fmt_money, fmt_pct, fmt_years,
    save_project_json, load_project_json,
)
from modules.validation import validate_setup, validate_forecast
from modules.calculations import (
    build_pnl, build_balance_sheet, build_cashflow,
    calc_roi, summarize, calc_npv,
)
from modules.charts import (
    line_trend, cashflow_waterfall, cumulative_cashflow, roi_trend,
    working_capital_components, capex_vs_depreciation, irr_gauge,
    dashboard_overview, tornado_sensitivity,
)
from modules.ui_components import (
    render_kpi_grid, render_recommendation, issues_panel,
)
from modules.excel_export import build_workbook


# ─────────────────────────────────────────────────────────
# Page config + branding
# ─────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
LOGO_PATH = ROOT / "assets" / "fin_apps_logo.png"
SAMPLE_PATH = ROOT / "data" / "sample_project.json"

st.set_page_config(
    page_title="FIN APPS — Investment Analysis",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


# ─────────────────────────────────────────────────────────
# Session state — STRICTLY EMPTY DEFAULTS
# ─────────────────────────────────────────────────────────
def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("project_name", "")
    ss.setdefault("currency", "USD")
    ss.setdefault("start_year", 2025)
    ss.setdefault("num_years", 5)
    ss.setdefault("initial_capex", 0.0)
    ss.setdefault("depreciable_capex", 0.0)
    ss.setdefault("useful_life", 0)
    ss.setdefault("residual_value", 0.0)
    ss.setdefault("tax_rate", 0.0)
    ss.setdefault("discount_rate", 0.0)
    ss.setdefault("receivable_days", 0)
    ss.setdefault("inventory_days", 0)
    ss.setdefault("payable_days", 0)
    ss.setdefault("recover_working_capital", True)
    if "forecast_df" not in ss:
        ss.forecast_df = empty_forecast_df(ss.num_years, ss.start_year)


_init_state()


def _setup_dict() -> dict:
    keys = ["project_name", "currency", "start_year", "num_years",
            "initial_capex", "depreciable_capex", "useful_life", "residual_value",
            "tax_rate", "discount_rate", "receivable_days", "inventory_days",
            "payable_days", "recover_working_capital"]
    return {k: st.session_state[k] for k in keys}


def _sync_years() -> None:
    """Resize forecast_df to match num_years / start_year (preserving entered values)."""
    df = st.session_state.forecast_df.copy()
    target_years = [st.session_state.start_year + i for i in range(st.session_state.num_years)]
    df = df.set_index("Year") if "Year" in df.columns else df
    new = empty_forecast_df(st.session_state.num_years, st.session_state.start_year).set_index("Year")
    for y in target_years:
        if y in df.index:
            for col in new.columns:
                if col in df.columns:
                    new.loc[y, col] = df.loc[y, col]
    st.session_state.forecast_df = new.reset_index()


# ─────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────
def _logo_bytes() -> str | None:
    if LOGO_PATH.exists():
        return base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return None


with st.sidebar:
    b64 = _logo_bytes()
    if b64:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 8px 0 2px 0;">
              <img src="data:image/png;base64,{b64}" style="width:160px; border-radius:14px;
                box-shadow:0 12px 28px -16px rgba(0,0,0,0.8);" />
            </div>
            """, unsafe_allow_html=True,
        )
    st.markdown(
        f"""
        <div style="text-align:center; margin: 6px 0 18px 0;">
          <div style="font-weight:800; letter-spacing:.18em; color:{PALETTE['text']}; font-size:14px;">
            INVESTMENT ANALYSIS
          </div>
          <div style="color:{PALETTE['text_mute']}; font-size:11px; margin-top:2px;">
            Financial Insights. Better Decisions.
          </div>
          <div class="brand-line" style="margin: 10px auto 0; max-width: 80%;"></div>
        </div>
        """, unsafe_allow_html=True,
    )

    st.markdown("##### Project")
    st.text_input("Project name", key="project_name", placeholder="e.g. Plant Expansion Phase II")
    st.selectbox("Currency", ["USD", "EUR", "GBP", "PLN", "CHF", "JPY", "CNY"], key="currency")

    st.divider()
    st.markdown("##### Workspace")
    if st.button("🆕 Reset to empty project", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        _init_state()
        st.rerun()

    if st.button("📂 Load example/demo project", use_container_width=True):
        if SAMPLE_PATH.exists():
            data = load_project_json(SAMPLE_PATH)
            for k, v in data.items():
                st.session_state[k] = v
            st.rerun()

    uploaded = st.file_uploader("Load saved project (.json)", type=["json"])
    if uploaded is not None:
        try:
            data = json.loads(uploaded.read())
            if "forecast_df" in data:
                data["forecast_df"] = pd.DataFrame(data["forecast_df"])
            for k, v in data.items():
                st.session_state[k] = v
            st.success("Project loaded.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not load project: {e}")

    if st.button("💾 Download project (.json)", use_container_width=True):
        out = ROOT / "exports" / "project.json"
        out.parent.mkdir(exist_ok=True)
        save_project_json(_setup_dict() | {"forecast_df": st.session_state.forecast_df}, out)
        st.download_button("Download JSON", out.read_bytes(),
                           file_name=f"{st.session_state.project_name or 'project'}.json",
                           mime="application/json", use_container_width=True)


# ─────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 4px;">
      <div>
        <div style="font-size:12px; letter-spacing:.18em; color:{PALETTE['text_mute']};">FIN APPS</div>
        <div style="font-size:30px; font-weight:800;">
          <span style="color:{PALETTE['blue']};">Investment</span>
          <span style="color:{PALETTE['red']};">Analysis</span>
        </div>
      </div>
      <div style="text-align:right; color:{PALETTE['text_mute']}; font-size:12px;">
        <div>Project: <b style="color:{PALETTE['text']};">{st.session_state.project_name or '— untitled —'}</b></div>
        <div>Currency: <b style="color:{PALETTE['text']};">{st.session_state.currency}</b></div>
      </div>
    </div>
    <div class="brand-line"></div>
    """, unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────
# Compute everything once
# ─────────────────────────────────────────────────────────
setup = _setup_dict()
fc_df: pd.DataFrame = st.session_state.forecast_df
pnl = build_pnl(fc_df, setup)
bs = build_balance_sheet(pnl, setup)
cf = build_cashflow(pnl, bs, setup)
roi_df = calc_roi(pnl, bs)
summary = summarize(pnl, bs, cf, roi_df, setup)
currency = st.session_state.currency


# ─────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 Executive Summary", "⚙️ Project Setup", "📝 Forecast Input",
    "💰 Profit Forecast", "📒 Balance Sheet", "💵 Cash Flow",
    "📈 IRR / NPV / Payback", "📉 Charts & Dashboard", "📤 Excel Export",
])

# ── Executive Summary ──
with tabs[0]:
    issues_panel(validate_setup(setup) + validate_forecast(fc_df))
    render_kpi_grid(summary, currency)
    st.write("")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(dashboard_overview(pnl), use_container_width=True)
    with c2:
        st.plotly_chart(irr_gauge(summary.get("irr"), summary.get("hurdle", 0))
                        if summary else irr_gauge(None, 0),
                        use_container_width=True)
    render_recommendation(summary)

# ── Project Setup ──
with tabs[1]:
    st.markdown("### Project Setup")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    st.caption("All financial assumptions start empty. Enter values appropriate for your project.")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Start year", min_value=1990, max_value=2100,
                        step=1, key="start_year", on_change=_sync_years)
    with c2:
        st.number_input("Number of project years", min_value=1, max_value=30,
                        step=1, key="num_years", on_change=_sync_years)
    with c3:
        st.number_input("Initial Capex", min_value=0.0, step=1000.0, key="initial_capex")
    with c4:
        st.number_input("Depreciable Capex", min_value=0.0, step=1000.0, key="depreciable_capex")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Useful life (years)", min_value=0, max_value=50, step=1, key="useful_life")
    with c2:
        st.number_input("Residual value", min_value=0.0, step=1000.0, key="residual_value")
    with c3:
        st.number_input("Tax rate (decimal)", min_value=0.0, max_value=1.0,
                        step=0.01, format="%.4f", key="tax_rate",
                        help="e.g. 0.21 for 21%")
    with c4:
        st.number_input("Discount rate / WACC (decimal)", min_value=0.0, max_value=1.0,
                        step=0.01, format="%.4f", key="discount_rate")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Working Capital Days")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Receivable days", min_value=0, max_value=365, step=1, key="receivable_days")
    with c2:
        st.number_input("Inventory days", min_value=0, max_value=365, step=1, key="inventory_days")
    with c3:
        st.number_input("Payable days", min_value=0, max_value=365, step=1, key="payable_days")
    with c4:
        st.checkbox("Recover NWC in final year", key="recover_working_capital")
    st.markdown("</div>", unsafe_allow_html=True)

    issues_panel(validate_setup(setup))

# ── Forecast Input ──
with tabs[2]:
    st.markdown("### Forecast Input")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    st.caption("Enter yearly assumptions. For each cost line you may use **either** a % of sales **or** an absolute value. "
               "If both are entered, the Value overrides the %.")

    col_cfg = {
        "Year": st.column_config.NumberColumn("Year", disabled=True, format="%d"),
        "Sales": st.column_config.NumberColumn("Sales", format="%.0f", min_value=0.0),
        "Material %": st.column_config.NumberColumn("Material %", format="%.4f", min_value=0.0, max_value=1.5,
                                                    help="Decimal, e.g. 0.35 = 35%"),
        "Material Value": st.column_config.NumberColumn("Material Value", format="%.0f", min_value=0.0),
        "Direct Labour %": st.column_config.NumberColumn("Labour %", format="%.4f", min_value=0.0, max_value=1.5),
        "Direct Labour Value": st.column_config.NumberColumn("Labour Value", format="%.0f", min_value=0.0),
        "MOH %": st.column_config.NumberColumn("MOH %", format="%.4f", min_value=0.0, max_value=1.5),
        "MOH Value": st.column_config.NumberColumn("MOH Value", format="%.0f", min_value=0.0),
        "SG&A %": st.column_config.NumberColumn("SG&A %", format="%.4f", min_value=0.0, max_value=1.5),
        "SG&A Value": st.column_config.NumberColumn("SG&A Value", format="%.0f", min_value=0.0),
    }
    edited = st.data_editor(
        st.session_state.forecast_df,
        column_config=col_cfg,
        num_rows="fixed",
        use_container_width=True,
        key="forecast_editor",
        hide_index=True,
    )
    st.session_state.forecast_df = edited

    issues_panel(validate_forecast(edited))

# ── Profit Forecast ──
with tabs[3]:
    st.markdown("### Profit Forecast (P&L)")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    if pnl.empty:
        st.info("Enter sales and assumptions to see the P&L.")
    else:
        display = pnl.copy()
        for c in ["Sales","Material Cost","Gross Profit","Direct Labour","Manufacturing Overhead",
                  "SG&A","EBITDA","Depreciation","EBIT","Taxes","Net Income"]:
            display[c] = display[c].map(lambda v: fmt_money(v, currency))
        for c in ["EBITDA Margin", "Net Margin"]:
            display[c] = display[c].map(fmt_pct)
        st.dataframe(display, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(line_trend(pnl, "EBITDA", "EBITDA Trend"), use_container_width=True)
        with c2: st.plotly_chart(line_trend(pnl, "Net Income", "Net Income Trend",
                                            color=PALETTE["red"]), use_container_width=True)

# ── Balance Sheet ──
with tabs[4]:
    st.markdown("### Balance Sheet & Working Capital")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    if bs.empty:
        st.info("Fill the inputs to compute the balance sheet.")
    else:
        display = bs.copy()
        for c in display.columns:
            if c == "Year": continue
            display[c] = display[c].map(lambda v: fmt_money(v, currency))
        st.dataframe(display, use_container_width=True, hide_index=True)
        st.plotly_chart(working_capital_components(bs), use_container_width=True)

# ── Cash Flow ──
with tabs[5]:
    st.markdown("### Cash Flow")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    if cf.empty:
        st.info("Cash flow appears once setup and forecast are populated.")
    else:
        display = cf.copy()
        for c in display.columns:
            if c == "Year": continue
            display[c] = display[c].map(lambda v: fmt_money(v, currency))
        st.dataframe(display, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(cashflow_waterfall(cf), use_container_width=True)
        with c2: st.plotly_chart(cumulative_cashflow(cf), use_container_width=True)

# ── IRR / NPV / Payback ──
with tabs[6]:
    st.markdown("### Investment Metrics")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    if not summary:
        st.info("Investment metrics will appear once cash flows are computed.")
    else:
        c = st.columns(4)
        c[0].markdown(f"**IRR**<br><span style='color:{PALETTE['blue']}; font-size:28px;'>{fmt_pct(summary['irr'])}</span>", unsafe_allow_html=True)
        c[1].markdown(f"**NPV**<br><span style='color:{PALETTE['blue']}; font-size:28px;'>{fmt_money(summary['npv'], currency)}</span>", unsafe_allow_html=True)
        c[2].markdown(f"**Payback**<br><span style='color:{PALETTE['blue']}; font-size:28px;'>{fmt_years(summary['payback'])}</span>", unsafe_allow_html=True)
        c[3].markdown(f"**Discounted Payback**<br><span style='color:{PALETTE['blue']}; font-size:28px;'>{fmt_years(summary['discounted_payback'])}</span>", unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns([1, 2])
        with c1: st.plotly_chart(irr_gauge(summary["irr"], summary["hurdle"]), use_container_width=True)
        with c2: st.plotly_chart(cumulative_cashflow(cf), use_container_width=True)

        st.markdown("#### ROI")
        if not roi_df.empty:
            disp = roi_df.copy()
            disp["EBIT"] = disp["EBIT"].map(lambda v: fmt_money(v, currency))
            disp["Average Investment"] = disp["Average Investment"].map(lambda v: fmt_money(v, currency))
            disp["ROI"] = disp["ROI"].map(fmt_pct)
            st.dataframe(disp, use_container_width=True, hide_index=True)
            c = st.columns(3)
            c[0].metric("Average ROI", fmt_pct(summary["roi_avg"]))
            c[1].metric("3-Year ROI", fmt_pct(summary["roi_3y"]))
            c[2].metric("5-Year ROI", fmt_pct(summary["roi_5y"]))
            st.plotly_chart(roi_trend(roi_df), use_container_width=True)

# ── Charts & Dashboard ──
with tabs[7]:
    st.markdown("### Charts & Dashboard")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    if pnl.empty:
        st.info("Charts appear once data is entered.")
    else:
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(line_trend(pnl, "Sales", "Sales Trend"), use_container_width=True)
        with c2: st.plotly_chart(line_trend(pnl, "EBITDA", "EBITDA Trend",
                                            color=PALETTE["red"]), use_container_width=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(cashflow_waterfall(cf), use_container_width=True)
        with c2: st.plotly_chart(cumulative_cashflow(cf), use_container_width=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(working_capital_components(bs), use_container_width=True)
        with c2: st.plotly_chart(capex_vs_depreciation(pnl, setup), use_container_width=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(roi_trend(roi_df), use_container_width=True)
        with c2: st.plotly_chart(dashboard_overview(pnl), use_container_width=True)

        with st.expander("🔬 Sensitivity Analysis (NPV tornado, ±10%)"):
            base_cf = cf["Cash Flow"].tolist()
            base_npv = calc_npv(setup["discount_rate"], base_cf)
            scenarios = {}
            # Sales ±10%
            for label, mult in [("Sales ±10%", "sales"), ("Material Cost ±10%", "mat"),
                                 ("Discount Rate ±10%", "dr"), ("Capex ±10%", "capex")]:
                lo_cf, hi_cf = base_cf.copy(), base_cf.copy()
                if mult == "sales":
                    lo_pnl = build_pnl(fc_df.assign(Sales=fc_df["Sales"]*0.9), setup)
                    hi_pnl = build_pnl(fc_df.assign(Sales=fc_df["Sales"]*1.1), setup)
                    lo_bs = build_balance_sheet(lo_pnl, setup); hi_bs = build_balance_sheet(hi_pnl, setup)
                    lo_cf = build_cashflow(lo_pnl, lo_bs, setup)["Cash Flow"].tolist()
                    hi_cf = build_cashflow(hi_pnl, hi_bs, setup)["Cash Flow"].tolist()
                elif mult == "mat":
                    lo = fc_df.assign(**{"Material %": fc_df["Material %"]*0.9, "Material Value": fc_df["Material Value"]*0.9})
                    hi = fc_df.assign(**{"Material %": fc_df["Material %"]*1.1, "Material Value": fc_df["Material Value"]*1.1})
                    lo_pnl = build_pnl(lo, setup); hi_pnl = build_pnl(hi, setup)
                    lo_bs = build_balance_sheet(lo_pnl, setup); hi_bs = build_balance_sheet(hi_pnl, setup)
                    lo_cf = build_cashflow(lo_pnl, lo_bs, setup)["Cash Flow"].tolist()
                    hi_cf = build_cashflow(hi_pnl, hi_bs, setup)["Cash Flow"].tolist()
                elif mult == "dr":
                    scenarios[label] = (calc_npv(setup["discount_rate"]*1.1, base_cf),
                                        calc_npv(setup["discount_rate"]*0.9, base_cf))
                    continue
                elif mult == "capex":
                    s_lo = setup | {"initial_capex": setup["initial_capex"]*1.1, "depreciable_capex": setup["depreciable_capex"]*1.1}
                    s_hi = setup | {"initial_capex": setup["initial_capex"]*0.9, "depreciable_capex": setup["depreciable_capex"]*0.9}
                    lo_pnl = build_pnl(fc_df, s_lo); hi_pnl = build_pnl(fc_df, s_hi)
                    lo_bs = build_balance_sheet(lo_pnl, s_lo); hi_bs = build_balance_sheet(hi_pnl, s_hi)
                    lo_cf = build_cashflow(lo_pnl, lo_bs, s_lo)["Cash Flow"].tolist()
                    hi_cf = build_cashflow(hi_pnl, hi_bs, s_hi)["Cash Flow"].tolist()
                scenarios[label] = (calc_npv(setup["discount_rate"], lo_cf),
                                    calc_npv(setup["discount_rate"], hi_cf))
            st.plotly_chart(tornado_sensitivity(base_npv, scenarios), use_container_width=True)

# ── Excel Export ──
with tabs[8]:
    st.markdown("### Excel Export")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    st.write("Generate a fully formatted Excel workbook including assumptions, P&L, balance sheet, "
             "cash flow, IRR/ROI and the executive summary.")
    if st.button("📤 Generate Excel workbook", type="primary"):
        try:
            data = build_workbook(setup, fc_df, pnl, bs, cf, roi_df, summary, logo_path=LOGO_PATH)
            st.download_button(
                "⬇️ Download FIN_APPS_Investment_Analysis.xlsx",
                data=data,
                file_name=f"FIN_APPS_{(st.session_state.project_name or 'project').replace(' ','_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.success("Workbook ready.")
        except Exception as e:
            st.error(f"Export failed: {e}")
