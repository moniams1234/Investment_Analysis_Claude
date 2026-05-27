"""Brand palette and CSS injection for FIN APPS."""
import streamlit as st

PALETTE = {
    "bg_deep":    "#2B0000",
    "bg":         "#3B0000",
    "panel":      "#450909",
    "panel_2":    "#5A1010",
    "blue":       "#7ED6FF",
    "blue_soft":  "#8BCBFF",
    "red":        "#FF2B4D",
    "red_deep":   "#D91C3C",
    "text":       "#FFFFFF",
    "text_mute":  "#D9D9D9",
    "border":     "rgba(255,255,255,0.08)",
    "good":       "#22C55E",
    "warn":       "#F59E0B",
    "bad":        "#EF4444",
}

CHART_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=PALETTE["text"], family="Inter, Segoe UI, sans-serif"),
        colorway=[PALETTE["blue"], PALETTE["red"], PALETTE["blue_soft"],
                  PALETTE["red_deep"], "#C084FC", "#34D399"],
        xaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.15)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=20, t=50, b=40),
    )
)


def inject_css() -> None:
    css = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

      html, body, [class*="css"]  {{
        font-family: 'Inter', sans-serif;
        color: {PALETTE['text']};
      }}

      .stApp {{
        background:
          radial-gradient(1200px 800px at 10% -10%, #6a0e0e 0%, transparent 60%),
          radial-gradient(900px 700px at 100% 0%, #3a0202 0%, transparent 55%),
          linear-gradient(180deg, {PALETTE['bg_deep']} 0%, {PALETTE['bg']} 100%);
      }}

      /* Sidebar */
      section[data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg, #1f0000 0%, #320404 100%);
        border-right: 1px solid {PALETTE['border']};
      }}
      section[data-testid="stSidebar"] * {{ color: {PALETTE['text']}; }}

      /* Headings */
      h1, h2, h3, h4 {{ color: {PALETTE['text']}; letter-spacing: -.01em; }}
      h1 {{ font-weight: 800; }}
      h2 {{ font-weight: 700; }}

      /* Tabs */
      .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: rgba(0,0,0,0.25);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid {PALETTE['border']};
      }}
      .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: {PALETTE['text_mute']};
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 500;
      }}
      .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {PALETTE['blue']}22, {PALETTE['red']}22);
        color: {PALETTE['text']};
        box-shadow: inset 0 0 0 1px {PALETTE['border']};
      }}

      /* KPI cards */
      .kpi-card {{
        background: linear-gradient(160deg, {PALETTE['panel_2']} 0%, {PALETTE['panel']} 100%);
        border: 1px solid {PALETTE['border']};
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 18px 40px -24px rgba(0,0,0,0.7);
        transition: transform .15s ease, border-color .15s ease;
      }}
      .kpi-card:hover {{
        transform: translateY(-2px);
        border-color: rgba(126,214,255,0.35);
      }}
      .kpi-label {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: {PALETTE['text_mute']};
        margin-bottom: 6px;
      }}
      .kpi-value {{ font-size: 26px; font-weight: 700; color: {PALETTE['text']}; }}
      .kpi-sub {{ font-size: 12px; color: {PALETTE['text_mute']}; margin-top: 4px; }}
      .kpi-accent-blue {{ color: {PALETTE['blue']}; }}
      .kpi-accent-red  {{ color: {PALETTE['red']}; }}

      .tl-dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }}
      .tl-good {{ background:{PALETTE['good']}; box-shadow:0 0 12px {PALETTE['good']}; }}
      .tl-warn {{ background:{PALETTE['warn']}; box-shadow:0 0 12px {PALETTE['warn']}; }}
      .tl-bad  {{ background:{PALETTE['bad']};  box-shadow:0 0 12px {PALETTE['bad']}; }}

      /* Buttons */
      .stButton>button, .stDownloadButton>button {{
        background: linear-gradient(135deg, {PALETTE['blue']}, {PALETTE['blue_soft']});
        color: #0a1a24;
        border: 0;
        border-radius: 10px;
        padding: 8px 18px;
        font-weight: 600;
        transition: transform .1s ease, box-shadow .15s ease;
      }}
      .stButton>button:hover, .stDownloadButton>button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 10px 24px -10px {PALETTE['blue']};
      }}

      /* Inputs */
      .stNumberInput input, .stTextInput input, .stDateInput input {{
        background: rgba(0,0,0,0.35) !important;
        color: {PALETTE['text']} !important;
        border: 1px solid {PALETTE['border']} !important;
        border-radius: 8px !important;
      }}
      .stSelectbox div[data-baseweb="select"] > div {{
        background: rgba(0,0,0,0.35) !important;
        color: {PALETTE['text']} !important;
        border: 1px solid {PALETTE['border']} !important;
      }}

      /* DataFrame / Data editor */
      .stDataFrame, .stDataEditor {{
        border-radius: 14px; overflow: hidden;
        border: 1px solid {PALETTE['border']};
      }}

      /* Section card */
      .section-card {{
        background: linear-gradient(160deg, {PALETTE['panel']} 0%, #380505 100%);
        border: 1px solid {PALETTE['border']};
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 18px;
      }}

      .brand-line {{
        height: 2px;
        background: linear-gradient(90deg, {PALETTE['blue']}, {PALETTE['red']});
        border-radius: 2px;
        margin: 6px 0 14px 0;
      }}

      /* Hide Streamlit chrome */
      #MainMenu, footer {{ visibility: hidden; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
