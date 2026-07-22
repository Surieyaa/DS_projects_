# PulseFit AI — Intelligent Personal Gym Assistant

An AI fitness chatbot built with Flask: create an account, tell it your goal in plain English,
and get exercise recommendations (with GIFs), a Tamil Nadu regional diet plan, a weekly workout
split, BMI/calorie tracking, and a downloadable PDF progress report.

## What's inside

- **NLP chatbot** (`chatbot/nlp_engine.py`) — rule/regex-based intent detection (no heavy ML
  dependency to install), detects: goal (muscle gain, fat loss, six-pack, bodybuilding, general
  fitness), body part, equipment, diet requests, weekly-plan requests, BMI questions, motivation
  requests, and free-text exercise search.
- **Exercise dataset** (`data/exercises.json`) — 1,324 exercises sourced from the public
  [hasaneyldrm/exercises-dataset](https://github.com/hasaneyldrm/exercises-dataset) repo (the
  same style of data as Kaggle's ExerciseDB Fitness Exercises Dataset: name, body part, target
  muscle, secondary muscles, equipment, step-by-step instructions). GIFs are 180×180 and served
  directly from GitHub's CDN, so the app doesn't need to store ~1,300 gif files locally.
- **Diet dataset** (`data/meals.json`) — converted from your uploaded `tamil_nadu_meals_csv.xlsx`
  (189 dishes: title, ingredients, veg/non-veg, meal time, calories, protein, carbs, fat, sodium).
- **Auth** — Flask sessions + Werkzeug password hashing (`auth.py`).
- **Engines** (`engines/`) — BMI/BMR/TDEE calculator, exercise recommender, diet recommender,
  ReportLab PDF report generator.
- **UI** — custom glassmorphic dark theme ("PulseFit"), animated aurora background, chat interface
  with exercise/diet cards, dashboard with stats, progress page with a Chart.js weight trend.

## Quick start

```bash
cd fitness_ai
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

Visit **http://127.0.0.1:5000**, register an account, fill in your profile, then open the AI Coach
and try:

- "I want a bigger chest"
- "I want six pack abs"
- "I want to lose weight"
- "give me a full weekly workout plan"
- "suggest a high protein diet"
- "I only have dumbbells"
- "motivate me"
- "what's my bmi"

## Database

Defaults to a local SQLite file (`instance/pulsefit.db`) so it runs with zero setup. To use MySQL
(as in the original spec) instead, install a driver (`PyMySQL` is already in requirements.txt) and
set an environment variable before running:

```bash
export DATABASE_URL="mysql+pymysql://user:password@localhost/pulsefit"
```

## Project structure

```
fitness_ai/
├── app.py                 # App factory / entry point
├── config.py               # Config incl. DB URI, dataset paths
├── extensions.py           # SQLAlchemy instance
├── models.py                # User, Profile, ChatLog, ProgressLog
├── auth.py                  # Register / login / logout
├── main.py                   # Dashboard, profile, chat API, progress, PDF export
├── chatbot/
│   ├── nlp_engine.py         # Intent detection
│   └── quotes.py             # Motivational quotes & fallback responses
├── engines/
│   ├── bmi.py                 # BMI, BMR/TDEE, protein targets
│   ├── exercise_engine.py     # Body-part/goal exercise filtering + weekly split
│   ├── diet_engine.py         # Meal filtering by diet/goal/slot
│   └── pdf_report.py          # ReportLab PDF report
├── data/
│   ├── exercises.json        # 1,324 exercises (GIF URLs point to GitHub CDN)
│   └── meals.json            # 189 Tamil Nadu meals
├── templates/                # Jinja2 templates
└── static/
    ├── css/style.css          # PulseFit visual theme
    └── js/                    # chat.js, app.js
```

## Ideas to extend further

- Swap the regex NLP engine for `sentence-transformers` semantic matching if you want fuzzier
  intent detection (the interface in `nlp_engine.detect_intent` is a drop-in replacement point).
- Add a "favorite exercises" table and a streak/badge system on the dashboard.
- Add water-intake and sleep tracking to the Progress page.
- Cache `data/exercises.json` GIFs locally if you need the app to work fully offline.
- Add an admin view to edit/add meals or exercises without touching the JSON directly.
