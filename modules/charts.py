"""Plotly charts using brand palette."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from .styling import PALETTE, CHART_TEMPLATE


def _apply(fig: go.Figure, title: str | None = None, height: int = 360) -> go.Figure:
    fig.update_layout(**CHART_TEMPLATE["layout"], height=height,
                      title=dict(text=title or "", x=0.01, xanchor="left",
                                 font=dict(size=16, color=PALETTE["text"])))
    return fig


def line_trend(df: pd.DataFrame, y: str, title: str, color: str | None = None) -> go.Figure:
    if df.empty:
        return _apply(go.Figure(), title)
    color = color or PALETTE["blue"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Year"], y=df[y], mode="lines+markers",
        line=dict(color=color, width=3),
        marker=dict(size=8, color=color, line=dict(color="white", width=1)),
        fill="tozeroy",
        fillcolor=f"rgba(126,214,255,0.10)" if color == PALETTE["blue"] else "rgba(255,43,77,0.10)",
        name=y,
    ))
    return _apply(fig, title)


def cashflow_waterfall(cf: pd.DataFrame) -> go.Figure:
    if cf.empty:
        return _apply(go.Figure(), "Cash Flow Waterfall")
    fig = go.Figure(go.Waterfall(
        x=[str(y) for y in cf["Year"]],
        y=cf["Cash Flow"],
        measure=["relative"] * len(cf),
        increasing=dict(marker=dict(color=PALETTE["blue"])),
        decreasing=dict(marker=dict(color=PALETTE["red"])),
        totals=dict(marker=dict(color=PALETTE["blue_soft"])),
        connector=dict(line=dict(color="rgba(255,255,255,0.2)")),
    ))
    return _apply(fig, "Cash Flow Waterfall", height=400)


def cumulative_cashflow(cf: pd.DataFrame) -> go.Figure:
    if cf.empty:
        return _apply(go.Figure(), "Cumulative Cash Flow")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cf["Year"], y=cf["Cash Flow"], name="Annual",
                         marker_color=PALETTE["red"]))
    fig.add_trace(go.Scatter(x=cf["Year"], y=cf["Cumulative Cash Flow"],
                             name="Cumulative", mode="lines+markers",
                             line=dict(color=PALETTE["blue"], width=3)))
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.3)", dash="dash"))
    return _apply(fig, "Cumulative Cash Flow", height=400)


def roi_trend(roi_df: pd.DataFrame) -> go.Figure:
    if roi_df.empty:
        return _apply(go.Figure(), "ROI Trend")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=roi_df["Year"], y=roi_df["ROI"] * 100,
                         marker_color=PALETTE["blue_soft"], name="ROI %"))
    return _apply(fig, "ROI by Year (%)")


def working_capital_components(bs: pd.DataFrame) -> go.Figure:
    if bs.empty:
        return _apply(go.Figure(), "Working Capital Components")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=bs["Year"], y=bs["Receivables"], name="Receivables",
                         marker_color=PALETTE["blue"]))
    fig.add_trace(go.Bar(x=bs["Year"], y=bs["Inventory"], name="Inventory",
                         marker_color=PALETTE["blue_soft"]))
    fig.add_trace(go.Bar(x=bs["Year"], y=-bs["Payables"], name="Payables",
                         marker_color=PALETTE["red"]))
    fig.add_trace(go.Scatter(x=bs["Year"], y=bs["Net Working Capital"],
                             name="Net WC", mode="lines+markers",
                             line=dict(color="white", width=2)))
    fig.update_layout(barmode="relative")
    return _apply(fig, "Working Capital Components", height=400)


def capex_vs_depreciation(pnl: pd.DataFrame, setup: dict) -> go.Figure:
    if pnl.empty:
        return _apply(go.Figure(), "Capex vs Depreciation")
    years = [int(pnl.iloc[0]["Year"]) - 1] + pnl["Year"].astype(int).tolist()
    capex = [float(setup.get("initial_capex", 0) or 0)] + [0.0] * len(pnl)
    dep = [0.0] + pnl["Depreciation"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=capex, name="Capex", marker_color=PALETTE["red"]))
    fig.add_trace(go.Bar(x=years, y=dep, name="Depreciation", marker_color=PALETTE["blue"]))
    fig.update_layout(barmode="group")
    return _apply(fig, "Capex vs Depreciation")


def irr_gauge(irr: float | None, hurdle: float) -> go.Figure:
    val = (irr or 0) * 100
    max_v = max(40, val * 1.4, hurdle * 100 * 2)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=val,
        number={"suffix": "%", "font": {"color": PALETTE["text"], "size": 38}},
        delta={"reference": hurdle * 100, "increasing": {"color": PALETTE["good"]},
               "decreasing": {"color": PALETTE["bad"]}},
        title={"text": "IRR vs Hurdle", "font": {"color": PALETTE["text_mute"]}},
        gauge={
            "axis": {"range": [0, max_v], "tickcolor": PALETTE["text_mute"]},
            "bar": {"color": PALETTE["blue"]},
            "bgcolor": "rgba(0,0,0,0.3)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, hurdle * 100], "color": "rgba(255,43,77,0.25)"},
                {"range": [hurdle * 100, max_v], "color": "rgba(126,214,255,0.15)"},
            ],
            "threshold": {"line": {"color": "white", "width": 3},
                          "thickness": 0.8, "value": hurdle * 100},
        }
    ))
    return _apply(fig, "Internal Rate of Return", height=340)


def dashboard_overview(pnl: pd.DataFrame) -> go.Figure:
    if pnl.empty:
        return _apply(go.Figure(), "Investment Dashboard")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=pnl["Year"], y=pnl["Sales"], name="Sales",
                         marker_color="rgba(126,214,255,0.55)"))
    fig.add_trace(go.Scatter(x=pnl["Year"], y=pnl["EBITDA"], name="EBITDA",
                             mode="lines+markers", line=dict(color=PALETTE["red"], width=3)))
    fig.add_trace(go.Scatter(x=pnl["Year"], y=pnl["Net Income"], name="Net Income",
                             mode="lines+markers", line=dict(color="white", width=2, dash="dot")))
    return _apply(fig, "Sales / EBITDA / Net Income", height=380)


def tornado_sensitivity(base_npv: float, sensitivities: dict[str, tuple[float, float]]) -> go.Figure:
    """sensitivities: {label: (npv_low, npv_high)}"""
    labels, lows, highs = [], [], []
    for k, (lo, hi) in sensitivities.items():
        labels.append(k)
        lows.append(lo - base_npv)
        highs.append(hi - base_npv)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=lows, orientation="h", name="−10%",
                         marker_color=PALETTE["red"]))
    fig.add_trace(go.Bar(y=labels, x=highs, orientation="h", name="+10%",
                         marker_color=PALETTE["blue"]))
    fig.update_layout(barmode="overlay")
    return _apply(fig, "NPV Sensitivity (Tornado)", height=380)
