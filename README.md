# 🚀 Data Science & Machine Learning Portfolio

Welcome to my portfolio of high-impact Data Science, Machine Learning, and Full-Stack AI applications. This repository houses five distinct, production-ready projects ranging from medical risk screening and agricultural cycle recommendations to computer vision driver monitoring, personal fitness coaching, and AI recruitment systems.

Each project is designed to address real-world ML design challenges such as class imbalance, probability calibration, reverse-causality bias, model selection, and efficient edge/browser inference.

---

## 📂 Portfolio Overview

| Project | Category | Tech Stack | Engineering Highlights & Challenges Solved |
| :--- | :--- | :--- | :--- |
| **🫀 CardioSense** | Medical Risk Screening | `Python` `SVM` `Streamlit` `Scikit-Learn` | • Eliminated **reverse-causality bias**<br>• Corrected class imbalance via **Isotonic Calibration** |
| **🌾 CropCycle** | Precision Agriculture | `Python` `RandomForest` `Streamlit` `Plotly` | • Resolved **yield scale bias** using a custom **suitability ratio** metrics engine |
| **🛡️ DriveGuard** | Computer Vision (Safety) | `Keras CNN` `Flask` `WebRTC` `OpenCV` | • Consolidated two disparate datasets into a single **9-class CNN**<br>• Optimized client-side WebRTC frame ingestion |
| **⚡ PulseFit AI** | AI Gym Assistant | `Flask` `SQLite` `NLP Engine` `ReportLab` | • Custom regex-based fast offline NLP engine<br>• Curated Tamil Nadu regional diet database (189 dishes) |
| **💼 AI Recruitment** | Semantic Search & HR | `Sentence-BERT` `Flask` `Web Speech API` | • Semantic skill embedding similarity scoring<br>• Interactive voice mock interview via Web Speech API |

---

## 🛠️ Project Deep Dives

### 1. 🫀 CardioSense — Cardiovascular Disease Risk Screening
An interactive screening application that estimates cardiovascular disease risk from everyday lifestyle factors without requiring clinical lab tests.

* **Tech Stack:** `Python` `Scikit-Learn` `Streamlit` `Pandas` `NumPy`
* **Core ML Architecture:** Feature selection via Random Forest; classification via a threshold-tuned, isotonic-calibrated Support Vector Machine (SVM).
* **Key Challenges Solved:**
  * ⚠️ **Reverse-Causality Bias:** Raw correlation showed unhealthy habits (like alcohol or fried food consumption) were negatively correlated with heart disease because diagnosed patients changed their habits *post-diagnosis*. Excluded these features to prevent model shortcut learning.
  * ⚖️ **Probability Calibration:** Skewed predicted probabilities were mapped to true population prevalence (~8%) using **Isotonic Calibration**, producing realistic, actionable risk probabilities.
  * 🎯 **High Recall Tuning:** Adjusted the decision boundary to achieve **10x higher recall** compared to default models, ensuring maximum sensitivity for medical screening.

👉 **Project Directory:** `CardioSense`

---

### 2. 🌾 CropCycle — Soil-Aware Crop Rotation Recommender
A precision agriculture tool that recommends optimal crop rotation schedules based on soil chemistry, climate, and previous crop footprint.

* **Tech Stack:** `Python` `Scikit-Learn (RandomForestRegressor)` `Streamlit` `Plotly` `Pandas`
* **Core ML Architecture:** Random Forest Regressor predicting yield ratios based on Soil N-P-K, pH, moisture, season, and region.
* **Key Challenges Solved:**
  * ⚖️ **Yield Scale Bias:** Direct yield prediction over-recommended high-yield crops (like Rice or Maize) regardless of soil fit. Solved by predicting a **suitability ratio** (predicted yield / crop baseline yield) to bubble up optimal crops (like Chickpea) when appropriate.
  * 🧼 **Feature Leakage & Redundancy:** Demonstrated that explicit "previous crop" labels were redundant when real soil chemical readings were present, simplifying the model feature space.

👉 **Project Directory:** `crop_recommend`

---

### 3. 🛡️ DriveGuard — Driver Drowsiness Detection
A computer vision driver safety monitoring app that classifies safety states in real-time and sounds alarms during sustained danger.

