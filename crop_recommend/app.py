import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import time
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# Page config + asset loading
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Next Crop — Soil-Based Planting Guide",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

@st.cache_resource
def load_assets():
    yield_model = joblib.load("app_assets/yield_model.pkl")
    soil_score_model = joblib.load("app_assets/soil_score_model.pkl")
    crop_requirements = pd.read_csv("app_assets/crop_requirements.csv", index_col=0)
    prev_crop_lookup = pd.read_csv("app_assets/previous_crop_soil_lookup.csv", index_col=0)
    region_climate = pd.read_csv("app_assets/region_climate_defaults.csv", index_col=0)
    region_soil_type = pd.read_csv("app_assets/region_soil_type_defaults.csv", index_col=0)
    with open("app_assets/reference.json") as f:
        reference = json.load(f)
    return yield_model, soil_score_model, crop_requirements, prev_crop_lookup, region_climate, region_soil_type, reference

yield_model, soil_score_model, crop_requirements, prev_crop_lookup, region_climate, region_soil_type, reference = load_assets()

SOIL_FEATURES = ["Soil pH", "Soil Nitrogen", "Soil Phosphorus", "Soil Potassium",
                  "Soil Organic Matter (%)", "Soil Moisture (%)"]
FEATURE_COLS = ["Region", "Season", "Soil Type", "Soil pH", "Soil Nitrogen", "Soil Phosphorus",
                 "Soil Potassium", "Soil Organic Matter (%)", "Soil Moisture (%)", "Avg Rainfall (mm)",
                 "Solar Radiation Impact (BTU/sqft)", "Crop_Planted (Action)"]

# Plain-language nutrient roles -- established agronomy facts, not model output
NUTRIENT_INFO = {
    "Soil Nitrogen": {"label": "Nitrogen (N)", "role": "Fuels leafy, green growth", "color": "#3B6FA0", "unit": ""},
    "Soil Phosphorus": {"label": "Phosphorus (P)", "role": "Builds strong roots and flowers", "color": "#C97A2B", "unit": ""},
    "Soil Potassium": {"label": "Potassium (K)", "role": "Strengthens plants and improves fruit quality", "color": "#7A5C9E", "unit": ""},
}

# ----------------------------------------------------------------------------
# Styling — soil-horizon inspired token system
# ----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --paper: #FAF7F0;
    --ink: #2B2117;
    --ink-soft: #5C5042;
    --growth: #3F7D53;
    --growth-soft: #E8F1EA;
    --nitrogen: #3B6FA0;
    --phosphorus: #C97A2B;
    --potassium: #7A5C9E;
    --clay: #B0492F;
    --line: #E4DDCE;
}

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: var(--paper) !important;
    color: var(--ink) !important;
    color-scheme: light !important;
}
* { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Fraunces', serif !important; color: var(--ink) !important; font-weight: 600; }
p, span, label, .stMarkdown, [data-testid="stMarkdownContainer"] { color: var(--ink) !important; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--ink-soft) !important; }

