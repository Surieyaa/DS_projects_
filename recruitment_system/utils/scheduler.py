"""
Interview Scheduling — Email + Calendar
------------------------------------------
Generates a downloadable .ics calendar invite (works with Google
Calendar, Outlook, Apple Calendar — no OAuth needed) and optionally
sends an email notification via SMTP if credentials are configured
as environment variables:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

If SMTP isn't configured, send_interview_email() simply returns
False and the caller can still hand the candidate the .ics file.
"""
import os
import smtplib
import uuid
from email.mime.text import MIMEText
from datetime import datetime, timedelta


def generate_ics(candidate_name: str, job_title: str, start_dt: datetime, duration_minutes: int = 45) -> str:
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    uid = str(uuid.uuid4())
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Smart Recruitment System//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:Interview — {job_title} ({candidate_name})
DESCRIPTION:Interview scheduled via AI Smart Recruitment System.
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""
    return ics


def send_interview_email(to_email: str, candidate_name: str, job_title: str, when_str: str) -> bool:
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT", 587)
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")

    if not all([host, user, password, to_email]):
        return False

    body = (
        f"Hi {candidate_name},\n\n"
        f"Your interview for the {job_title} role has been scheduled for {when_str}.\n"
        f"Please be ready 5 minutes early.\n\n"
        f"Best,\nRecruitment Team"
    )
    msg = MIMEText(body)
    msg["Subject"] = f"Interview Scheduled — {job_title}"
    msg["From"] = user
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, int(port)) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_email], msg.as_string())
        return True
    except Exception:
        return False
