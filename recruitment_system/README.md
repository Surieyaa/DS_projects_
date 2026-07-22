# AI Smart Recruitment System — Flask Edition

An end-to-end AI-powered recruitment platform: resume parsing, Sentence-BERT
semantic skill matching, ATS scoring, skill-gap analysis, candidate ranking,
AI resume summaries, AI-generated HR/technical interview questions, a
browser-based voice mock interview, a recruiter analytics dashboard,
email + calendar interview scheduling, and PDF performance reports.

## 1. Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

First run will download the Sentence-BERT model (`all-MiniLM-L6-v2`, ~90MB)
from Hugging Face — make sure you have internet access the first time. If it
can't reach the internet, the app automatically falls back to TF-IDF
similarity so it still runs (see `utils/matcher.py`).

## 2. Run

```bash
python3 app.py
```

Visit **http://localhost:5000**. A SQLite database is created automatically
at `instance/recruitment.db` on first run.

## 3. Walkthrough

1. Go to **Post a Job** → sign up as HR → create a job. Required skills are
   auto-detected from the description.
2. Copy the **Apply link** shown on the job detail page (or visit
   `/jobs` as a candidate) and upload a resume (PDF/DOCX/TXT).
3. The candidate is redirected to a **Results** page with their ATS score,
   sub-score breakdown, skill-gap analysis, and an AI resume summary.
4. From there they can take a **Voice Mock Interview** (uses the browser's
   Web Speech API — Chrome/Edge recommended) which scores each spoken
   answer's relevance.
5. Back on the HR side, the **Job Detail** page shows every candidate
   ranked by ATS score, with charts, status management, interview
   scheduling (sends an email if SMTP env vars are set, and always
   generates a downloadable `.ics` calendar invite), and one-click PDF
   report downloads.

## 4. Optional: real LLM-generated questions/summaries

By default, interview questions come from a curated template bank and
resume summaries use an offline Sentence-BERT centrality method — so the
app works with **zero API keys**. To plug in a real LLM (OpenAI or Groq):

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
pip install openai
```

or

```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=gsk-...
pip install groq
```

See `utils/llm.py`.

## 5. Optional: email sending

Interview scheduling always produces a downloadable `.ics` calendar file.
To also send an email notification, set:

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=you@gmail.com
export SMTP_PASSWORD=your-app-password
```

## 6. Project structure

```
app.py                  Flask routes (all endpoints)
database.py              SQLAlchemy models (HRUser, Job, Candidate, Application)
utils/
  skills_data.py          Skill taxonomy used for parsing, matching, questions
  parser.py               Resume text extraction + info extraction (PyMuPDF)
  matcher.py               Sentence-BERT semantic matching + ATS scoring
  summarizer.py            Embedding-centrality AI resume summary
  questions.py              HR + technical interview question generation
  llm.py                    Optional hosted-LLM hook (OpenAI/Groq)
  pdf_report.py             ReportLab PDF report generator
  scheduler.py              .ics calendar invite + SMTP email
templates/                Jinja2 HTML (dark "neural network" themed UI)
static/css/style.css       Design tokens, animations, glassmorphism
static/js/main.js           Node-network canvas, score rings, dropzone, mic UI
```

## 7. Deploying to Render

This repo is already set up for Render — it includes a `Procfile`,
`render.yaml`, and a `DATA_DIR` env var so your database/uploads survive
redeploys.

**Option A — Blueprint (recommended, one click):**
1. Push this folder to a GitHub repo.
2. In Render: **New → Blueprint**, point it at the repo. Render reads
   `render.yaml` and sets everything up automatically — build command,
   start command, `SECRET_KEY` (auto-generated), and a 1GB persistent
   disk mounted at `/var/data` for the SQLite DB, uploaded resumes, and
   generated PDF reports.
3. Click **Apply**. First deploy takes a few minutes (installing
   `torch`/`sentence-transformers` and pre-downloading the BERT model
   during the build step, so runtime startup is fast).

**Option B — Manual web service:**
1. **New → Web Service**, connect the repo.
2. **Build Command:**
   ```
   pip install -r requirements.txt && python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```
   (the second part pre-caches the model during build, not at runtime)
3. **Start Command:**
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300
   ```
4. Add environment variables: `SECRET_KEY` (any long random string),
   `DATA_DIR=/var/data`.
5. Add a **Disk**: mount path `/var/data`, size 1GB — otherwise your
   database and uploaded resumes are wiped on every redeploy/restart,
   since Render's default filesystem is ephemeral.
6. Pick at least the **Starter** plan — the free tier's ~512MB RAM is
   usually too tight for `torch` + `sentence-transformers` running
   alongside Flask.

**Notes:**
- `--workers 1` is intentional: each gunicorn worker loads its own copy
  of the BERT model, so more workers = more memory, not more speed for
  this workload. `--threads 4` gives you concurrency without that cost.
- SQLite is fine for a portfolio/demo deployment. For real multi-user
  production traffic, swap `SQLALCHEMY_DATABASE_URI` for a managed
  Postgres instance (Render offers one) instead of the persistent disk.
- Passwords are stored in plaintext in this demo (`database.py`,
  `HRUser.password`) — fine for local/demo use, but hash them with
  `werkzeug.security.generate_password_hash` before using this for
  anything real.

Deploying elsewhere (Railway, PythonAnywhere, AWS Elastic Beanstalk,
your own server behind nginx) works the same way — it's a standard
Flask + gunicorn app. Just set `SECRET_KEY` and, if you want
persistence, `DATA_DIR` to point at a writable, persistent path.

## 8. Training / exploring the DL pipeline in Colab

See `AI_Smart_Recruitment_Colab.ipynb` — it walks through resume parsing,
Sentence-BERT embeddings, ATS scoring and skill-gap analysis on sample data,
so you can experiment with the model before/alongside the Flask app.