* **Tech Stack:** `Keras/TensorFlow` `Flask` `OpenCV` `JavaScript` `HTML5/CSS3`
* **Core ML Architecture:** 2D Convolutional Neural Network (CNN) classifying 9 driver states (`Drowsy`, `Yawn`, `SafeDriving`, `DangerousDriving`, etc.).
* **Key Challenges Solved:**
  * 🧠 **Single Model vs. Multiple Pipelines:** Combined two different Kaggle datasets (one binary, one 7-class) using symlinks and mapped them to a single **9-class classification model** with custom risk mapping (`safe`, `warning`, `danger`).
  * 🌐 **Client-Side Camera Capture:** Captured frames client-side via browser `getUserMedia` and sent base64 frames to the Flask server, decoupling inference from server hardware webcam requirements.

👉 **Project Directory:** `driveguard-project`

---

### 4. ⚡ PulseFit AI — Intelligent Personal Gym Assistant
A comprehensive AI fitness companion providing conversational workout planning, nutrition guides, and downloadable progress reports.

* **Tech Stack:** `Flask` `SQLAlchemy (SQLite/MySQL)` `Python NLP Engine` `ReportLab PDF` `Chart.js`
* **Core NLP Engine:** Lightweight regex-based intent classifier mapping goal, body part, equipment, and diet requests without heavy PyTorch dependencies.
* **Key Features:**
  * 🍛 **Tamil Nadu Regional Diet:** Meal recommendation engine powered by a custom dataset of 189 regional South Indian dishes.
  * 🏋️ **Exercise Database:** Integrates 1,324 exercises with dynamically rendered GIFs served via CDN to optimize application size.
  * 💅 **Visual Aesthetics:** Dark glassmorphic user interface featuring animated aurora backgrounds, dashboard weight tracking, and a clean chat interface.

👉 **Project Directory:** `fitness_ai`

---

### 5. 💼 AI Smart Recruitment System — Flask Edition
An end-to-end recruitment platform that parses resumes, calculates ATS matching scores, analyzes skill gaps, and ranks candidates.

* **Tech Stack:** `Sentence-BERT (Hugging Face)` `Flask` `PyMuPDF` `ReportLab PDF` `Web Speech API`
* **Core ML Architecture:** Semantic embedding matching via `all-MiniLM-L6-v2` with automated fallback to TF-IDF cosine similarity for offline usage.
* **Key Features:**
  * 🎙️ **Voice Mock Interview:** Uses browser-based Speech-to-Text to let candidates answer interview questions and scores answer relevance.
  * 📊 **ATS Scoring & Skill-Gap Analysis:** Extracts skills using rule-based taxonomies and performs semantic similarity scoring.
  * 📈 **HR Dashboard:** Beautiful recruiter interface with analytics charts, custom status tracking, `.ics` calendar scheduling, and automated PDF candidate report generation.

👉 **Project Directory:** `recruitment_system`

---

## ⚙️ Quick Start

To run any of the applications locally, clone the repository and navigate into the target project folder.

### Prerequisites
* Python 3.10+
* Git

```bash
# Clone the repository
git clone https://github.com/Surieyaa/DS_Projects.git
cd DS_Projects
```

### Running Streamlit Apps (CardioSense / CropCycle)
```bash
# 1. CardioSense
cd CardioSense
pip install -r requirements.txt
streamlit run app.py

# 2. CropCycle
cd ../crop_recommend
pip install -r requirements.txt
streamlit run app.py
```

### Running Flask Apps (DriveGuard / PulseFit / Recruitment System)
```bash
# 1. DriveGuard
cd driveguard-project
pip install -r requirements.txt
python app.py  # Open http://localhost:5000

# 2. PulseFit AI
cd ../fitness_ai
pip install -r requirements.txt
python app.py  # Open http://localhost:5000

# 3. AI Recruitment System
cd ../recruitment_system
pip install -r requirements.txt
python app.py  # Open http://localhost:5000
```

---

## 🎨 Design & Engineering Standards

* **User-Centric Design:** Every project features a custom, high-fidelity user interface—ranging from glassmorphic dark mode to farmland-inspired light themes.
* **Robust Fallbacks:** Applications are designed with offline/local fallbacks (e.g., Sentence-BERT falling back to TF-IDF, LLMs falling back to curated templates) so that they run seamlessly with zero configuration.
* **Clinical & Practical Safety:** Model evaluations prioritize metrics that matter in production—such as Recall in medical screening and relative suitability ratios in agriculture.

---

Feel free to browse through each directory to view source notebooks, dataset schemas, and full implementation code. For any questions or suggestions, please open an issue!