/* Native widgets: force light, on-brand styling regardless of browser/system dark mode */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important; color: var(--ink) !important; border: 1px solid var(--line) !important;
}
[data-testid="stSelectbox"] svg { fill: var(--ink) !important; }
[data-baseweb="popover"] { background-color: #FFFFFF !important; }
[data-baseweb="menu"] li { color: var(--ink) !important; background-color: #FFFFFF !important; }
[data-baseweb="menu"] li:hover { background-color: var(--growth-soft) !important; }

[data-testid="stWidgetLabel"] p { color: var(--ink) !important; font-weight: 500 !important; }

.stSlider [data-baseweb="slider"] div[role="slider"] { background-color: var(--growth) !important; border-color: var(--growth) !important; }
.stSlider [data-baseweb="slider"] > div > div { background-color: var(--growth) !important; }
[data-testid="stSliderTickBar"] { display: none !important; }

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stVerticalBlockBorderWrapper"] { animation: fadeInUp 0.55s ease both; }

[data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid var(--line) !important; border-radius: 10px; }
[data-testid="stExpander"] summary { color: var(--ink) !important; }

.hero-banner {
    border-radius: 18px; overflow: hidden; margin-bottom: 1.6rem; box-shadow: 0 8px 24px rgba(43,33,23,0.12);
    line-height: 0; background: #E3A75E;
}
.hero-banner svg { display: block; width: 100%; }
.hero-title-wrap { text-align: center; margin-bottom: 1.8rem; }
.hero-title { font-family: 'Fraunces', serif !important; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.3rem; color: var(--ink) !important; }
.hero-subtitle { font-family: 'Inter', sans-serif; font-size: 1.05rem; color: var(--ink) !important; opacity: 0.85; margin-bottom: 0.2rem; max-width: 640px; margin-left: auto; margin-right: auto; }

.horizon-strip { display: flex; height: 14px; border-radius: 7px; overflow: hidden; margin: 0.4rem 0 1.2rem 0; border: 1px solid var(--line); }
.horizon-segment { height: 100%; }

.crop-card {
    background: #FFFFFF; border: 1px solid var(--line); border-radius: 14px;
    padding: 1.3rem 1.4rem; margin-bottom: 1rem;
}
.crop-card.top-pick { border: 2px solid var(--growth); background: var(--growth-soft); }
.crop-rank { font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; color: var(--ink-soft) !important; letter-spacing: 0.04em; }
.crop-name { font-family: 'Fraunces', serif !important; font-size: 1.5rem; font-weight: 700; margin: 0.1rem 0 0.3rem 0; color: var(--ink) !important; }
.crop-yield { font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; color: var(--growth) !important; font-weight: 600; }

.section-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--ink-soft) !important; margin-bottom: 0.3rem; font-weight: 600;
}

