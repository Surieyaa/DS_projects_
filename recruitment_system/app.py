import os
import uuid
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for,
                    session, flash, jsonify, send_file, abort)
from werkzeug.utils import secure_filename

from database import db, HRUser, Job, Candidate, Application
from utils.parser import parse_resume
from utils.matcher import compute_ats_score, skill_gap, rank_candidates
from utils.summarizer import summarize_resume
from utils.questions import generate_questions
from utils.pdf_report import generate_report
from utils.scheduler import generate_ics, send_interview_email

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR lets you point uploads/reports/the SQLite DB at a persistent
# disk (e.g. Render Disks, mounted at /var/data) so they survive
# redeploys. Defaults to the project folder for local development.
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
REPORT_DIR = os.path.join(DATA_DIR, "reports")
ALLOWED_EXT = {"pdf", "docx", "doc", "txt"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(DATA_DIR, "instance", "recruitment.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

db.init_app(app)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "instance"), exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def current_hr():
    uid = session.get("hr_user_id")
    return HRUser.query.get(uid) if uid else None


# ---------------------------------------------------------------- landing
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------- HR auth
@app.route("/hr/signup", methods=["GET", "POST"])
def hr_signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        company = request.form.get("company", "Your Company").strip()
        if HRUser.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return redirect(url_for("hr_signup"))
        user = HRUser(username=username, password=password, company=company)
        db.session.add(user)
        db.session.commit()
        session["hr_user_id"] = user.id
        return redirect(url_for("hr_dashboard"))
    return render_template("hr_signup.html")


@app.route("/hr/login", methods=["GET", "POST"])
def hr_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = HRUser.query.filter_by(username=username, password=password).first()
        if not user:
            flash("Invalid credentials.", "error")
            return redirect(url_for("hr_login"))
        session["hr_user_id"] = user.id
        return redirect(url_for("hr_dashboard"))
    return render_template("hr_login.html")


@app.route("/hr/logout")
def hr_logout():
    session.pop("hr_user_id", None)
    return redirect(url_for("index"))


# ---------------------------------------------------------------- HR dashboard / jobs
@app.route("/hr/dashboard")
def hr_dashboard():
    hr = current_hr()
    if not hr:
        return redirect(url_for("hr_login"))
    jobs = Job.query.filter_by(created_by=hr.id).order_by(Job.created_at.desc()).all()
    job_stats = []
    for j in jobs:
        apps = j.applications
        job_stats.append({
            "job": j,
            "count": len(apps),
            "avg_score": round(sum(a.ats_score for a in apps) / len(apps), 1) if apps else 0,
            "top_score": round(max((a.ats_score for a in apps), default=0), 1),
        })
    return render_template("hr_dashboard.html", hr=hr, job_stats=job_stats)


@app.route("/hr/job/new", methods=["GET", "POST"])
def job_new():
    hr = current_hr()
    if not hr:
        return redirect(url_for("hr_login"))
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        required_experience = float(request.form.get("required_experience") or 0)

        from utils.parser import extract_skills
        req_skills = extract_skills(description)

        job = Job(title=title, description=description, required_experience=required_experience,
                   created_by=hr.id)
        job.required_skills = req_skills
        db.session.add(job)
        db.session.commit()
        flash(f"Job posted. Auto-detected {len(req_skills)} required skills.", "success")
        return redirect(url_for("hr_dashboard"))
    return render_template("job_new.html", hr=hr)


@app.route("/hr/job/<int:job_id>")
def job_detail(job_id):
    hr = current_hr()
    if not hr:
        return redirect(url_for("hr_login"))
    job = Job.query.get_or_404(job_id)
    apps = rank_candidates([
        {
            "id": a.id, "candidate": a.candidate, "ats_score": a.ats_score,
            "verdict": a.verdict, "status": a.status, "matched_skills": a.matched_skills,
            "missing_skills": a.missing_skills, "application": a
        } for a in job.applications
    ])
    return render_template("job_detail.html", hr=hr, job=job, applications=apps)


# ---------------------------------------------------------------- public job listing
@app.route("/jobs")
def jobs_list():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template("jobs.html", jobs=jobs)


# ---------------------------------------------------------------- candidate apply
@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
def apply(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        file = request.files.get("resume")

        if not file or file.filename == "" or not allowed_file(file.filename):
            flash("Please upload a valid resume file (PDF, DOCX, or TXT).", "error")
            return redirect(url_for("apply", job_id=job_id))

        fname = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        file.save(fpath)

        try:
            parsed = parse_resume(fpath)

            candidate = Candidate(
                name=name or parsed["name"],
                email=email or parsed["email"],
                phone=phone or parsed["phone"],
                resume_path=fpath,
                experience_years=parsed["experience_years"],
                raw_text=parsed["raw_text"],
            )
            candidate.skills = parsed["skills"]
            candidate.education = parsed["education"]
            db.session.add(candidate)
            db.session.commit()
        except Exception:
            app.logger.exception("Resume parsing failed")
            flash("We couldn't read that resume file. Please try a different PDF/DOCX/TXT.", "error")
            return redirect(url_for("apply", job_id=job_id))

        try:
            scores = compute_ats_score(
                resume_text=parsed["raw_text"], resume_skills=parsed["skills"],
                jd_text=job.description, jd_skills=job.required_skills,
                experience_years=parsed["experience_years"], required_experience=job.required_experience,
            )
            gap = skill_gap(parsed["skills"], job.required_skills)
            summary = summarize_resume(parsed["raw_text"], candidate.name)
            qs = generate_questions(gap["matched_skills"], role_title=job.title)
        except Exception:
            app.logger.exception("ATS scoring failed")
            flash("Something went wrong while scoring your resume. Please try again — "
                  "if this keeps happening, check the server console for the error.", "error")
            return redirect(url_for("apply", job_id=job_id))

        application = Application(
            job_id=job.id, candidate_id=candidate.id,
            ats_score=scores["ats_score"], semantic_score=scores["semantic_score"],
            keyword_score=scores["keyword_score"], experience_score=scores["experience_score"],
            verdict=scores["verdict"], summary=summary,
        )
        application.matched_skills = gap["matched_skills"]
        application.missing_skills = gap["missing_skills"]
        application.hr_questions = qs["hr"]
        application.technical_questions = qs["technical"]
        db.session.add(application)
        db.session.commit()

        return redirect(url_for("results", app_id=application.id))

    return render_template("apply.html", job=job)


@app.route("/results/<int:app_id>")
def results(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("results.html", application=application, job=application.job,
                            candidate=application.candidate)


# ---------------------------------------------------------------- voice mock interview
@app.route("/interview/<int:app_id>")
def interview(app_id):
    application = Application.query.get_or_404(app_id)
    questions = application.technical_questions + application.hr_questions
    return render_template("interview.html", application=application, questions=questions)


@app.route("/interview/<int:app_id>/submit", methods=["POST"])
def interview_submit(app_id):
    application = Application.query.get_or_404(app_id)
    data = request.get_json(force=True)
    answers = data.get("answers", [])  # list of {question, transcript}

    from utils.matcher import semantic_similarity
    scored = []
    total = 0
    for item in answers:
        transcript = (item.get("transcript") or "").strip()
        if not transcript:
            scored.append({"question": item["question"], "transcript": "", "score": 0})
            continue
        s = round(semantic_similarity(item["question"], transcript) * 100, 1)
        scored.append({"question": item["question"], "transcript": transcript, "score": s})
        total += s

    answered = sum(1 for a in scored if a["transcript"])
    avg_score = round(total / answered, 1) if answered else 0

    application.voice_eval = {"answered": answered, "total": len(scored), "avg_score": avg_score,
                                "details": scored}
    if avg_score >= 60 and application.ats_score >= 60:
        application.recommendation = "Recommended for next round"
    elif avg_score >= 40 or application.ats_score >= 45:
        application.recommendation = "Consider with reservations"
    else:
        application.recommendation = "Not recommended"
    db.session.commit()

    return jsonify({"ok": True, "avg_score": avg_score, "recommendation": application.recommendation})


# ---------------------------------------------------------------- scheduling
@app.route("/hr/schedule/<int:app_id>", methods=["POST"])
def schedule_interview(app_id):
    application = Application.query.get_or_404(app_id)
    when_str = request.form.get("datetime")  # "2026-07-20T14:30"
    try:
        dt = datetime.strptime(when_str, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        flash("Invalid date/time.", "error")
        return redirect(url_for("job_detail", job_id=application.job_id))

    application.interview_datetime = dt.strftime("%A, %d %B %Y — %I:%M %p")
    application.status = "Interview Scheduled"
    db.session.commit()

    sent = send_interview_email(application.candidate.email, application.candidate.name,
                                  application.job.title, application.interview_datetime)
    ics = generate_ics(application.candidate.name, application.job.title, dt)
    ics_path = os.path.join(REPORT_DIR, f"interview_{application.id}.ics")
    with open(ics_path, "w") as f:
        f.write(ics)

    flash(f"Interview scheduled. {'Email sent.' if sent else 'Email not configured — download the .ics invite instead.'}", "success")
    return redirect(url_for("job_detail", job_id=application.job_id))


@app.route("/hr/schedule/<int:app_id>/ics")
def download_ics(app_id):
    ics_path = os.path.join(REPORT_DIR, f"interview_{app_id}.ics")
    if not os.path.exists(ics_path):
        abort(404)
    return send_file(ics_path, as_attachment=True, download_name=f"interview_{app_id}.ics")


@app.route("/hr/status/<int:app_id>", methods=["POST"])
def update_status(app_id):
    application = Application.query.get_or_404(app_id)
    application.status = request.form.get("status", application.status)
    db.session.commit()
    return redirect(url_for("job_detail", job_id=application.job_id))


# ---------------------------------------------------------------- PDF report
@app.route("/report/<int:app_id>")
def download_report(app_id):
    application = Application.query.get_or_404(app_id)
    job = application.job
    candidate = application.candidate

    ranked = rank_candidates([{"id": a.id, "ats_score": a.ats_score} for a in job.applications])
    rank = next((r["rank"] for r in ranked if r["id"] == application.id), None)

    filepath = os.path.join(REPORT_DIR, f"report_{application.id}.pdf")
    generate_report(filepath, {
        "candidate_name": candidate.name, "email": candidate.email, "phone": candidate.phone,
        "job_title": job.title, "ats_score": application.ats_score,
        "semantic_score": application.semantic_score, "keyword_score": application.keyword_score,
        "experience_score": application.experience_score, "verdict": application.verdict,
        "matched_skills": application.matched_skills, "missing_skills": application.missing_skills,
        "rank": rank, "total_candidates": len(job.applications), "summary": application.summary,
        "hr_questions": application.hr_questions, "technical_questions": application.technical_questions,
        "voice_eval": application.voice_eval or None,
        "interview_datetime": application.interview_datetime or "Not yet scheduled",
        "recommendation": application.recommendation or application.verdict,
    })
    return send_file(filepath, as_attachment=True, download_name=f"{candidate.name}_report.pdf")


# ---------------------------------------------------------------- dashboard analytics API
@app.route("/api/job/<int:job_id>/analytics")
def job_analytics(job_id):
    job = Job.query.get_or_404(job_id)
    apps = job.applications
    return jsonify({
        "labels": [a.candidate.name for a in apps],
        "scores": [a.ats_score for a in apps],
        "verdicts": [a.verdict for a in apps],
        "skill_counts": _skill_frequency(apps),
    })


def _skill_frequency(apps):
    freq = {}
    for a in apps:
        for s in a.matched_skills:
            freq[s] = freq.get(s, 0) + 1
    return freq


with app.app_context():
    db.create_all()

# Pre-warm the Sentence-BERT model at startup instead of on the first upload.
# Loading a ~90MB model mid-request is the most common cause of the dev
# server appearing to "crash" / reset the connection on first submit —
# doing it here means any download/load error shows up clearly in the
# console at startup, and the first real user request is fast.
if os.environ.get("WERKZEUG_RUN_MAIN") != "true":  # skip in the reloader's watcher process
    print("Warming up Sentence-BERT model (first run downloads ~90MB from Hugging Face)...")
    try:
        from utils.matcher import get_model
        model = get_model()
        if model is not None:
            print("Sentence-BERT ready.")
        else:
            print("Sentence-BERT unavailable — falling back to TF-IDF similarity (check internet access).")
    except Exception as e:
        print(f"Model warmup failed ({e}). The app will fall back to TF-IDF similarity.")

if __name__ == "__main__":
    # debug/reloader off by default: the reloader can kill an in-flight
    # request (e.g. mid resume-parsing) if it detects a file change,
    # which looks exactly like a connection reset. Set FLASK_DEBUG=1 to
    # re-enable it for development.
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", 5000))  # Render (and most PaaS) inject PORT
    app.run(debug=debug_mode, host="0.0.0.0", port=port, threaded=True, use_reloader=debug_mode)
