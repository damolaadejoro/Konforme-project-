import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from assessment_questions import (
    ARTICLES,
    QUESTION_MAP,
    QUESTIONS_BY_ARTICLE,
    RECOMMENDATIONS,
    SEVERITY_WEIGHTS as ASSESSMENT_SEVERITY_WEIGHTS,
    calculate_assessment_score,
)
from auth import enforce_account_access, get_current_account
from database import get_db
from models import Account, AssessmentVersion, Scan, ScanResult
from scanner.nis2_mapping import NIS2_MAPPING
from schemas import (
    ArticleBreakdown,
    CombinedScoreResponse,
    GapResponse,
    ReportAction,
    ReportResponse,
)

router = APIRouter()

TECHNICAL_WEIGHT = 0.60
HUMAN_WEIGHT = 0.40

SEVERITY_WEIGHTS = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _grade(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _get_latest_scan(db: Session, account_id: str, aws_account_id: str | None = None) -> Scan | None:
    q = db.query(Scan).filter(Scan.account_id == account_id, Scan.status == "complete")
    if aws_account_id:
        q = q.filter(Scan.aws_account_id == aws_account_id)
    return q.order_by(Scan.completed_at.desc()).first()


def _get_latest_assessment(db: Session, account_id: str) -> AssessmentVersion | None:
    return (
        db.query(AssessmentVersion)
        .filter(
            AssessmentVersion.account_id == account_id,
            AssessmentVersion.status == "submitted",
        )
        .order_by(AssessmentVersion.submitted_at.desc())
        .first()
    )


def _article_breakdown_from_scan(results: list[ScanResult]) -> dict[str, dict]:
    articles: dict[str, dict] = {}
    for r in results:
        if r.status in ("warn", "info"):
            continue
        mapping = NIS2_MAPPING.get(r.check_id, {})
        article = r.nis2_article or mapping.get("article", "Unknown")
        title = mapping.get("article_title", "")
        if article not in articles:
            articles[article] = {"article": article, "articleTitle": title, "pass_w": 0.0, "total_w": 0.0}
        w = SEVERITY_WEIGHTS.get(r.severity, 1)
        articles[article]["total_w"] += w
        if r.status == "pass":
            articles[article]["pass_w"] += w
    return articles


def _article_breakdown_from_assessment(assessment: AssessmentVersion) -> dict[str, float]:
    """Calculate per-article scores from V2 maturity responses."""
    score_inputs = [
        {"question_id": r.question_id, "maturity_level": r.maturity_level}
        for r in assessment.responses
    ]
    scores = calculate_assessment_score(score_inputs)
    return {a["article"]: a["score"] for a in scores["article_scores"] if a["score"] > 0}


@router.get("/score/{account_id}", response_model=CombinedScoreResponse)
def get_combined_score(
    account_id: str,
    aws_account_id: str | None = Query(None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    scan = _get_latest_scan(db, account_id, aws_account_id)
    assessment = _get_latest_assessment(db, account_id)

    tech_score = scan.overall_score if scan else None
    human_score = assessment.overall_score if assessment else None

    overall = None
    if tech_score is not None and human_score is not None:
        overall = round(tech_score * TECHNICAL_WEIGHT + human_score * HUMAN_WEIGHT, 1)
    elif tech_score is not None:
        overall = tech_score
    elif human_score is not None:
        overall = human_score

    # Build per-article breakdown
    all_articles: dict[str, dict] = {}

    if scan:
        scan_results = db.query(ScanResult).filter(ScanResult.scan_id == scan.id).all()
        tech_breakdown = _article_breakdown_from_scan(scan_results)
        for article, data in tech_breakdown.items():
            t_score = round((data["pass_w"] / data["total_w"]) * 100, 1) if data["total_w"] > 0 else None
            all_articles[article] = {
                "article": article,
                "articleTitle": data["articleTitle"],
                "technicalScore": t_score,
                "humanScore": None,
                "combinedScore": None,
            }

    if assessment:
        human_breakdown = _article_breakdown_from_assessment(assessment)
        for article, h_score in human_breakdown.items():
            # Find article title
            art_title = ""
            for art_def in ARTICLES:
                if art_def["article"] == article:
                    art_title = art_def["title"]
                    break

            if article not in all_articles:
                all_articles[article] = {
                    "article": article,
                    "articleTitle": art_title,
                    "technicalScore": None,
                    "humanScore": h_score,
                    "combinedScore": None,
                }
            else:
                all_articles[article]["humanScore"] = h_score

    # Compute combined per-article
    for data in all_articles.values():
        t = data["technicalScore"]
        h = data["humanScore"]
        if t is not None and h is not None:
            data["combinedScore"] = round(t * TECHNICAL_WEIGHT + h * HUMAN_WEIGHT, 1)
        elif t is not None:
            data["combinedScore"] = t
        elif h is not None:
            data["combinedScore"] = h

    return CombinedScoreResponse(
        overallScore=overall,
        technicalScore=tech_score,
        humanFactorScore=human_score,
        lastTechnicalScan=scan.completed_at.isoformat() if scan and scan.completed_at else None,
        lastHumanAssessment=assessment.submitted_at.isoformat() if assessment else None,
        technicalWeight=TECHNICAL_WEIGHT,
        humanWeight=HUMAN_WEIGHT,
        grade=_grade(overall),
        articleBreakdown=[ArticleBreakdown(**d) for d in all_articles.values()],
    )


@router.get("/report/{account_id}", response_model=ReportResponse)
def get_report(
    account_id: str,
    aws_account_id: str | None = Query(None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    scan = _get_latest_scan(db, account_id, aws_account_id)
    assessment = _get_latest_assessment(db, account_id)

    tech_score = scan.overall_score if scan else None
    human_score = assessment.overall_score if assessment else None
    overall = None
    if tech_score is not None and human_score is not None:
        overall = round(tech_score * TECHNICAL_WEIGHT + human_score * HUMAN_WEIGHT, 1)
    elif tech_score is not None:
        overall = tech_score
    elif human_score is not None:
        overall = human_score

    critical_actions: list[ReportAction] = []
    warnings: list[ReportAction] = []
    passing_count = 0
    total_checks = 0

    if scan:
        results = db.query(ScanResult).filter(ScanResult.scan_id == scan.id).all()
        total_checks = len(results)
        for r in results:
            if r.status == "pass":
                passing_count += 1
            elif r.status == "fail":
                action = ReportAction(
                    checkId=r.check_id,
                    title=r.title,
                    severity=r.severity,
                    article=r.nis2_article,
                    remediation=r.remediation,
                    resource=r.resource,
                )
                if r.severity in ("critical", "high"):
                    critical_actions.append(action)
                else:
                    warnings.append(action)

    # Build human gaps from V2 maturity assessment
    human_gaps: list[GapResponse] = []
    if assessment:
        for resp in assessment.responses:
            if resp.maturity_level is None:
                continue  # N/A
            if resp.maturity_level <= 2:
                q = QUESTION_MAP.get(resp.question_id)
                if not q:
                    continue
                maturity_labels = {0: "Not Addressed", 1: "Aware", 2: "Ad-hoc"}
                human_gaps.append(
                    GapResponse(
                        questionId=q["id"],
                        question=q["question"],
                        category=q["article"],
                        article=q["article"],
                        severity=q["severity"],
                        response=f"Level {resp.maturity_level}: {maturity_labels.get(resp.maturity_level, '')}",
                        recommendation=RECOMMENDATIONS.get(q["id"], ""),
                    )
                )

    return ReportResponse(
        accountId=account.id,
        accountName=account.name,
        generatedAt=datetime.now(timezone.utc).isoformat(),
        overallScore=overall,
        grade=_grade(overall),
        criticalActions=critical_actions,
        warnings=warnings,
        humanGaps=human_gaps,
        passingCount=passing_count,
        totalChecks=total_checks,
    )
