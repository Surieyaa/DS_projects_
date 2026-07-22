"""
CardioSense — Early-Stage Cardiovascular Risk Screening
Random Forest feature selection + threshold-tuned SVM classifier
"""

import time
import pickle
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CardioSense — Cardiovascular Risk Screening",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────
# LOAD ARTIFACT
# ──────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_artifact(path="cvd_svm_model.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

artifact = load_artifact()
model = artifact["model"]
scaler = artifact["scaler"]
selected_features = artifact["selected_features"]
health_map = artifact["health_map"]
age_map = artifact["age_map"]
diabetes_map = artifact["diabetes_map"]
best_threshold = float(artifact["best_threshold"])

FULL_FEATURE_ORDER = artifact["full_feature_order"]
UNUSED_COLUMNS = [c for c in FULL_FEATURE_ORDER if c not in selected_features]

DIABETES_UI = {
    "No": "No",
    "Pre-diabetes or borderline": "No, pre-diabetes or borderline diabetes",
    "Yes": "Yes",
}
AGE_OPTIONS = sorted(age_map.keys(), key=lambda k: age_map[k])
HEALTH_OPTIONS = sorted(health_map.keys(), key=lambda k: health_map[k])

# ──────────────────────────────────────────────────────────────────────────
# STYLE
# ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root{
  --bg:#DCEBFB; --navy:#0B2E4F; --navy-soft:#284B6B;
  --coral:#E4572E; --teal:#2A9D8F; --amber:#F4A261; --danger:#C1121F;
  --muted:#5C6B73; --card:#FFFFFF; --line:#E3E9EF;
}

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; color: var(--navy); }
h1, h2, h3, h4, .display { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: linear-gradient(180deg, #EAF3FD 0%, #CFE4F9 100%); }
#MainMenu, footer, header {visibility: hidden;}

/* Force every Streamlit label/text element to a visible, theme-independent color */
label, .stMarkdown, .stMarkdown p, .stCaption, p, span, div[data-testid="stWidgetLabel"] p {
  color: var(--navy) !important;
}

/* Selectbox: dark navy chip with WHITE text for the chosen value */
div[data-baseweb="select"] > div{
  background-color: var(--navy) !important;
  border-color: var(--navy) !important;
  border-radius: 8px !important;
}
div[data-baseweb="select"] > div *{ color: #FFFFFF !important; fill: #FFFFFF !important; }
/* Dropdown menu panel — cover every possible BaseWeb wrapper layer so the
   navy background actually shows behind the option list (not just the
   innermost listbox element, which was leaving a white gap behind it) */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] div[role="listbox"]{
  background-color: var(--navy) !important;
}
/* Every option row, in every state (default / hover / selected) — force
   white text with !important so it beats any inline style BaseWeb applies
   to the currently-selected row */
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] li *,
div[data-baseweb="popover"] li[aria-selected="true"],
div[data-baseweb="popover"] li[aria-selected="true"] *{
  color: #FFFFFF !important;
  background-color: var(--navy) !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"]:hover{
  background-color: var(--navy-soft) !important;
}

/* Number input: dark navy chip, white text */
[data-testid="stNumberInput"] input{
  background-color: var(--navy) !important;
  color: #FFFFFF !important;
  border-radius: 8px !important;
  border-color: var(--navy) !important;
}
[data-testid="stNumberInput"] button{ background-color: var(--navy) !important; }
[data-testid="stNumberInput"] button svg{ fill: #FFFFFF !important; }

/* Slider current-value bubble text */
[data-testid="stSlider"] div[role="slider"]{ background-color: var(--coral) !important; }
[data-testid="stTickBar"] { display:none; }

/* Sidebar text — force white on the dark sidebar */
section[data-testid="stSidebar"]{ background: linear-gradient(180deg,#0B2E4F,#123A5E) !important; }
section[data-testid="stSidebar"] *{ color: #FFFFFF !important; }
section[data-testid="stSidebar"] code{ color: #FFE3C4 !important; }
/* st.code() block and inline `code` spans keep a near-white background by
   default even inside the dark sidebar — force it to match, or the peach
   text above sits on white and becomes nearly invisible */
section[data-testid="stSidebar"] pre,
section[data-testid="stSidebar"] .stCode{
  background-color: var(--navy-soft) !important;
}
section[data-testid="stSidebar"] pre div{
  background-color: transparent !important;
}
section[data-testid="stSidebar"] li code,
section[data-testid="stSidebar"] p code{
  background-color: var(--navy-soft) !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
}
section[data-testid="stSidebar"] hr{ border-color: rgba(255,255,255,0.2) !important; }

/* ---------- HERO ---------- */
.hero-wrap{
  background: linear-gradient(135deg, var(--navy) 0%, var(--navy-soft) 100%);
  border-radius: 20px; padding: 2.4rem 2.6rem 1.6rem 2.6rem; margin-bottom: 1.6rem;
  position: relative; overflow: hidden; box-shadow: 0 12px 30px rgba(11,46,79,0.25);
}
.hero-eyebrow{ color:#9FC4E8; letter-spacing:3px; font-size:0.72rem; font-weight:600; text-transform:uppercase; margin-bottom:6px; }
.hero-title{ color:white; font-size:2.4rem; font-weight:700; margin:0 0 6px 0; line-height:1.1; }
.hero-sub{ color:#C9DCEC; font-size:0.98rem; max-width:640px; margin-bottom:1.1rem; }

.ecg-wrap{ width:100%; height:54px; overflow:hidden; }
.ecg-line{
  stroke: var(--coral); stroke-width:2.4; fill:none;
  stroke-dasharray:1400; stroke-dashoffset:1400;
  animation: draw 3.2s linear infinite;
  filter: drop-shadow(0 0 4px rgba(228,87,46,0.7));
}
@keyframes draw{ 0%{stroke-dashoffset:1400;} 100%{stroke-dashoffset:0;} }

/* ---------- FORM CARDS ---------- */
.section-card{
  background: var(--card); border-radius:16px; padding:1.5rem 1.7rem;
  border:1px solid var(--line); margin-bottom:1.1rem;
}
.section-title{
  font-size:1.05rem; font-weight:700; color:var(--navy) !important; margin-bottom:1rem;
  display:flex; align-items:center; gap:8px; padding-bottom:0.7rem;
  border-bottom: 2px solid var(--line);
}
.section-title .tag{
  font-size:0.65rem; font-weight:700; letter-spacing:1px; background:#EAF1F8;
  color: var(--navy-soft) !important; padding:2px 8px; border-radius:20px; margin-left:auto;
}
.field-label{
  font-size:0.82rem; font-weight:700; color: var(--navy-soft) !important;
  margin-bottom:4px; margin-top:0.4rem; display:flex; align-items:center; gap:6px;
}
.field-hint{ font-size:0.72rem; color: var(--muted) !important; margin-bottom:6px; margin-top:-2px;}

/* ---------- LOADING ANIMATION ---------- */
.loader-wrap{
  text-align:center; padding: 2.8rem 1rem; background: linear-gradient(135deg, var(--navy) 0%, var(--navy-soft) 100%);
  border-radius: 20px; box-shadow: 0 12px 30px rgba(11,46,79,0.25); margin-bottom: 1.1rem;
}
.loader-heart-ring{
  position:relative; width:110px; height:110px; margin:0 auto; display:flex; align-items:center; justify-content:center;
}
.loader-ring{
  position:absolute; width:100%; height:100%; border-radius:50%;
  border: 3px solid rgba(228,87,46,0.55);
  animation: ring-pulse 1.4s ease-out infinite;
}
.loader-ring.delay{ animation-delay: 0.7s; }
@keyframes ring-pulse{
  0% { transform: scale(0.6); opacity: 1; }
  100% { transform: scale(1.4); opacity: 0; }
}
.loader-heart{
  font-size: 3rem; display:inline-block; position:relative; z-index:2;
  animation: heartbeat 0.9s ease-in-out infinite;
  filter: drop-shadow(0 0 10px rgba(228,87,46,0.8));
}
@keyframes heartbeat{
  0%, 100% { transform: scale(1); }
  25% { transform: scale(1.3); }
  40% { transform: scale(0.95); }
  60% { transform: scale(1.2); }
}
.loader-ecg{ width: 280px; height:40px; margin: 1rem auto 0 auto; }
.loader-ecg-line{
  stroke: var(--coral); stroke-width:2.6; fill:none;
  stroke-dasharray:900; stroke-dashoffset:900;
  animation: draw-loader 1.6s linear infinite;
  filter: drop-shadow(0 0 5px rgba(228,87,46,0.9));
}
@keyframes draw-loader{ 0%{stroke-dashoffset:900;} 100%{stroke-dashoffset:0;} }
.loader-text{
  font-family:'Space Grotesk', sans-serif; color: #FFFFFF !important;
  font-weight:600; margin-top:1rem; font-size:1.1rem; letter-spacing:0.3px;
}
.loader-sub{ color:#B9D4EC !important; font-size:0.82rem; margin-top:4px; }

/* ---------- RESULT ---------- */
.result-card{
  border-radius:18px; padding:1.8rem 2rem; color:white !important; position:relative;
  overflow:hidden; animation: pulse-glow 2.6s ease-in-out infinite;
}
.result-card *, .result-card .risk-label, .result-card .risk-sub { color: white !important; }
.result-low{ background: linear-gradient(135deg,#1E7F73,#2A9D8F); }
.result-borderline{ background: linear-gradient(135deg,#C98A1E,#F4A261); }
.result-elevated{ background: linear-gradient(135deg,#C1520E,#E4572E); }
.result-high{ background: linear-gradient(135deg,#8C0F17,#C1121F); }
@keyframes pulse-glow{
  0%,100%{ box-shadow: 0 0 0 0 rgba(255,255,255,0.0), 0 10px 30px rgba(0,0,0,0.18); }
  50%{ box-shadow: 0 0 0 10px rgba(255,255,255,0.06), 0 10px 30px rgba(0,0,0,0.18); }
}
.risk-label{ font-family:'Space Grotesk', sans-serif; font-size:1.8rem; font-weight:700; margin-bottom:2px; }
.risk-sub{ opacity:0.92; font-size:0.92rem; }

.factor-pill{
  display:inline-block; background:#EAF1F8; color: var(--navy-soft) !important;
  border-radius:20px; padding:5px 12px; font-size:0.8rem; margin:3px 4px 3px 0; font-weight:600;
}
.disclaimer{
  font-size:0.8rem; color: var(--muted) !important; border-left:3px solid var(--line);
  padding:10px 14px; background:#FBFCFD; border-radius:6px;
}

.stButton>button{
  background: var(--coral); color:white !important; border:none; border-radius:10px;
  padding:0.75rem 1rem; font-weight:700; font-family:'Space Grotesk', sans-serif;
  letter-spacing:0.3px; transition: transform 0.15s ease, box-shadow 0.15s ease; width:100%;
  font-size: 1rem;
}
.stButton>button:hover{ transform: translateY(-1px); box-shadow: 0 6px 16px rgba(228,87,46,0.35); }
/* Global p/span rule above would otherwise override the button's inner text color */
.stButton>button p, .stButton>button span, .stButton>button div{ color:#FFFFFF !important; }

/* Form submit buttons (e.g. "Analyze Risk") use a different container than st.button */
div[data-testid="stFormSubmitButton"] button{
  background: var(--coral) !important; border:none !important; border-radius:10px !important;
  padding:0.75rem 1rem !important; font-weight:700 !important;
  font-family:'Space Grotesk', sans-serif !important; letter-spacing:0.3px !important;
  width:100% !important; font-size:1rem !important;
}
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stFormSubmitButton"] button p,
div[data-testid="stFormSubmitButton"] button span,
div[data-testid="stFormSubmitButton"] button div{ color:#FFFFFF !important; }
div[data-testid="stFormSubmitButton"] button:hover{
  transform: translateY(-1px); box-shadow: 0 6px 16px rgba(228,87,46,0.35);
}
[data-testid="stMetricValue"]{ font-family:'Space Grotesk', sans-serif; color:var(--navy) !important; }
[data-testid="stMetricLabel"]{ color: var(--navy-soft) !important; }
hr { border-color: var(--line); }

/* ---------- TOP BRAND BAR ---------- */
.navbar{
  display:flex; align-items:center; justify-content:space-between;
  background: #FFFFFF; border-radius:16px; padding:0.9rem 1.6rem;
  margin-bottom:1rem; box-shadow: 0 4px 14px rgba(11,46,79,0.08);
  border: 1px solid var(--line);
}
.navbar-brand{
  font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:1.3rem;
  color: var(--navy) !important; display:flex; align-items:center; gap:10px;
}
.navbar-brand .accent{ color: var(--coral) !important; }
.navbar-tag{
  font-size:0.75rem; font-weight:600; color:var(--navy-soft) !important;
  background:#EAF1F8; padding:5px 12px; border-radius:20px;
}

/* ---------- FORM GROUP TITLE ---------- */
.form-group-title{
  font-family:'Space Grotesk', sans-serif; font-size:1.25rem; font-weight:700;
  color: var(--navy) !important; margin: 0.4rem 0 0.9rem 0; text-align:center;
}
.form-group-sub{
  text-align:center; color: var(--muted) !important; font-size:0.88rem; margin-bottom:1.2rem;
}
</style>
""", unsafe_allow_html=True)

def field_label(text, hint=None):
    st.markdown(f'<div class="field-label">{text}</div>', unsafe_allow_html=True)
    if hint:
        st.markdown(f'<div class="field-hint">{hint}</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# TOP BRAND BAR
# ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
  <div class="navbar-brand">🫀 Cardio<span class="accent">Sense</span> AI</div>
  <div class="navbar-tag">Precision Cardiac Risk Intelligence</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
  <div class="hero-eyebrow">EARLY-STAGE SCREENING · RANDOM FOREST + OPTIMIZED SVM</div>
  <div class="hero-title">🫀 CardioSense</div>
  <div class="hero-sub">
    A machine-learning screening tool that estimates cardiovascular disease risk from lifestyle
    and health indicators. Built on Random-Forest feature selection and a threshold-tuned SVM
    classifier trained on BRFSS health-survey data.
  </div>
  <div class="ecg-wrap">
    <svg viewBox="0 0 1400 54" class="ecg-wrap" preserveAspectRatio="none">
      <path class="ecg-line" d="M0,27 L120,27 L145,27 L160,10 L180,45 L200,5 L220,48 L240,27 L340,27
               L360,27 L385,27 L400,10 L420,45 L440,5 L460,48 L480,27 L580,27
               L600,27 L625,27 L640,10 L660,45 L680,5 L700,48 L720,27 L820,27
               L840,27 L865,27 L880,10 L900,45 L920,5 L940,48 L960,27 L1060,27
               L1080,27 L1105,27 L1120,10 L1140,45 L1160,5 L1180,48 L1200,27 L1400,27"/>
    </svg>
  </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# FORM — full width, every field explicitly titled
# ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="form-group-title">🩻 Complete Your Health Assessment</div>
<div class="form-group-sub">Fill in the details below — it takes less than a minute</div>
""", unsafe_allow_html=True)

with st.form("risk_form"):

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 Patient Profile <span class="tag">STEP 1</span></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        field_label("📅 Age Category")
        age_label = st.selectbox("Age category", AGE_OPTIONS,
                                  index=AGE_OPTIONS.index("45-49"), label_visibility="collapsed")
    with c2:
        field_label("🩺 Self-Rated General Health")
        health_label = st.selectbox("General health", HEALTH_OPTIONS, index=2, label_visibility="collapsed")

    c3, c4 = st.columns(2)
    with c3:
        field_label("📏 Height (cm)")
        height_cm = st.number_input("Height", min_value=91.0, max_value=241.0,
                                     value=170.0, step=1.0, label_visibility="collapsed")
    with c4:
        field_label("⚖️ Weight (kg)")
        weight_kg = st.number_input("Weight", min_value=25.0, max_value=293.0,
                                     value=75.0, step=0.5, label_visibility="collapsed")

    bmi = weight_kg / ((height_cm / 100) ** 2)
    st.caption(f"Calculated BMI: **{bmi:.1f}**")

    field_label("💉 Diabetes Status")
    diabetes_label = st.selectbox("Diabetes", list(DIABETES_UI.keys()), label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🥗 Lifestyle & Diet <span class="tag">STEP 2</span></div>', unsafe_allow_html=True)

    field_label("🍎 Fruit Consumption", "Times per month")
    fruit = st.slider("Fruit", 0, 120, 30, label_visibility="collapsed")

    field_label("🥦 Green Vegetable Consumption", "Times per month")
    greens = st.slider("Greens", 0, 128, 12, label_visibility="collapsed")

    c5, c6 = st.columns(2)
    with c5:
        field_label("🦴 Arthritis")
        arthritis_label = st.selectbox("Arthritis", ["No", "Yes"], label_visibility="collapsed")
    with c6:
        field_label("🚬 Smoking History")
        smoking_label = st.selectbox("Smoking history", ["No", "Yes"], label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

    submitted = st.form_submit_button("🔍  Analyze Risk")

# ──────────────────────────────────────────────────────────────────────────
# RESULTS — appear below the form, full width, with loading animation
# ──────────────────────────────────────────────────────────────────────────
if submitted:
    loader = st.empty()
    loader.markdown("""
    <div class="loader-wrap">
      <div class="loader-heart-ring">
        <div class="loader-ring"></div>
        <div class="loader-ring delay"></div>
        <div class="loader-heart">🫀</div>
      </div>
      <svg viewBox="0 0 280 40" class="loader-ecg">
        <path class="loader-ecg-line" d="M0,20 L60,20 L72,20 L80,6 L90,34 L100,2 L110,36 L120,20 L180,20
                 L192,20 L200,6 L210,34 L220,2 L230,36 L240,20 L280,20"/>
      </svg>
      <div class="loader-text">Analyzing cardiovascular risk factors…</div>
      <div class="loader-sub">Running Random Forest &amp; SVM inference</div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(1.8)
    loader.empty()

    row = {c: 0 for c in UNUSED_COLUMNS}
    row["General_Health"] = health_map[health_label]
    row["Diabetes"] = diabetes_map[DIABETES_UI[diabetes_label]]
    row["Age_Category"] = age_map[age_label]
    row["Height_(cm)"] = height_cm
    row["Weight_(kg)"] = weight_kg
    row["BMI"] = bmi
    row["Fruit_Consumption"] = fruit
    row["Green_Vegetables_Consumption"] = greens
    row["Arthritis"] = 1 if arthritis_label == "Yes" else 0
    row["Smoking_History"] = 1 if smoking_label == "Yes" else 0

    X_full = pd.DataFrame([row])[FULL_FEATURE_ORDER]
    X_scaled = pd.DataFrame(scaler.transform(X_full), columns=FULL_FEATURE_ORDER)
    X_input = X_scaled[selected_features]
    proba = float(model.predict_proba(X_input)[0, 1])

    # Risk tiers — calibrated so predicted probability reflects true population risk.
    # Population base rate is ~8%; tiers set from the calibrated test-set distribution
    # (median ~4.4%, 90th pct ~22%, 99th pct ~27%) rather than arbitrary round numbers.
    if proba < 0.05:
        tier, css_class, sub = "Healthy", "result-low", "Below the typical population baseline"
    elif proba < best_threshold:
        tier, css_class, sub = "Borderline", "result-borderline", "Some risk factors present — monitor"
    elif proba < 0.30:
        tier, css_class, sub = "Elevated Risk", "result-elevated", "Above the model's decision threshold"
    else:
        tier, css_class, sub = "High Risk", "result-high", "Strong indicators — clinical follow-up advised"

    st.markdown(f"""
    <div class="result-card {css_class}">
      <div class="risk-label">{tier}</div>
      <div class="risk-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    res_left, res_right = st.columns([1, 1.2], gap="large")

    with res_left:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=proba * 100,
            number={"suffix": "%", "font": {"size": 40, "family": "Space Grotesk"}},
            gauge={
                "axis": {"range": [0, 50], "tickwidth": 1, "tickcolor": "#5C6B73"},
                "bar": {"color": "#0B2E4F", "thickness": 0.28},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 5], "color": "#CDEDE8"},
                    {"range": [5, best_threshold * 100], "color": "#FBE3C4"},
                    {"range": [best_threshold * 100, 30], "color": "#F6C4AE"},
                    {"range": [30, 50], "color": "#F1AEB0"},
                ],
                "threshold": {
                    "line": {"color": "#C1121F", "width": 3},
                    "thickness": 0.8,
                    "value": best_threshold * 100,
                },
            },
        ))
        fig.update_layout(height=260, margin=dict(l=20, r=20, t=10, b=10),
                           paper_bgcolor="rgba(0,0,0,0)", font={"color": "#0B2E4F"})
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        m1, m2, m3 = st.columns(3)
        m1.metric("Risk probability", f"{proba*100:.1f}%")
        m2.metric("Decision threshold", f"{best_threshold*100:.1f}%")
        m3.metric("BMI", f"{bmi:.1f}")

    with res_right:
        st.markdown("""
        <div class="section-card" style="height:100%;">
          <div class="section-title">📊 Top Predictive Factors</div>
          <div>
        """ + "".join(f'<span class="factor-pill">{f.replace("_"," ")}</span>' for f in selected_features) + """
          </div>
          <div style="margin-top:12px; font-size:0.85rem; color:var(--muted);">
            Ranked by Random-Forest feature importance during model development — these ten
            features carry the most predictive weight in the SVM's decision boundary.
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer">
      ⚠️ CardioSense is a machine-learning screening demo trained on population survey data
      (BRFSS). It is <b>not a diagnostic tool</b> and does not replace professional medical
      evaluation. Please consult a qualified healthcare provider for any health concerns.
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🫀 About CardioSense")
    st.markdown("""
    **Pipeline**
    - Random Forest → top-10 feature selection
    - Features standardized (StandardScaler)
    - SVM (RBF kernel) — class-balanced, hyperparameters tuned via `RandomizedSearchCV`
    - Decision threshold tuned via precision–recall F1 optimization
    """)
    st.markdown("---")
    st.markdown("**Model configuration**")
    st.code(f"""kernel = {artifact['svm_kernel']}
C = {artifact['svm_C']}
gamma = {artifact['svm_gamma']}
calibration = {artifact['calibration_method']} (isotonic)
threshold = {best_threshold:.3f}""", language="text")
    st.markdown("---")
    st.markdown("**Methodology notes**")
    st.caption(
        "Probabilities are isotonic-calibrated so the displayed risk % reflects "
        "true population rates (~8% baseline) rather than the raw, class-balanced "
        "SVM score, which was compressed into an uninformative 17–54% band."
    )
    st.markdown("---")
    st.caption("Dataset: BRFSS-derived Cardiovascular Diseases Risk Prediction (Kaggle)")
