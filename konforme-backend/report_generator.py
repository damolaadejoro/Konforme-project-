"""Server-side PDF report generation using ReportLab."""

import io
from datetime import date, datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from models import Account, AccountControl, BaseControl, RemediationTask, ScanResult

# Brand colors
NAVY = colors.HexColor("#0D1E3A")
CYAN = colors.HexColor("#25C2D3")
GREEN = colors.HexColor("#10B981")
RED = colors.HexColor("#DC2626")
AMBER = colors.HexColor("#D97706")
SLATE = colors.HexColor("#5A6478")
LIGHT_BORDER = colors.HexColor("#E2E8F0")


def _get_article_areas(db: Session, account_id: str) -> list[dict]:
    """Build Article 21(2) coverage summary from account controls."""
    AREA_NAMES = {
        "a": "Risk analysis & ISMS policies",
        "b": "Incident handling",
        "c": "Business continuity & crisis management",
        "d": "Supply chain security",
        "e": "Network & information systems security",
        "f": "Vulnerability handling & disclosure",
        "g": "Effectiveness assessment",
        "h": "Cyber hygiene & training",
        "i": "Cryptography & encryption",
        "j": "HR security & access control",
    }

    controls = (
        db.query(AccountControl)
        .filter(AccountControl.account_id == account_id)
        .all()
    )
    base_controls = {bc.control_id: bc for bc in db.query(BaseControl).all()}

    areas: dict[str, dict] = {}
    for letter, name in AREA_NAMES.items():
        areas[letter] = {"letter": letter, "name": name, "implemented": 0, "total": 0, "score": 0, "status": "Critical"}

    for ac in controls:
        bc = base_controls.get(ac.control_id)
        if not bc or not bc.article:
            continue
        letter = None
        if "(" in bc.article:
            parts = bc.article.split("(")
            for p in reversed(parts):
                p = p.rstrip(")")
                if len(p) == 1 and p.isalpha():
                    letter = p.lower()
                    break
        if letter and letter in areas:
            areas[letter]["total"] += 1
            if ac.status == "Implemented":
                areas[letter]["implemented"] += 1

    result = []
    for letter in sorted(areas.keys()):
        area = areas[letter]
        total = area["total"]
        impl = area["implemented"]
        pct = round((impl / total) * 100) if total > 0 else 0
        area["score"] = pct
        if pct >= 80:
            area["status"] = "Healthy"
        elif pct >= 40:
            area["status"] = "At Risk"
        else:
            area["status"] = "Critical"
        result.append(area)
    return result


def _get_open_findings(db: Session, account_id: str) -> list[dict]:
    """Get open scan findings (failed checks)."""
    from models import Scan

    scan = (
        db.query(Scan)
        .filter(Scan.account_id == account_id, Scan.status == "complete")
        .order_by(Scan.completed_at.desc())
        .first()
    )
    if not scan:
        return []

    results = (
        db.query(ScanResult)
        .filter(ScanResult.scan_id == scan.id, ScanResult.status == "fail")
        .all()
    )
    return [
        {
            "severity": (r.severity or "medium").capitalize(),
            "check_name": r.check_name or "",
            "article": r.article or "",
            "description": (r.description or "")[:120],
        }
        for r in results
    ]


def _get_open_remediation_tasks(db: Session, account_id: str) -> list[dict]:
    """Get open/in-progress remediation tasks."""
    tasks = (
        db.query(RemediationTask)
        .filter(
            RemediationTask.account_id == account_id,
            RemediationTask.status.in_(["open", "in_progress"]),
        )
        .order_by(RemediationTask.priority, RemediationTask.due_date)
        .limit(20)
        .all()
    )
    return [
        {
            "priority": (t.priority or "P2").upper(),
            "title": t.title,
            "assigned_to": t.assigned_to or "—",
            "due_date": t.due_date.isoformat() if t.due_date else "—",
        }
        for t in tasks
    ]


def _footer(canvas, doc, document_id: str, generated_short: str):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SLATE)
    canvas.drawCentredString(
        A4[0] / 2, 1.2 * cm,
        f"{document_id}  ·  Page {doc.page}  ·  Generated {generated_short}",
    )
    canvas.restoreState()


