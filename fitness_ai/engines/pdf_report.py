import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

PRIMARY = colors.HexColor("#0EA5A0")
DARK = colors.HexColor("#101826")
ACCENT = colors.HexColor("#7C5CFC")
LIGHT_GREY = colors.HexColor("#F2F4F7")


def generate_progress_report(output_dir, user, profile, bmi, bmi_cat, calorie_target,
                              protein_target, diet_plan, weekly_plan_summary, progress_logs):
    os.makedirs(output_dir, exist_ok=True)
    filename = f"PulseFit_Report_{user.id}_{date.today().isoformat()}.pdf"
    path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=1.7 * cm, rightMargin=1.7 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], textColor=DARK, fontSize=22,
                                  spaceAfter=4)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=PRIMARY, fontSize=12,
                                     spaceAfter=14)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=DARK, fontSize=14, spaceBefore=14,
                         spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=15)

    story = []
    story.append(Paragraph("PulseFit AI &mdash; Progress Report", title_style))
    story.append(Paragraph(f"Prepared for {user.name} &nbsp;|&nbsp; {date.today().strftime('%d %B %Y')}", subtitle_style))
    story.append(HRFlowable(width="100%", color=PRIMARY, thickness=1.2))

    # Profile summary table
    story.append(Paragraph("Profile Summary", h2))
    profile_data = [
        ["Age", str(profile.age or "-"), "Gender", (profile.gender or "-").title()],
        ["Height", f"{profile.height_cm or '-'} cm", "Weight", f"{profile.weight_kg or '-'} kg"],
        ["BMI", f"{bmi or '-'} ({bmi_cat})", "Goal", (profile.goal or "-").replace("_", " ").title()],
        ["Daily Calories", f"{calorie_target or '-'} kcal", "Daily Protein", f"{protein_target or '-'} g"],
    ]
    t = Table(profile_data, colWidths=[3.3 * cm, 5 * cm, 3.3 * cm, 5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREY),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_GREY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9DEE7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    # Weekly workout plan
    story.append(Paragraph("This Week's Training Split", h2))
    plan_rows = [["Day", "Focus", "Exercises"]]
    for day, info in weekly_plan_summary.items():
        names = ", ".join(info["exercise_names"]) if info["exercise_names"] else "Rest & recovery"
        plan_rows.append([day, info["title"], names])
    t2 = Table(plan_rows, colWidths=[2.4 * cm, 5.2 * cm, 9 * cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9DEE7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
    ]))
    story.append(t2)

    # Diet plan
    story.append(Paragraph("Daily Diet Plan (Tamil Nadu Regional Meals)", h2))
    diet_rows = [["Meal", "Dish", "Calories", "Protein (g)"]]
    for slot, meals in diet_plan.items():
        for m in meals:
            diet_rows.append([slot.title(), m["title"], f"{m['calories']:.0f}", f"{m['protein']:.1f}"])
    t3 = Table(diet_rows, colWidths=[2.6 * cm, 8 * cm, 3 * cm, 3 * cm])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9DEE7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t3)

    # Progress history
    story.append(Paragraph("Recent Progress Log", h2))
    if progress_logs:
        rows = [["Date", "Workouts", "Weight (kg)", "Notes"]]
        for p in progress_logs:
            rows.append([p.log_date.isoformat(), str(p.workouts_completed or 0),
                         str(p.weight_kg or "-"), p.notes or "-"])
        t4 = Table(rows, colWidths=[3 * cm, 3 * cm, 3.5 * cm, 7 * cm])
        t4.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9DEE7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ]))
        story.append(t4)
    else:
        story.append(Paragraph("No progress logged yet &mdash; start tracking your workouts from the dashboard!", body))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=PRIMARY, thickness=1))
    story.append(Paragraph(
        "Generated by PulseFit AI &mdash; your personal AI gym assistant. Stay consistent, stay strong. 💪",
        ParagraphStyle("Footer", parent=body, textColor=colors.HexColor("#667085"), fontSize=9, spaceBefore=8)
    ))

    doc.build(story)
    return path
