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
from models import Account, AccountControl, AssessmentVersion, Country, CountryAssessmentQuestion, CountryControl, Scan, ScanResult
from scanner.nis2_mapping import NIS2_MAPPING
from schemas import (
    ArticleBreakdown,
    CombinedScoreResponse,
    GapResponse,
    ReportAction,
    ReportResponse,
)

router = APIRouter()

SEVERITY_WEIGHTS = {"critical": 4, "high": 3, "medium": 2, "low": 1}

# --- 3-pillar scoring constants ---

PILLAR_TECH_W = 0.40
PILLAR_ASSESS_W = 0.35
PILLAR_CONTROLS_W = 0.25

CONTROL_SEVERITY_MAP: dict[str, str] = {
    "ctrl-001": "critical",
    "ctrl-002": "critical",
    "ctrl-003": "high",
    "ctrl-004": "high",
    "ctrl-005": "critical",
    "ctrl-006": "high",
    "ctrl-007": "critical",
    "ctrl-008": "high",
    "ctrl-009": "critical",
    "ctrl-010": "critical",
    "ctrl-011": "critical",
    "ctrl-012": "critical",
    "ctrl-013": "high",
    "ctrl-014": "high",
    "ctrl-015": "high",
    "ctrl-016": "high",
    "ctrl-017": "critical",
    "ctrl-018": "high",
    "ctrl-019": "high",
    "ctrl-020": "high",
    "ctrl-021": "medium",
    "ctrl-022": "high",
    "ctrl-023": "critical",
    "ctrl-024": "high",
    "ctrl-025": "high",
    "ctrl-026": "critical",
    "ctrl-027": "high",
    "ctrl-028": "high",
}

CTRL_STATUS_WEIGHTS: dict[str, float] = {
    "Not Started": 0,
    "Planned": 0.25,
    "Partial": 0.5,
    "Implemented": 1.0,
}

CTRL_SEVERITY_WEIGHTS: dict[str, int] = {"critical": 3, "high": 2, "medium": 1}


def _get_account_weights(account: Account) -> tuple[float, float, float]:
    """Read 3-pillar weights from account.scoring_config, falling back to defaults."""
    if account.scoring_config:
        try:
            cfg = json.loads(account.scoring_config)
            if "assessment_weight" in cfg:
                return (
                    cfg.get("technical_weight", PILLAR_TECH_W),
                    cfg.get("assessment_weight", PILLAR_ASSESS_W),
                    cfg.get("controls_weight", PILLAR_CONTROLS_W),
                )
        except (json.JSONDecodeError, TypeError):
            pass
    return PILLAR_TECH_W, PILLAR_ASSESS_W, PILLAR_CONTROLS_W


def _compute_controls_score(db: Session, account_id: str, account: Account) -> float | None:
    """Compute a weighted controls implementation score (0-100) or None if no controls.

    Considers both the base 28 controls and any country-specific additional controls
    derived from the account's selected country.
    """
    rows = db.query(AccountControl).filter(AccountControl.account_id == account_id).all()
    saved_statuses: dict[str, str] = {r.control_id: r.status for r in rows}

    # Start with the base 28 controls — always present
    all_control_ids = list(CONTROL_SEVERITY_MAP.keys())

    # Add country-specific additional controls if the account has a country
    if account.country_id:
        country = db.query(Country).filter(Country.id == account.country_id).first()
        if country:
            additional_qs = (
                db.query(CountryAssessmentQuestion)
                .filter(
                    CountryAssessmentQuestion.country_id == account.country_id,
                    CountryAssessmentQuestion.is_additional.is_(True),
                )
                .all()
            )
            for i, _q in enumerate(additional_qs, 1):
                ctrl_id = f"country-ctrl-{country.code.lower()}-{i}"
                all_control_ids.append(ctrl_id)

    if not all_control_ids:
        return None

    weighted_sum = 0.0
    total_weight = 0.0
    for ctrl_id in all_control_ids:
        # Country-specific controls (not in the base map) default to "high"
        # to match frontend behaviour in useControls.ts
        severity = CONTROL_SEVERITY_MAP.get(ctrl_id, "high")
        sev_w = CTRL_SEVERITY_WEIGHTS.get(severity, 1)
        status = saved_statuses.get(ctrl_id, "Not Started")
        status_w = CTRL_STATUS_WEIGHTS.get(status, 0)
        weighted_sum += status_w * sev_w
        total_weight += sev_w

    if total_weight == 0:
        return None
    return round(weighted_sum / total_weight * 100, 1)


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