def generate_compliance_pdf(
    db: Session,
    account: Account,
    account_id: str,
    period: str,
    period_start: date,
    period_end: date,
    document_id: str,
    score_data: dict,
) -> bytes:
    """Generate a compliance PDF and return the raw bytes."""

    overall = score_data.get("overallScore") or 0
    tech = score_data.get("technicalScore") or 0
    human = score_data.get("humanFactorScore") or 0
    ctrl = score_data.get("controlsScore") or 0
    grade = score_data.get("grade") or "F"
    maturity = min(5, max(1, round(overall / 20))) if overall else 1

    w_tech = score_data.get("technicalWeight", 0.40)
    w_assess = score_data.get("assessmentWeight", 0.35)
    w_ctrl = score_data.get("controlsWeight", 0.25)

    now = datetime.now(timezone.utc)
    gen_long = now.strftime("%d %b %Y %H:%M UTC")
    gen_short = now.strftime("%Y-%m-%d")

    article_areas = _get_article_areas(db, account_id)
    findings = _get_open_findings(db, account_id)
    remediation_tasks = _get_open_remediation_tasks(db, account_id)

    # --- Styles ---
    styles = getSampleStyleSheet()
    s_title = ParagraphStyle("CoverTitle", parent=styles["Title"], fontSize=24, textColor=NAVY, spaceAfter=6)
    s_meta = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=10, textColor=SLATE)
    s_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=NAVY, spaceBefore=24, spaceAfter=8,
                           borderWidth=0, borderPadding=0)
    s_body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, textColor=NAVY)
    s_score_big = ParagraphStyle("ScoreBig", parent=styles["Normal"], fontSize=48, textColor=NAVY, leading=52)
    s_empty = ParagraphStyle("Empty", parent=styles["Normal"], fontSize=10, textColor=SLATE, fontName="Helvetica-Oblique")

    header_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), NAVY),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LIGHT_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])

    # --- Build story ---
    story = []

    # Cover page
    story.append(Spacer(1, 6 * cm))
    story.append(Paragraph("KONFORME", ParagraphStyle("Brand", parent=s_meta, fontSize=11, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("NIS2 Compliance Report", s_title))
    story.append(Paragraph(f"{account.name} — {period}", s_meta))
    story.append(Paragraph(f"Document ID: {document_id}", s_meta))
    story.append(Paragraph(f"Generated {gen_long}", s_meta))
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph(f"{overall:.1f}", s_score_big))

    grade_color = GREEN if grade in ("A", "B") else (AMBER if grade == "C" else RED)
    story.append(Paragraph(
        f'<font color="{grade_color.hexval()}">Grade {grade}</font>'
        f'&nbsp;&nbsp;&nbsp;<font color="{SLATE.hexval()}">Maturity Level {maturity}</font>',
        ParagraphStyle("GradeLine", parent=s_body, fontSize=12),
    ))
    story.append(PageBreak())

    # Score breakdown
    story.append(Paragraph("Score Breakdown", s_h2))
    score_data_table = [
        ["COMPONENT", "WEIGHT", "SCORE"],
        ["Technical", f"{w_tech * 100:.0f}%", f"{tech:.1f} / 100"],
        ["Assessment (Human Factor)", f"{w_assess * 100:.0f}%", f"{human:.1f} / 100"],
        ["Controls Implementation", f"{w_ctrl * 100:.0f}%", f"{ctrl:.1f} / 100"],
        ["Aggregate", "—", f"{overall:.1f} / 100"],
    ]
    t = Table(score_data_table, colWidths=[9 * cm, 3 * cm, 4 * cm])
    style = TableStyle(header_style.getCommands())
    style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
    style.add("LINEABOVE", (0, -1), (-1, -1), 1, NAVY)
    t.setStyle(style)
    story.append(t)

    # Article 21(2) coverage
    story.append(Paragraph("Article 21(2) Coverage", s_h2))
    if article_areas:
        rows = [["§", "AREA", "IMPL.", "TOTAL", "SCORE", "STATUS"]]
        for a in article_areas:
            status_color = GREEN if a["status"] == "Healthy" else (AMBER if a["status"] == "At Risk" else RED)
            rows.append([
                f'({a["letter"]})',
                a["name"],
                str(a["implemented"]),
                str(a["total"]),
                f'{a["score"]}%',
                Paragraph(f'<font color="{status_color.hexval()}">{a["status"]}</font>', s_body),
            ])
        t = Table(rows, colWidths=[1.2 * cm, 7 * cm, 1.5 * cm, 1.5 * cm, 1.8 * cm, 3 * cm])
        t.setStyle(header_style)
        story.append(t)
    else:
        story.append(Paragraph("No control coverage data available.", s_empty))

    # Open findings
    if findings:
        story.append(Paragraph("Open Findings", s_h2))
        rows = [["SEVERITY", "CHECK", "ARTICLE", "DESCRIPTION"]]
        for f in findings:
            sev = f["severity"]
            sev_color = RED if sev in ("Critical", "High") else (AMBER if sev == "Medium" else SLATE)
            rows.append([
                Paragraph(f'<font color="{sev_color.hexval()}">{sev}</font>', s_body),
                Paragraph(f["check_name"], s_body),
                f["article"],
                Paragraph(f["description"], s_body),
            ])
        t = Table(rows, colWidths=[2 * cm, 4.5 * cm, 2.5 * cm, 7 * cm])
        t.setStyle(header_style)
        story.append(t)

    # Remediation queue
    if remediation_tasks:
        story.append(Paragraph("Remediation Queue", s_h2))
        rows = [["PRIORITY", "TASK", "ASSIGNED TO", "DUE"]]
        for task in remediation_tasks:
            rows.append([task["priority"], Paragraph(task["title"], s_body), task["assigned_to"], task["due_date"]])
        t = Table(rows, colWidths=[2 * cm, 8 * cm, 3.5 * cm, 2.5 * cm])
        t.setStyle(header_style)
        story.append(t)

    # --- Build PDF ---
    buf = io.BytesIO()
    frame = Frame(1.8 * cm, 1.8 * cm, A4[0] - 3.6 * cm, A4[1] - 3.6 * cm, id="main")

    def _on_page(canvas, doc):
        _footer(canvas, doc, document_id, gen_short)

    page_tpl = PageTemplate(id="main", frames=[frame], onPage=_on_page)
    doc = BaseDocTemplate(buf, pagesize=A4, pageTemplates=[page_tpl],
                          title=f"{document_id} — NIS2 Compliance Report",
                          author="Konforme")
    doc.build(story)

    return buf.getvalue()
