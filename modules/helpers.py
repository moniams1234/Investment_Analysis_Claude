"""Shared helpers: formatting, JSON I/O, defaults."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import pandas as pd


def fmt_money(value: float | None, currency: str = "USD", decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "—"
    sign = "-" if value < 0 else ""
    v = abs(value)
    if v >= 1_000_000_000:
        s = f"{v/1_000_000_000:.2f}B"
    elif v >= 1_000_000:
        s = f"{v/1_000_000:.2f}M"
    elif v >= 1_000:
        s = f"{v/1_000:.1f}K"
    else:
        s = f"{v:,.{decimals}f}"
    return f"{sign}{currency} {s}"


def fmt_pct(value: float | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value*100:.{decimals}f}%"


def fmt_years(value: float | None) -> str:
    if value is None or pd.isna(value) or value < 0:
        return "—"
    return f"{value:.2f} yrs"


def empty_forecast_row(year: int) -> dict[str, Any]:
    """An empty (user-must-fill) yearly row. No financial defaults."""
    return {
        "Year": year,
        "Sales": 0.0,
        "Material %": 0.0,
        "Material Value": 0.0,
        "Direct Labour %": 0.0,
        "Direct Labour Value": 0.0,
        "MOH %": 0.0,
        "MOH Value": 0.0,
        "SG&A %": 0.0,
        "SG&A Value": 0.0,
    }


def empty_forecast_df(num_years: int, start_year: int = 2025) -> pd.DataFrame:
    return pd.DataFrame([empty_forecast_row(start_year + i) for i in range(num_years)])


def save_project_json(state: dict, path: Path) -> None:
    serializable = {k: v for k, v in state.items() if _is_jsonable(v)}
    if "forecast_df" in state and isinstance(state["forecast_df"], pd.DataFrame):
        serializable["forecast_df"] = state["forecast_df"].to_dict(orient="records")
    path.write_text(json.dumps(serializable, indent=2))


def load_project_json(path: Path) -> dict:
    data = json.loads(path.read_text())
    if "forecast_df" in data:
        data["forecast_df"] = pd.DataFrame(data["forecast_df"])
    return data


def _is_jsonable(v: Any) -> bool:
    try:
        json.dumps(v)
        return True
    except Exception:
        return isinstance(v, pd.DataFrame)