.stButton > button {
    background-color: var(--growth) !important; color: white !important; border: none; border-radius: 8px;
    padding: 0.6rem 1.6rem; font-weight: 600; font-family: 'Inter', sans-serif;
}
.stButton > button:hover { background-color: #336847 !important; color: white !important; }
.stButton > button p { color: white !important; }

.disclaimer-box {
    background: #FFFFFF; border: 1px solid var(--line); border-left: 4px solid var(--clay);
    border-radius: 8px; padding: 0.9rem 1.1rem; font-size: 0.88rem; color: var(--ink-soft) !important; margin-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Header — farmland banner + title card
# ----------------------------------------------------------------------------
FARMLAND_SVG = """
<div class="hero-banner">
<svg viewBox="0 0 1200 260" width="100%" height="220" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#F7E7B8"/>
      <stop offset="55%" stop-color="#EFCB86"/>
      <stop offset="100%" stop-color="#E3A75E"/>
    </linearGradient>
    <linearGradient id="hillBack" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7FA35C"/>
      <stop offset="100%" stop-color="#5C8B48"/>
    </linearGradient>
    <linearGradient id="hillFront" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4C7A3E"/>
      <stop offset="100%" stop-color="#345C2C"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="260" fill="url(#sky)"/>
  <circle cx="1030" cy="70" r="58" fill="#F6B23E" opacity="0.9"/>
  <circle cx="1030" cy="70" r="90" fill="#F6B23E" opacity="0.18"/>
  <path d="M0,190 C200,150 380,215 620,180 C860,145 1020,190 1200,160 L1200,260 L0,260 Z" fill="url(#hillBack)"/>
  <path d="M0,230 C220,195 420,250 650,220 C900,187 1040,235 1200,210 L1200,260 L0,260 Z" fill="url(#hillFront)"/>
  <g stroke="#2C4A24" stroke-width="2" opacity="0.55">
    <path d="M60,250 Q400,232 760,252 Q980,262 1150,246" fill="none"/>
  </g>
  <g fill="#F4E7C7" opacity="0.8">
    <circle cx="120" cy="247" r="3"/><circle cx="160" cy="244" r="3"/><circle cx="200" cy="248" r="3"/>
    <circle cx="240" cy="243" r="3"/><circle cx="280" cy="249" r="3"/><circle cx="320" cy="245" r="3"/>
  </g>
  <text x="46" y="140" font-family="Fraunces, serif" font-size="44" font-weight="700" fill="#3A2A16" opacity="0.92">CropCycle</text>
  <text x="48" y="172" font-family="Inter, sans-serif" font-size="17" letter-spacing="0.04em" fill="#4A3722" opacity="0.85">SOIL-AWARE ROTATION PLANNING</text>
</svg>
</div>
"""
st.markdown(FARMLAND_SVG, unsafe_allow_html=True)

st.markdown(f"""
<div class="hero-title-wrap">
    <div class="hero-title">🌾 What should you plant next?</div>
    <div class="hero-subtitle">Tell us what's in your soil — either by naming your last crop,
    or entering test numbers directly — and we'll recommend the next crop for the strongest yield.</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------
def nutrient_level_label(value, low, high):
    if value < low:
        return "Low", "#B0492F"
    elif value > high:
        return "High", "#3F7D53"
    else:
        return "Moderate", "#C97A2B"

def render_horizon_strip(n, p, k):
    """A soil-horizon-style strip showing relative N/P/K levels."""
    total = max(n + p + k, 1)
    n_pct, p_pct, k_pct = (n / total * 100, p / total * 100, k / total * 100)
    st.markdown(f"""
    <div class="horizon-strip">
        <div class="horizon-segment" style="width:{n_pct}%; background:{NUTRIENT_INFO['Soil Nitrogen']['color']};"></div>
        <div class="horizon-segment" style="width:{p_pct}%; background:{NUTRIENT_INFO['Soil Phosphorus']['color']};"></div>
        <div class="horizon-segment" style="width:{k_pct}%; background:{NUTRIENT_INFO['Soil Potassium']['color']};"></div>
    </div>
    """, unsafe_allow_html=True)

def soil_score_gauge(score_0_100):
    if score_0_100 >= 70:
        band, color = "Good condition", "#3F7D53"
    elif score_0_100 >= 45:
        band, color = "Fair condition", "#C97A2B"
    else:
        band, color = "Needs attention", "#B0492F"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score_0_100,
        number={"suffix": "/100", "font": {"family": "IBM Plex Mono", "size": 36, "color": "#332A22"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#6B5F52"},
            "bar": {"color": color},
            "bgcolor": "#FAF7F0",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 45], "color": "#F3E3DD"},
                {"range": [45, 70], "color": "#F3E9D8"},
                {"range": [70, 100], "color": "#E8F1EA"},
            ],
        },
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig, band

def show_growing_animation(duration=1.8):
    """A small sprouting-plant animation shown while recommendations are computed."""
    placeholder = st.empty()
    placeholder.markdown(f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:2.2rem 0;">
      <svg width="120" height="140" viewBox="0 0 120 140">
        <ellipse cx="60" cy="128" rx="44" ry="9" fill="#6B4A2E" opacity="0.3"/>
        <rect x="57" y="128" width="6" height="0" rx="3" fill="#3F7D53">
          <animate attributeName="height" from="0" to="55" dur="0.9s" begin="0s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.2 1"/>
          <animate attributeName="y" from="128" to="73" dur="0.9s" begin="0s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.2 1"/>
        </rect>
        <path d="M60,95 C40,88 30,72 34,58 C50,62 60,78 60,95 Z" fill="#4C7A51" opacity="0">
          <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.75s" fill="freeze"/>
        </path>
        <path d="M60,88 C80,80 90,64 86,50 C70,55 60,72 60,88 Z" fill="#6B9E56" opacity="0">
          <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.95s" fill="freeze"/>
        </path>
        <circle cx="60" cy="70" r="0" fill="#F6B23E">
          <animate attributeName="r" from="0" to="7" dur="0.4s" begin="1.3s" fill="freeze"/>
        </circle>
      </svg>
      <div style="font-family:'IBM Plex Mono',monospace; color:#5C5042; margin-top:0.5rem; font-size:0.92rem; animation: cropcyclePulse 1.2s ease-in-out infinite;">
        Growing your recommendations...
      </div>
    </div>
    <style>
      @keyframes cropcyclePulse {{ 0%,100% {{ opacity: 0.55; }} 50% {{ opacity: 1; }} }}
    </style>
    """, unsafe_allow_html=True)
    time.sleep(duration)
    placeholder.empty()


def recommend_crops(field_state, top_n=3):
    rows = []
    for crop in reference["crops"]:
        row = field_state.copy()
        row["Crop_Planted (Action)"] = crop
        rows.append(row)
    candidates = pd.DataFrame(rows)[FEATURE_COLS]
    ratio_pred = yield_model.predict(candidates)
    base_yield = crop_requirements.loc[candidates["Crop_Planted (Action)"], "Base Yield (kg/ha)"].values
    candidates["suitability_ratio"] = ratio_pred
    candidates["predicted_yield"] = ratio_pred * base_yield
    # Rank by suitability ratio (how well THIS soil suits each crop relative to its own norm),
    # not raw yield -- crops have wildly different natural yield scales (Tomato ~10,000 kg/ha vs
    # Chickpea ~1,000 kg/ha), so ranking by raw yield just returns whichever crop has the highest
    # baseline every time, regardless of soil fit.
    return candidates[["Crop_Planted (Action)", "suitability_ratio", "predicted_yield"]] \
        .sort_values("suitability_ratio", ascending=False).head(top_n).reset_index(drop=True)

def render_results(field_state, previous_crop_label):
    n, p, k = field_state["Soil Nitrogen"], field_state["Soil Phosphorus"], field_state["Soil Potassium"]

    st.markdown("---")
    st.markdown('<div class="section-label">Current soil snapshot</div>', unsafe_allow_html=True)
    render_horizon_strip(n, p, k)

    col_nutrients, col_score = st.columns([1.4, 1])

    with col_nutrients:
        for key in ["Soil Nitrogen", "Soil Phosphorus", "Soil Potassium"]:
            info = NUTRIENT_INFO[key]
            value = field_state[key]
            level, color = nutrient_level_label(value, 40, 90)
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.35rem 0; border-bottom:1px solid var(--line);">
                <div>
                    <span style="font-weight:600;">{info['label']}</span>
                    <span style="color:var(--ink-soft); font-size:0.85rem;"> — {info['role']}</span>
                </div>
                <div style="font-family:'IBM Plex Mono',monospace;">
                    {value:.0f} <span style="color:{color}; font-weight:600;">({level})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_score:
        soil_score_input = pd.DataFrame([{f: field_state[f] for f in SOIL_FEATURES}])
        raw_score = soil_score_model.predict(soil_score_input)[0]
        score_100 = float(np.clip(raw_score * 100, 0, 100))
        fig, band = soil_score_gauge(score_100)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<div style='text-align:center; font-weight:600;'>{band}</div>", unsafe_allow_html=True)

    st.caption(
        "Soil score is a model-based estimate summarizing pH, nutrients, organic matter, and moisture into "
        "a single 0–100 reading. Treat it as a directional guide, not a lab-certified measurement."
    )

    st.markdown('<div class="section-label" style="margin-top:1.8rem;">Recommended next crops</div>', unsafe_allow_html=True)
    if previous_crop_label:
        st.caption(f"Recommendations account for soil conditions after growing {previous_crop_label.lower()}.")
    st.caption("Ranked by how well-suited each crop is to this soil, relative to that crop's own typical yield — not by raw kg/ha, since crops naturally yield at very different scales.")

    top3 = recommend_crops(field_state, top_n=3)

    for i, row in top3.iterrows():
        crop = row["Crop_Planted (Action)"]
        pred_yield = row["predicted_yield"]
        suitability_pct = row["suitability_ratio"] * 100
        req = crop_requirements.loc[crop]
        rank_text = "TOP PICK" if i == 0 else f"OPTION {i+1}"
        badge_color = "#3F7D53" if i == 0 else "#8A7E6D"

        with st.container(border=True):
            c1, c2 = st.columns([2, 3])
            with c1:
                st.markdown(f"""
                <span style="font-family:'IBM Plex Mono',monospace; font-size:0.78rem; letter-spacing:0.06em;
                    background:{badge_color}; color:white; padding:0.2rem 0.55rem; border-radius:20px;">{rank_text}</span>
                """, unsafe_allow_html=True)
                st.markdown(f'<div class="crop-name">{crop}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="crop-yield">≈ {pred_yield:,.0f} kg/ha expected</div>', unsafe_allow_html=True)
                st.caption(f"Suitability for this soil: {suitability_pct:.0f}% of {crop}'s typical yield · grows in ~{req['Growth Duration (days)']:.0f} days")
            with c2:
                needs_fig = go.Figure()
                categories = ["Nitrogen", "Phosphorus", "Potassium", "Water"]
                needed = [req["Nitrogen Requirement (kg/ha)"], req["Phosphorus Requirement (kg/ha)"],
                          req["Potassium Requirement (kg/ha)"], req["Water Requirement (mm)"]]
                available = [n, p, k, field_state["Avg Rainfall (mm)"] / 5]  # scaled for visual comparability
                needs_fig.add_trace(go.Bar(name="Needed", x=categories, y=needed, marker_color="#E4DDCE"))
                needs_fig.add_trace(go.Bar(name="Currently available", x=categories, y=available, marker_color="#3F7D53"))
                needs_fig.update_layout(
                    barmode="group", height=200, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
                    font=dict(family="Inter", size=11, color="#332A22"),
                )
                st.plotly_chart(needs_fig, use_container_width=True)

    st.markdown("""
    <div class="disclaimer-box">
        <strong>How to read this:</strong> yield estimates come from a model trained on simulated agricultural data,
        not verified field trials — treat them as a relative comparison between crop options, not a guaranteed harvest figure.
        For high-stakes planting decisions, confirm with a local agricultural extension officer or a physical soil test.
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Pathway selector
# ----------------------------------------------------------------------------
pathway = st.radio(
    "How would you like to start?",
    ["🌱 I know what I grew last", "🧪 I have soil test numbers"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Shared location/season inputs
# ----------------------------------------------------------------------------
loc_col1, loc_col2, loc_col3 = st.columns(3)
with loc_col1:
    region = st.selectbox("Region", reference["regions"], index=reference["regions"].index("Tamil Nadu") if "Tamil Nadu" in reference["regions"] else 0)
with loc_col2:
    season = st.selectbox("Growing season", reference["seasons"])
with loc_col3:
    default_soil_type = region_soil_type.loc[region, "Soil Type"] if region in region_soil_type.index else reference["soil_types"][0]
    soil_type = st.selectbox("Soil type", reference["soil_types"], index=reference["soil_types"].index(default_soil_type))

with st.expander("Advanced: rainfall & sunlight (auto-filled from your region — adjust if you know better numbers)"):
    default_rain = float(region_climate.loc[region, "Avg Rainfall (mm)"]) if region in region_climate.index else 1000.0
    default_solar = float(region_climate.loc[region, "Solar Radiation Impact (BTU/sqft)"]) if region in region_climate.index else 20.0
    adv_col1, adv_col2 = st.columns(2)
    with adv_col1:
        rainfall = st.number_input("Average rainfall (mm)", min_value=0.0, max_value=5000.0, value=default_rain, step=50.0)
    with adv_col2:
        solar = st.number_input("Solar radiation (BTU/sqft)", min_value=0.0, max_value=100.0, value=default_solar, step=1.0)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Pathway 1 — Previous crop
# ----------------------------------------------------------------------------
if pathway == "🌱 I know what I grew last":
    st.markdown('<div class="section-label">What did you last harvest here?</div>', unsafe_allow_html=True)
    previous_crop = st.selectbox("Previous crop", reference["previous_crop_options"], label_visibility="collapsed")

    lookup_key = previous_crop if previous_crop in prev_crop_lookup.index else "First planting"
    estimated = prev_crop_lookup.loc[lookup_key]

    st.markdown(
        f'<div class="section-label" style="margin-top:1rem;">Estimated soil left behind by {previous_crop.lower()}</div>',
        unsafe_allow_html=True,
    )
    st.caption("These are typical values for this crop — adjust any of them if you have your own test results.")

    e1, e2, e3 = st.columns(3)
    with e1:
        est_n = st.slider("Nitrogen", 0, 150, int(estimated["Soil Nitrogen"]))
        est_ph = st.slider("Soil pH", 3.5, 9.0, float(estimated["Soil pH"]), step=0.1)
    with e2:
        est_p = st.slider("Phosphorus", 0, 60, int(estimated["Soil Phosphorus"]))
        est_om = st.slider("Organic matter (%)", 0.0, 8.0, float(estimated["Soil Organic Matter (%)"]), step=0.1)
    with e3:
        est_k = st.slider("Potassium", 0, 120, int(estimated["Soil Potassium"]))
        est_moisture = st.slider("Soil moisture (%)", 0.0, 40.0, float(estimated["Soil Moisture (%)"]), step=0.5)

    if st.button("Get recommendations", key="btn_pathway1"):
        show_growing_animation()
        field_state = {
            "Region": region, "Season": season, "Soil Type": soil_type,
            "Soil pH": est_ph, "Soil Nitrogen": est_n, "Soil Phosphorus": est_p,
            "Soil Potassium": est_k, "Soil Organic Matter (%)": est_om, "Soil Moisture (%)": est_moisture,
            "Avg Rainfall (mm)": rainfall, "Solar Radiation Impact (BTU/sqft)": solar,
        }
        render_results(field_state, previous_crop if previous_crop != "First planting" else None)

# ----------------------------------------------------------------------------
# Pathway 2 — Direct soil test numbers
# ----------------------------------------------------------------------------
else:
    st.markdown('<div class="section-label">Enter your soil test numbers</div>', unsafe_allow_html=True)
    st.caption("From a lab report or a home soil test kit. Typical ranges are shown as a guide.")

    t1, t2, t3 = st.columns(3)
    with t1:
        test_n = st.slider("Nitrogen (typical range: 20–140)", 0, 150, 70)
        test_ph = st.slider("Soil pH (typical range: 5.5–7.5)", 3.5, 9.0, 6.5, step=0.1)
    with t2:
        test_p = st.slider("Phosphorus (typical range: 10–50)", 0, 60, 25)
        test_om = st.slider("Organic matter % (typical range: 1–4%)", 0.0, 8.0, 2.5, step=0.1)
    with t3:
        test_k = st.slider("Potassium (typical range: 30–100)", 0, 120, 60)
        test_moisture = st.slider("Soil moisture % (typical range: 10–25%)", 0.0, 40.0, 16.0, step=0.5)

    current_crop = st.selectbox(
        "What's currently growing here, if anything? (used only to label your results)",
        ["Nothing / not sure"] + reference["crops"],
    )

    if st.button("Get recommendations", key="btn_pathway2"):
        show_growing_animation()
        field_state = {
            "Region": region, "Season": season, "Soil Type": soil_type,
            "Soil pH": test_ph, "Soil Nitrogen": test_n, "Soil Phosphorus": test_p,
            "Soil Potassium": test_k, "Soil Organic Matter (%)": test_om, "Soil Moisture (%)": test_moisture,
            "Avg Rainfall (mm)": rainfall, "Solar Radiation Impact (BTU/sqft)": solar,
        }
        render_results(field_state, current_crop if current_crop != "Nothing / not sure" else None)

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(
    "Built as a decision-support tool using simulated Indian agricultural data. "
    "Nitrogen, phosphorus, and potassium roles reflect established agronomy; yield and soil-score figures are model estimates."
)
