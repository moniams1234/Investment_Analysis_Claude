"""Input validation."""
from __future__ import annotations
import pandas as pd


def validate_setup(setup: dict) -> list[tuple[str, str]]:
    """Return list of (level, message). level in {'error','warn','info'}."""
    issues: list[tuple[str, str]] = []
    if setup.get("num_years", 0) <= 0:
        issues.append(("error", "Number of project years must be greater than zero."))
    if setup.get("initial_capex", 0) <= 0:
        issues.append(("warn", "Initial capex is zero. IRR / payback will not be meaningful."))
    if setup.get("useful_life", 0) <= 0:
        issues.append(("error", "Useful life (book depreciation period) must be greater than zero."))
    tax = setup.get("tax_rate", 0)
    if tax < 0 or tax > 1:
        issues.append(("error", "Tax rate must be between 0% and 100%."))
    dr = setup.get("discount_rate", 0)
    if dr < 0:
        issues.append(("error", "Discount rate / WACC cannot be negative."))
    for k in ("receivable_days", "inventory_days", "payable_days"):
        if setup.get(k, 0) < 0:
            issues.append(("error", f"{k.replace('_', ' ').title()} cannot be negative."))
    return issues


def validate_forecast(df: pd.DataFrame) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    if df.empty:
        issues.append(("error", "Forecast table is empty."))
        return issues
    if (df["Sales"] < 0).any():
        issues.append(("warn", "One or more years have negative sales."))
    if df["Sales"].sum() == 0:
        issues.append(("info", "No sales entered yet — fill in the Forecast Input tab."))
    for col in ["Material %", "Direct Labour %", "MOH %", "SG&A %"]:
        if (df[col] > 1.5).any():
            issues.append(("warn", f"'{col}' contains values > 150%. Enter percentages as decimals (e.g. 0.35 = 35%)."))
    for label, pct, val in [
        ("Material", "Material %", "Material Value"),
        ("Direct Labour", "Direct Labour %", "Direct Labour Value"),
        ("MOH", "MOH %", "MOH Value"),
        ("SG&A", "SG&A %", "SG&A Value"),
    ]:
        both = ((df[pct] > 0) & (df[val] > 0)).any()
        if both:
            issues.append(("info", f"{label}: both % and Value entered for some years — Value will override %."))
    return issues
