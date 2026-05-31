"""Core financial calculations: P&L, BS, CF, IRR, NPV, Payback, ROI."""
from __future__ import annotations
import numpy as np
import numpy_financial as npf
import pandas as pd


def _resolve(pct: float, val: float, sales: float) -> tuple[float, bool]:
    """Value overrides percentage. Returns (resolved_amount, value_overrode)."""
    if val and val > 0:
        return float(val), bool(pct and pct > 0)
    return float(sales) * float(pct or 0.0), False


def build_pnl(forecast_df: pd.DataFrame, setup: dict) -> pd.DataFrame:
    """Profit forecast. Index = Year."""
    if forecast_df.empty:
        return pd.DataFrame()

    capex = float(setup.get("initial_capex", 0) or 0)
    life = max(int(setup.get("useful_life", 1) or 1), 1)
    tax_rate = float(setup.get("tax_rate", 0) or 0)
    depreciable = float(setup.get("depreciable_capex", capex) or 0)

    rows = []
    for _, r in forecast_df.iterrows():
        year = int(r["Year"])
        sales = float(r["Sales"] or 0)

        material, _ = _resolve(r["Material %"], r["Material Value"], sales)
        labour, _   = _resolve(r["Direct Labour %"], r["Direct Labour Value"], sales)
        moh, _      = _resolve(r["MOH %"], r["MOH Value"], sales)
        sga, _      = _resolve(r["SG&A %"], r["SG&A Value"], sales)

        gross_profit = sales - material
        ebitda = gross_profit - labour - moh - sga
        # depreciation only during useful life from year 1
        idx_in_life = (year - int(forecast_df.iloc[0]["Year"])) < life
        depreciation = (depreciable / life) if idx_in_life and depreciable > 0 else 0.0
        ebit = ebitda - depreciation
        taxes = max(ebit, 0.0) * tax_rate
        net_income = ebit - taxes

        rows.append({
            "Year": year,
            "Sales": sales,
            "Material Cost": material,
            "Gross Profit": gross_profit,
            "Direct Labour": labour,
            "Manufacturing Overhead": moh,
            "SG&A": sga,
            "EBITDA": ebitda,
            "Depreciation": depreciation,
            "EBIT": ebit,
            "Taxes": taxes,
            "Net Income": net_income,
            "EBITDA Margin": (ebitda / sales) if sales else 0.0,
            "Net Margin": (net_income / sales) if sales else 0.0,
        })
    return pd.DataFrame(rows)


def build_balance_sheet(pnl: pd.DataFrame, setup: dict) -> pd.DataFrame:
    if pnl.empty:
        return pd.DataFrame()

    capex = float(setup.get("initial_capex", 0) or 0)
    rec_days = float(setup.get("receivable_days", 0) or 0)
    inv_days = float(setup.get("inventory_days", 0) or 0)
    pay_days = float(setup.get("payable_days", 0) or 0)

    rows = []
    accum = 0.0
    for _, r in pnl.iterrows():
        accum += float(r["Depreciation"])
        gross_fa = capex
        net_fa = max(capex - accum, 0.0)
        receivables = r["Sales"] / 365.0 * rec_days
        inventory   = r["Material Cost"] / 365.0 * inv_days
        payables    = r["Material Cost"] / 365.0 * pay_days
        nwc = receivables + inventory - payables
        rows.append({
            "Year": int(r["Year"]),
            "Gross Fixed Assets": gross_fa,
            "Accumulated Depreciation": accum,
            "Net Fixed Assets": net_fa,
            "Receivables": receivables,
            "Inventory": inventory,
            "Payables": payables,
            "Net Working Capital": nwc,
            "Net Investment": net_fa + nwc,
        })
    return pd.DataFrame(rows)


