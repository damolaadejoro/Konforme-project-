"""Reports archive — server-side PDF generation, storage, and download."""

import io
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from auth import enforce_account_access, get_current_account, get_current_user
from database import get_db
from models import Account, Report, User
from report_generator import generate_compliance_pdf
from report_storage import store_pdf, load_pdf, delete_pdf
from schemas import ReportArchiveResponse, ReportGenerateRequest

router = APIRouter()


def _report_to_response(r: Report) -> ReportArchiveResponse:
    return ReportArchiveResponse(
        id=r.id,
        documentId=r.document_id,
        period=r.period,
        periodStart=r.period_start.isoformat() if r.period_start else "",
        periodEnd=r.period_end.isoformat() if r.period_end else "",
        aggregateScore=r.aggregate_score,
        technicalScore=r.technical_score,
        humanFactorScore=r.human_factor_score,
        grade=r.grade,
        maturityLevel=r.maturity_level,
        fileSizeBytes=r.file_size_bytes,
        contentHash=r.content_hash,
        generatedAt=r.generated_at.isoformat() if r.generated_at else "",
        generatedByUserId=r.generated_by_user_id,
        downloadUrl=f"/api/v1/reports/{r.account_id}/{r.id}/download",
    )


@router.get("/reports/{account_id}", response_model=list[ReportArchiveResponse])
def list_reports(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    reports = (
        db.query(Report)
        .filter(Report.account_id == account_id)
        .order_by(desc(Report.generated_at))
        .all()
    )
    return [_report_to_response(r) for r in reports]


@router.post("/reports/{account_id}/generate", response_model=ReportArchiveResponse, status_code=201)
def generate_report(
    account_id: str,
    request: ReportGenerateRequest,
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    # Parse dates
    try:
        p_start = date.fromisoformat(request.period_start)
        p_end = date.fromisoformat(request.period_end)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")

    # Build document ID: KNF-{YYYY}-{QN}-{seq}
    seq = db.query(Report).filter(Report.account_id == account_id).count() + 1
    now = datetime.now(timezone.utc)
    document_id = f"KNF-{now.year}-{request.period.replace(' ', '-').upper()}-{seq:03d}"

    # Snapshot current scores
    from routers.score import (
        _build_score_response,
        _compute_controls_score,
        _get_country_question_weights,
        _get_latest_assessment,
        _get_latest_scans_per_provider,
        _get_severity_map,
    )

    country_weights = _get_country_question_weights(account, db)
    assessment = _get_latest_assessment(db, account_id)
    severity_map = _get_severity_map(db)
    controls_score = _compute_controls_score(db, account_id, account, severity_map)
    scans = _get_latest_scans_per_provider(db, account_id)
    score_resp = _build_score_response(db, account, scans, assessment, controls_score, country_weights)

    score_data = {
        "overallScore": score_resp.overallScore or 0,
        "technicalScore": score_resp.technicalScore or 0,
        "humanFactorScore": score_resp.humanFactorScore or 0,
        "controlsScore": score_resp.controlsScore or 0,
        "grade": score_resp.grade or "F",
        "technicalWeight": score_resp.technicalWeight,
        "assessmentWeight": score_resp.assessmentWeight,
        "controlsWeight": score_resp.controlsWeight,
    }

    overall = score_data["overallScore"]
    maturity = min(5, max(1, round(overall / 20))) if overall else 1

    # Generate PDF
    pdf_bytes = generate_compliance_pdf(
        db=db,
        account=account,
        account_id=account_id,
        period=request.period,
        period_start=p_start,
        period_end=p_end,
        document_id=document_id,
        score_data=score_data,
    )

    # Create the report row
    report = Report(
        account_id=account_id,
        document_id=document_id,
        period=request.period,
        period_start=p_start,
        period_end=p_end,
        aggregate_score=overall,
        technical_score=score_data["technicalScore"],
        human_factor_score=score_data["humanFactorScore"],
        grade=score_data["grade"],
        maturity_level=maturity,
        file_size_bytes=0,
        file_path=None,
        content_hash=None,
        generated_by_user_id=user.id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Store PDF and update metadata
    relative_path, size, content_hash = store_pdf(account_id, report.id, pdf_bytes)
    report.file_path = relative_path
    report.file_size_bytes = size
    report.content_hash = content_hash
    db.commit()
    db.refresh(report)

    return _report_to_response(report)


@router.get("/reports/{account_id}/{report_id}/download")
def download_report(
    account_id: str,
    report_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    report = db.query(Report).filter(
        Report.id == report_id,
        Report.account_id == account_id,
    ).first()
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        pdf_bytes = load_pdf(report.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{report.document_id}.pdf"',
            "Content-Length": str(report.file_size_bytes),
        },
    )


@router.delete("/reports/{account_id}/{report_id}", status_code=204)
def delete_report(
    account_id: str,
    report_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    report = db.query(Report).filter(
        Report.id == report_id,
        Report.account_id == account_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.file_path:
        delete_pdf(report.file_path)
    db.delete(report)
    db.commit()
