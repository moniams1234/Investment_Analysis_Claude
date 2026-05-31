"""Reusable UI components."""
from __future__ import annotations
import streamlit as st
from .helpers import fmt_money, fmt_pct, fmt_years
from .styling import PALETTE


def kpi_card(label: str, value: str, sub: str = "", accent: str = "blue") -> str:
    cls = "kpi-accent-blue" if accent == "blue" else "kpi-accent-red" if accent == "red" else ""
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value {cls}">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """


def traffic_light(level: str, text: str) -> str:
    cls = {"good": "tl-good", "warn": "tl-warn", "bad": "tl-bad"}.get(level, "tl-warn")
    return f'<span class="tl-dot {cls}"></span><span style="color:{PALETTE["text_mute"]}">{text}</span>'


def render_kpi_grid(summary: dict, currency: str) -> None:
    if not summary:
        st.info("Fill in Project Setup and Forecast Input to see KPIs.")
        return
    irr = summary.get("irr")
    hurdle = summary.get("hurdle", 0)
    npv = summary.get("npv", 0)
    payback = summary.get("payback")

    cards = [
        ("Total Investment", fmt_money(summary["total_investment"], currency), "Initial Capex", "red"),
        ("IRR", fmt_pct(irr) if irr is not None else "—",
         f"Hurdle {fmt_pct(hurdle)}", "blue"),
        ("NPV", fmt_money(npv, currency), f"@ {fmt_pct(hurdle)} discount", "blue" if npv >= 0 else "red"),
        ("Payback", fmt_years(payback), "Standard", "blue"),
        ("Discounted Payback", fmt_years(summary.get("discounted_payback")), "Time-adjusted", "blue"),
        ("Avg EBITDA", fmt_money(summary["ebitda_avg"], currency), "Per year", "blue"),
        ("Average ROI", fmt_pct(summary["roi_avg"]), "EBIT / Avg Investment", "blue"),
        ("Peak Working Capital", fmt_money(summary["peak_wc"], currency), "Maximum NWC", "red"),
    ]
    cols = st.columns(4)
    for i, (lbl, val, sub, acc) in enumerate(cards):
        with cols[i % 4]:
            st.markdown(kpi_card(lbl, val, sub, acc), unsafe_allow_html=True)


def render_recommendation(summary: dict) -> None:
    if not summary:
        return
    irr = summary.get("irr")
    npv = summary.get("npv", 0)
    hurdle = summary.get("hurdle", 0)
    payback = summary.get("payback")

    signals = []
    if irr is not None and irr >= hurdle and npv > 0:
        verdict = ("good", "INVEST — Project clears the hurdle and creates value.")
    elif npv > 0:
        verdict = ("warn", "REVIEW — Positive NPV but IRR borderline vs hurdle.")
    elif irr is None:
        verdict = ("warn", "INSUFFICIENT DATA — IRR cannot be computed from current cash flows.")
    else:
        verdict = ("bad", "REJECT — Project destroys value at the chosen discount rate.")

    signals.append(("good" if npv > 0 else "bad", f"NPV: {'positive' if npv > 0 else 'negative'}"))
    if irr is not None:
        signals.append(("good" if irr >= hurdle else "bad",
                        f"IRR {'≥' if irr >= hurdle else '<'} hurdle rate"))
    if payback is not None:
        signals.append(("good" if payback <= 5 else "warn",
                        f"Payback {'≤' if payback <= 5 else '>'} 5 years"))

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Investment Recommendation")
    st.markdown('<div class="brand-line"></div>', unsafe_allow_html=True)
    st.markdown(traffic_light(verdict[0], f"<b>{verdict[1]}</b>"), unsafe_allow_html=True)
    st.write("")
    for lvl, txt in signals:
        st.markdown(traffic_light(lvl, txt), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def issues_panel(issues: list[tuple[str, str]]) -> None:
    if not issues:
        return
    for lvl, msg in issues:
        if lvl == "error":
            st.error(msg)
        elif lvl == "warn":
            st.warning(msg)
        else:
            st.info(msg)