def _get_country_question_weights(account: Account, db: Session) -> dict[str, float] | None:
    """Query CountryAssessmentQuestion for the account's country, return {base_question_id: weight} or None."""
    if not account.country_id:
        return None
    rows = (
        db.query(CountryAssessmentQuestion)
        .filter(
            CountryAssessmentQuestion.country_id == account.country_id,
            CountryAssessmentQuestion.base_question_id.isnot(None),
        )
        .all()
    )
    if not rows:
        return None
    return {r.base_question_id: r.weight for r in rows}


def _get_latest_scan(
    db: Session,
    account_id: str,
    aws_account_id: str | None = None,
    credential_id: str | None = None,
) -> Scan | None:
    q = db.query(Scan).filter(Scan.account_id == account_id, Scan.status == "complete")
    if credential_id:
        q = q.filter(Scan.cloud_credential_id == credential_id)
    elif aws_account_id:
        q = q.filter(Scan.aws_account_id == aws_account_id)
    return q.order_by(Scan.completed_at.desc()).first()


def _get_latest_scans_per_provider(db: Session, account_id: str) -> list[Scan]:
    """Get the latest completed scan for each AWS account and cloud credential."""
    from sqlalchemy import func, and_

    scans: list[Scan] = []

    # Latest scan per AWS account
    aws_subq = (
        db.query(
            Scan.aws_account_id,
            func.max(Scan.completed_at).label("max_completed"),
        )
        .filter(
            Scan.account_id == account_id,
            Scan.status == "complete",
            Scan.aws_account_id.isnot(None),
        )
        .group_by(Scan.aws_account_id)
        .subquery()
    )
    aws_scans = (
        db.query(Scan)
        .join(
            aws_subq,
            and_(
                Scan.aws_account_id == aws_subq.c.aws_account_id,
                Scan.completed_at == aws_subq.c.max_completed,
            ),
        )
        .all()
    )
    scans.extend(aws_scans)

    # Latest scan per cloud credential (Azure etc.)
    cred_subq = (
        db.query(
            Scan.cloud_credential_id,
            func.max(Scan.completed_at).label("max_completed"),
        )
        .filter(
            Scan.account_id == account_id,
            Scan.status == "complete",
            Scan.cloud_credential_id.isnot(None),
            Scan.aws_account_id.is_(None),  # Exclude AWS scans that also have credential_id
        )
        .group_by(Scan.cloud_credential_id)
        .subquery()
    )
    cred_scans = (
        db.query(Scan)
        .join(
            cred_subq,
            and_(
                Scan.cloud_credential_id == cred_subq.c.cloud_credential_id,
                Scan.completed_at == cred_subq.c.max_completed,
            ),
        )
        .all()
    )
    # Avoid duplicates
    seen_ids = {s.id for s in scans}
    for s in cred_scans:
        if s.id not in seen_ids:
            scans.append(s)

    return scans


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


def _article_breakdown_from_assessment(
    assessment: AssessmentVersion,
    weight_overrides: dict[str, float] | None = None,
) -> dict[str, float]:
    """Calculate per-article scores from V2 maturity responses."""
    score_inputs = [
        {"question_id": r.question_id, "maturity_level": r.maturity_level}
        for r in assessment.responses
    ]
    scores = calculate_assessment_score(score_inputs, weight_overrides=weight_overrides)
    return {a["article"]: a["score"] for a in scores["article_scores"] if a["score"] > 0}


