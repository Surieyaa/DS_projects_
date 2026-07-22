# 🚀 Data Science & Machine Learning Portfolio

Welcome to my portfolio of Data Science, Machine Learning, and Full-Stack AI applications. This repository houses five distinct, production-ready projects ranging from medical risk screening and agricultural cycle recommendations to computer vision driver monitoring, personal fitness coaching, and AI recruitment systems.

Each project demonstrates end-to-end engineering, addressing real-world ML design challenges such as class imbalance, probability calibration, reverse-causality bias, model selection, and efficient edge/browser inference.

---

## 📂 Portfolio Overview

| Project | Category | Key Tech Stack | Key Highlight / Challenge Solved |
| :--- | :--- | :--- | :--- |
| [🫀 CardioSense](./CardioSense) | Medical Risk Screening | SVM, Streamlit, Scikit-Learn | Corrected **reverse-causality** and **probability miscalibration** (isotonic) |
| [🌾 CropCycle](./crop_recommend) | Precision Agriculture | RandomForest, Streamlit, Plotly | Designed **suitability ratio** ranking to resolve raw yield scale bias |
| [🛡️ DriveGuard](./driveguard-project) | Computer Vision (Safety) | Keras CNN, Flask, WebRTC | Unified two datasets into **one 9-class CNN**; real-time client-side webcam feed |
| [⚡ PulseFit AI](./fitness_ai) | AI Assistant & Chatbot | Flask, SQLite, NLP Engine, ReportLab | Fast, offline regex-based **NLP engine**; Tamil Nadu meal dataset; glassmorphic UI |
| [💼 AI Recruitment](./recruitment_system) | Semantic Search (HR) | Sentence-BERT, Flask, Web Speech API | **Semantic skill matching** via S-BERT; interactive web speech mock interviews |

---

## 🛠️ Project Deep Dives

---

### 1. 🫀 CardioSense — Cardiovascular Disease Risk Screening
An interactive screening tool that estimates cardiovascular disease risk from everyday lifestyle factors without requiring clinical lab tests.

* **Tech Stack:** Python, Scikit-Learn, Streamlit, Pandas, NumPy
* **Core ML Architecture:** Feature selection via Random Forest, classification via a threshold-tuned, isotonic-calibrated Support Vector Machine (SVM).
* **Key Challenges Solved:**
  1. **Reverse-Causality Bias:** Raw data showed unhealthy habits (like fried food or alcohol) were negatively correlated with heart disease because diagnosed patients cut back *after* diagnosis. Corrected by excluding these features to prevent the model from learning harmful shortcuts.
  2. **Probability Calibration:** Correcting class imbalance skewed predicted probabilities into a narrow, uninformative band. Solved using **Isotonic Calibration** to map raw outputs to true population prevalence (~8%).
  3. **High Recall Tuning:** Adjusted the decision boundary to achieve **10x higher recall** compared to default Random Forest, ensuring high sensitivity for medical screening.

👉 **Explore Project:** [`/CardioSense`](./CardioSense)

---

### 2. 🌾 CropCycle — Soil-Aware Crop Rotation Recommender
A precision agriculture tool that recommends optimal crop rotation schedules based on soil chemistry, climate, and previous crop footprint.

* **Tech Stack:** Python, Scikit-Learn (RandomForestRegressor), Streamlit, Plotly, Pandas
* **Core ML Architecture:** Random Forest Regressor predicting yield ratios based on Soil N-P-K, pH, moisture, season, and region.
* **Key Challenges Solved:**
  1. **Yield Scale Bias:** Direct yield prediction over-recommended high-yield crops (like Rice or Maize) regardless of soil fit. Solved by predicting a **suitability ratio** (predicted yield / crop baseline yield) to bubble up optimal crops (like Chickpea) when appropriate.
  2. **Feature Leakage & Redundancy:** Demonstrated that explicit "previous crop" labels were redundant when real soil chemical readings were present, simplifying the model feature space.

👉 **Explore Project:** [`/crop_recommend`](./crop_recommend)

---

### 3. 🛡️ DriveGuard — Driver Drowsiness Detection
A computer vision driver safety monitoring app that classifies safety states in real-time and sounds alarms during sustained danger.

* **Tech Stack:** Keras/TensorFlow, Flask, OpenCV, JavaScript, HTML5/CSS3
* **Core ML Architecture:** 2D Convolutional Neural Network (CNN) classifying 9 driver states (`Drowsy`, `Yawn`, `SafeDriving`, `DangerousDriving`, etc.).
* **Key Challenges Solved:**
  1. **Single Model vs. Multiple Pipelines:** Combined two different Kaggle datasets (one binary, one 7-class) using symlinks and mapped them to a single **9-class classification model** with custom risk mapping (`safe`, `warning`, `danger`).
  2. **Client-Side Camera Capture:** Captured frames client-side via browser `getUserMedia` and sent base64 frames to the Flask server, decoupling inference from server hardware webcam requirements.

👉 **Explore Project:** [`/driveguard-project`](./driveguard-project)

---

### 4. ⚡ PulseFit AI — Intelligent Personal Gym Assistant
A comprehensive AI fitness companion providing conversational workout planning, nutrition guides, and downloadable progress reports.

* **Tech Stack:** Flask, SQLAlchemy (SQLite/MySQL), Python NLP Engine, ReportLab PDF, Chart.js
* **Core NLP Engine:** Lightweight regex-based intent classifier mapping goal, body part, equipment, and diet requests without heavy PyTorch dependencies.
* **Key Features:**
  1. **Tamil Nadu Regional Diet:** Meal recommendation engine powered by a custom dataset of 189 regional South Indian dishes.
  2. **Exercise database:** Integrates 1,324 exercises with dynamically rendered GIFs served via CDN to optimize application size.
  3. **Visual Aesthetics:** Dark glassmorphic user interface featuring animated aurora backgrounds, dashboard weight tracking, and a clean chat interface.

👉 **Explore Project:** [`/fitness_ai`](./fitness_ai)

---

### 5. 💼 AI Smart Recruitment System — Flask Edition
An end-to-end recruitment platform that parses resumes, calculates ATS matching scores, analyzes skill gaps, and ranks candidates.

* **Tech Stack:** Sentence-BERT (Hugging Face), Flask, PyMuPDF, ReportLab PDF, Web Speech API
* **Core ML Architecture:** Semantic embedding matching via `all-MiniLM-L6-v2` with automated fallback to TF-IDF cosine similarity for offline usage.
* **Key Features:**
  1. **Voice Mock Interview:** Uses browser-based Speech-to-Text to let candidates answer interview questions and scores answer relevance.
  2. **ATS Scoring & Skill-Gap Analysis:** Extracts skills using rule-based taxonomies and performs semantic similarity scoring.
  3. **HR Dashboard:** Beautiful recruiter interface with analytics charts, custom status tracking, `.ics` calendar scheduling, and automated PDF candidate report generation.

👉 **Explore Project:** [`/recruitment_system`](./recruitment_system)

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