def build_cashflow(pnl: pd.DataFrame, bs: pd.DataFrame, setup: dict) -> pd.DataFrame:
    if pnl.empty:
        return pd.DataFrame()

    capex = float(setup.get("initial_capex", 0) or 0)
    residual = float(setup.get("residual_value", 0) or 0)
    recover_wc = bool(setup.get("recover_working_capital", True))

    first_year = int(pnl.iloc[0]["Year"])
    rows = [{
        "Year": first_year - 1,
        "Net Income": 0.0,
        "Depreciation": 0.0,
        "Change in WC": 0.0,
        "Capex": -capex,
        "Residual Value": 0.0,
        "Cash Flow": -capex,
    }]

    prev_nwc = 0.0
    last_idx = len(pnl) - 1
    for i, (_, r) in enumerate(pnl.iterrows()):
        nwc = float(bs.iloc[i]["Net Working Capital"])
        d_wc = nwc - prev_nwc
        prev_nwc = nwc
        residual_now = 0.0
        wc_recovery = 0.0
        if i == last_idx:
            residual_now = residual
            if recover_wc:
                wc_recovery = nwc  # release working capital
        cf = (float(r["Net Income"]) + float(r["Depreciation"]) - d_wc
              + residual_now + wc_recovery)
        rows.append({
            "Year": int(r["Year"]),
            "Net Income": float(r["Net Income"]),
            "Depreciation": float(r["Depreciation"]),
            "Change in WC": d_wc,
            "Capex": 0.0,
            "Residual Value": residual_now + wc_recovery,
            "Cash Flow": cf,
        })
    df = pd.DataFrame(rows)
    df["Cumulative Cash Flow"] = df["Cash Flow"].cumsum()
    return df


# ---------- Investment metrics ----------

def calc_irr(cashflows: list[float]) -> float | None:
    try:
        if not cashflows or all(c == 0 for c in cashflows):
            return None
        if not (any(c < 0 for c in cashflows) and any(c > 0 for c in cashflows)):
            return None
        irr = npf.irr(cashflows)
        if irr is None or np.isnan(irr) or np.isinf(irr):
            return None
        return float(irr)
    except Exception:
        return None


def calc_npv(rate: float, cashflows: list[float]) -> float:
    # cashflows[0] at t=0, cashflows[i] at t=i (end of year)
    return float(sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows)))


def discounted_cashflows(rate: float, cashflows: list[float]) -> list[float]:
    return [cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows)]


def _payback_from(series: list[float]) -> float | None:
    cum = 0.0
    for t, cf in enumerate(series):
        prev = cum
        cum += cf
        if prev < 0 <= cum:
            # interpolate within year
            frac = -prev / cf if cf != 0 else 0
            return (t - 1) + frac
    return None


def calc_payback(cashflows: list[float]) -> float | None:
    return _payback_from(cashflows)


def calc_discounted_payback(rate: float, cashflows: list[float]) -> float | None:
    return _payback_from(discounted_cashflows(rate, cashflows))


def calc_roi(pnl: pd.DataFrame, bs: pd.DataFrame) -> pd.DataFrame:
    if pnl.empty or bs.empty:
        return pd.DataFrame()
    rows = []
    prev_inv = bs.iloc[0]["Net Investment"]
    for i, (_, r) in enumerate(pnl.iterrows()):
        curr_inv = float(bs.iloc[i]["Net Investment"])
        avg_inv = (prev_inv + curr_inv) / 2 if i > 0 else curr_inv
        roi = (r["EBIT"] / avg_inv) if avg_inv else 0.0
        rows.append({"Year": int(r["Year"]), "EBIT": r["EBIT"],
                     "Average Investment": avg_inv, "ROI": roi})
        prev_inv = curr_inv
    return pd.DataFrame(rows)


def summarize(pnl: pd.DataFrame, bs: pd.DataFrame, cf: pd.DataFrame,
              roi_df: pd.DataFrame, setup: dict) -> dict:
    if pnl.empty:
        return {}
    cashflows = cf["Cash Flow"].tolist()
    rate = float(setup.get("discount_rate", 0) or 0)
    irr = calc_irr(cashflows)
    npv = calc_npv(rate, cashflows)
    payback = calc_payback(cashflows)
    dpayback = calc_discounted_payback(rate, cashflows)

    roi_vals = roi_df["ROI"].tolist() if not roi_df.empty else []
    avg_roi = float(np.mean(roi_vals)) if roi_vals else 0.0
    roi_3 = float(np.mean(roi_vals[:3])) if len(roi_vals) >= 1 else 0.0
    roi_5 = float(np.mean(roi_vals[:5])) if len(roi_vals) >= 1 else 0.0

    return {
        "total_investment": float(setup.get("initial_capex", 0) or 0),
        "irr": irr,
        "npv": npv,
        "payback": payback,
        "discounted_payback": dpayback,
        "ebitda_total": float(pnl["EBITDA"].sum()),
        "ebitda_avg": float(pnl["EBITDA"].mean()),
        "roi_avg": avg_roi,
        "roi_3y": roi_3,
        "roi_5y": roi_5,
        "peak_wc": float(bs["Net Working Capital"].max()),
        "cum_cashflow": float(cf["Cash Flow"].sum()),
        "hurdle": rate,
    }