def _build_score_response(
    db: Session,
    account: Account,
    scans: list[Scan],
    assessment: AssessmentVersion | None,
    controls_score: float | None,
    country_weights: dict[str, float] | None,
) -> CombinedScoreResponse:
    """Build a CombinedScoreResponse from one or more scans + optional assessment + controls."""

    # Read user-configured weights (or defaults)
    w_tech, w_assess, w_controls = _get_account_weights(account)

    # Aggregate technical score across all scans (weighted average by check count)
    tech_score: float | None = None
    last_scan_time: str | None = None
    all_scan_results: list[ScanResult] = []

    if scans:
        total_weighted = 0.0
        total_checks = 0
        latest_completed = None
        for scan in scans:
            if scan.overall_score is not None and scan.total_checks > 0:
                total_weighted += scan.overall_score * scan.total_checks
                total_checks += scan.total_checks
            results = db.query(ScanResult).filter(ScanResult.scan_id == scan.id).all()
            all_scan_results.extend(results)
            if scan.completed_at and (latest_completed is None or scan.completed_at > latest_completed):
                latest_completed = scan.completed_at

        if total_checks > 0:
            tech_score = round(total_weighted / total_checks, 1)
        last_scan_time = latest_completed.isoformat() if latest_completed else None

    human_score = assessment.overall_score if assessment else None

    # 3-pillar proportional weighting using user-configured weights
    pillars: list[tuple[float, float]] = []
    if tech_score is not None and tech_score > 0:
        pillars.append((tech_score, w_tech))
    if human_score is not None and human_score > 0:
        pillars.append((human_score, w_assess))
    if controls_score is not None and controls_score > 0:
        pillars.append((controls_score, w_controls))
    total_w = sum(w for _, w in pillars)
    overall = round(sum(s * w for s, w in pillars) / total_w) if total_w > 0 else None

    # Build per-article breakdown from all scan results
    all_articles: dict[str, dict] = {}

    if all_scan_results:
        tech_breakdown = _article_breakdown_from_scan(all_scan_results)
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
        human_breakdown = _article_breakdown_from_assessment(assessment, country_weights)
        for article, h_score in human_breakdown.items():
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

    for data in all_articles.values():
        t = data["technicalScore"]
        h = data["humanScore"]
        if t is not None and h is not None:
            data["combinedScore"] = round(t * w_tech + h * w_assess, 1)
        elif t is not None:
            data["combinedScore"] = t
        elif h is not None:
            data["combinedScore"] = h

    return CombinedScoreResponse(
        overallScore=overall,
        technicalScore=tech_score,
        humanFactorScore=human_score,
        controlsScore=controls_score,
        lastTechnicalScan=last_scan_time,
        lastHumanAssessment=assessment.submitted_at.isoformat() if assessment else None,
        technicalWeight=w_tech,
        humanWeight=w_assess,
        assessmentWeight=w_assess,
        controlsWeight=w_controls,
        grade=_grade(overall),
        articleBreakdown=[ArticleBreakdown(**d) for d in all_articles.values()],
    )


@router.get("/score/{account_id}", response_model=CombinedScoreResponse)
def get_combined_score(
    account_id: str,
    aws_account_id: str | None = Query(None),
    credential_id: str | None = Query(None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    country_weights = _get_country_question_weights(account, db)
    assessment = _get_latest_assessment(db, account_id)
    controls_score = _compute_controls_score(db, account_id, account)

    if aws_account_id or credential_id:
        # Single provider/account filter — return score for just that one
        scan = _get_latest_scan(db, account_id, aws_account_id, credential_id)
        scans = [scan] if scan else []
    else:
        # Aggregate across ALL providers: latest scan per AWS account + per credential
        scans = _get_latest_scans_per_provider(db, account_id)

    return _build_score_response(db, account, scans, assessment, controls_score, country_weights)


@router.get("/report/{account_id}", response_model=ReportResponse)
def get_report(
    account_id: str,
    aws_account_id: str | None = Query(None),
    credential_id: str | None = Query(None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    if aws_account_id or credential_id:
        scan = _get_latest_scan(db, account_id, aws_account_id, credential_id)
    else:
        # For reports, use the latest single scan (aggregation is in score endpoint)
        scan = _get_latest_scan(db, account_id)
    assessment = _get_latest_assessment(db, account_id)
    controls_score = _compute_controls_score(db, account_id, account)

    tech_score = scan.overall_score if scan else None
    human_score = assessment.overall_score if assessment else None

    # 3-pillar proportional weighting using user-configured weights
    w_tech, w_assess, w_controls = _get_account_weights(account)
    pillars: list[tuple[float, float]] = []
    if tech_score is not None and tech_score > 0:
        pillars.append((tech_score, w_tech))
    if human_score is not None and human_score > 0:
        pillars.append((human_score, w_assess))
    if controls_score is not None and controls_score > 0:
        pillars.append((controls_score, w_controls))
    total_w = sum(w for _, w in pillars)
    overall = round(sum(s * w for s, w in pillars) / total_w) if total_w > 0 else None

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
