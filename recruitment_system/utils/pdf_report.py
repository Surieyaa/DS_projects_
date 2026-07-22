"""
Final Candidate Performance PDF Report
----------------------------------------
Generates a professional PDF summarizing: candidate info, resume
analysis, ATS score, skill gap, ranking, HR/technical questions,
voice-interview evaluation, recruiter notes, interview schedule and
final recommendation.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

NAVY = colors.HexColor("#131A3A")
INDIGO = colors.HexColor("#4C5FD5")
GOLD = colors.HexColor("#E4A93B")
LIGHT_GREY = colors.HexColor("#F3F4F8")
TEXT_GREY = colors.HexColor("#454B63")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="TitleBig", fontSize=22, leading=26, textColor=NAVY,
                           fontName="Helvetica-Bold", spaceAfter=4))
    ss.add(ParagraphStyle(name="SubTitle", fontSize=11, leading=14, textColor=TEXT_GREY,
                           fontName="Helvetica"))
    ss.add(ParagraphStyle(name="Section", fontSize=13, leading=16, textColor=INDIGO,
                           fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=6))
    ss.add(ParagraphStyle(name="Body", fontSize=10, leading=15, textColor=TEXT_GREY,
                           fontName="Helvetica", alignment=TA_LEFT))
    ss.add(ParagraphStyle(name="ScoreNum", fontSize=34, leading=38, textColor=INDIGO,
                           fontName="Helvetica-Bold", alignment=TA_CENTER))
    ss.add(ParagraphStyle(name="ScoreLabel", fontSize=9, leading=11, textColor=TEXT_GREY,
                           fontName="Helvetica", alignment=TA_CENTER))
    return ss


def generate_report(filepath: str, data: dict):
    """
    data keys expected:
      candidate_name, email, phone, job_title, ats_score, semantic_score,
      keyword_score, experience_score, verdict, matched_skills,
      missing_skills, rank, total_candidates, summary, hr_questions,
      technical_questions, voice_eval (dict or None), interview_datetime,
      recommendation
    """
    styles = _styles()
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                             topMargin=18 * mm, bottomMargin=16 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    story = []

    story.append(Paragraph("Candidate Performance Report", styles["TitleBig"]))
    story.append(Paragraph(f"AI Smart Recruitment System &nbsp;|&nbsp; Position: {data.get('job_title', 'N/A')}",
                            styles["SubTitle"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GREY))
    story.append(Spacer(1, 10))

    # Candidate info + score row
    info_table = Table([
        [Paragraph(f"<b>{data.get('candidate_name','N/A')}</b>", styles["Body"]),
         Paragraph(str(data.get('ats_score', 0)), styles["ScoreNum"])],
        [Paragraph(f"{data.get('email','—')}<br/>{data.get('phone','—')}", styles["Body"]),
         Paragraph("ATS SCORE / 100", styles["ScoreLabel"])],
        [Paragraph(f"Rank #{data.get('rank','—')} of {data.get('total_candidates','—')} candidates<br/>"
                    f"Verdict: <b>{data.get('verdict','—')}</b>", styles["Body"]), ""],
    ], colWidths=[120 * mm, 50 * mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (1, 1), (1, 2)),
        ("BACKGROUND", (1, 0), (1, 2), LIGHT_GREY),
        ("BOX", (1, 0), (1, 2), 0.5, LIGHT_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)

    # Sub-score breakdown
    story.append(Paragraph("Resume & ATS Analysis", styles["Section"]))
    sub_scores = Table([
        ["Semantic Match (Sentence-BERT)", "Keyword / Skill Match", "Experience Match"],
        [f"{data.get('semantic_score',0)}%", f"{data.get('keyword_score',0)}%", f"{data.get('experience_score',0)}%"],
    ], colWidths=[57 * mm, 57 * mm, 56 * mm])
    sub_scores.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
    ]))
    story.append(sub_scores)

    # Skill gap
    story.append(Paragraph("Skill Gap Analysis", styles["Section"]))
    matched = ", ".join(data.get("matched_skills", [])) or "None found"
    missing = ", ".join(data.get("missing_skills", [])) or "None — full match"
    story.append(Paragraph(f"<b>Matched skills:</b> {matched}", styles["Body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Missing / gap skills:</b> {missing}", styles["Body"]))

    # Summary
    story.append(Paragraph("AI Resume Summary", styles["Section"]))
    story.append(Paragraph(data.get("summary", "—"), styles["Body"]))

    # Interview questions
    story.append(Paragraph("AI-Generated HR Questions", styles["Section"]))
    for q in data.get("hr_questions", []):
        story.append(Paragraph(f"• {q}", styles["Body"]))

    story.append(Paragraph("AI-Generated Technical Questions", styles["Section"]))
    for q in data.get("technical_questions", []):
        story.append(Paragraph(f"• {q}", styles["Body"]))

    # Voice interview evaluation
    voice_eval = data.get("voice_eval")
    if voice_eval:
        story.append(Paragraph("Voice Mock Interview Evaluation", styles["Section"]))
        story.append(Paragraph(
            f"Questions answered: {voice_eval.get('answered', 0)} / {voice_eval.get('total', 0)} &nbsp;|&nbsp; "
            f"Avg. relevance score: {voice_eval.get('avg_score', 0)}%", styles["Body"]))

    # Schedule + recommendation
    story.append(Paragraph("Interview Schedule", styles["Section"]))
    story.append(Paragraph(data.get("interview_datetime", "Not yet scheduled"), styles["Body"]))

    story.append(Paragraph("Final Recommendation", styles["Section"]))
    story.append(Paragraph(f"<b>{data.get('recommendation', '—')}</b>", styles["Body"]))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GREY))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Generated by AI Smart Recruitment System — BERT & LLM powered.",
                            styles["ScoreLabel"]))

    doc.build(story)
    return filepath
