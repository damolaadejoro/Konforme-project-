import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from audit import log_scoring_config_changed
from auth import get_current_account
from database import get_db
from models import Account, AccountControl, AssessmentVersion, Country, CountryAssessmentQuestion, Scan
from schemas import ScoringConfig, ScoringConfigResponse, ScoringConfigUpdateResponse

router = APIRouter()

DEFAULT_SCORING_CONFIG = {
    "technical_weight": 0.40,
    "assessment_weight": 0.35,
    "controls_weight": 0.25,
    "preset": "balanced",
}


def _get_scoring_config(account: Account) -> dict:
    if account.scoring_config:
        try:
            cfg = json.loads(account.scoring_config)
            # Migrate old 2-pillar configs
            if "organizational_weight" in cfg and "assessment_weight" not in cfg:
                cfg = DEFAULT_SCORING_CONFIG.copy()
            return cfg
        except (json.JSONDecodeError, TypeError):
            pass
    return DEFAULT_SCORING_CONFIG.copy()


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


def _compute_controls_score_for_preview(account: Account, db: Session) -> float | None:
    """Lightweight controls score for preview — mirrors score.py logic."""
    from routers.score import CONTROL_SEVERITY_MAP, CTRL_STATUS_WEIGHTS, CTRL_SEVERITY_WEIGHTS

    rows = db.query(AccountControl).filter(AccountControl.account_id == account.id).all()
    saved_statuses: dict[str, str] = {r.control_id: r.status for r in rows}

    all_control_ids = list(CONTROL_SEVERITY_MAP.keys())
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
                all_control_ids.append(f"country-ctrl-{country.code.lower()}-{i}")

    if not all_control_ids:
        return None

    weighted_sum = 0.0
    total_weight = 0.0
    for ctrl_id in all_control_ids:
        severity = CONTROL_SEVERITY_MAP.get(ctrl_id, "high")
        sev_w = CTRL_SEVERITY_WEIGHTS.get(severity, 1)
        status = saved_statuses.get(ctrl_id, "Not Started")
        status_w = CTRL_STATUS_WEIGHTS.get(status, 0)
        weighted_sum += status_w * sev_w
        total_weight += sev_w

    if total_weight == 0:
        return None
    return round(weighted_sum / total_weight * 100, 1)


def _preview_score(account: Account, config: dict, db: Session) -> tuple[float | None, str | None]:
    """Compute what the overall score would be with the given config."""
    scan = (
        db.query(Scan)
        .filter(Scan.account_id == account.id, Scan.status == "complete")
        .order_by(Scan.completed_at.desc())
        .first()
    )
    assessment = (
        db.query(AssessmentVersion)
        .filter(AssessmentVersion.account_id == account.id, AssessmentVersion.status == "submitted")
        .order_by(AssessmentVersion.submitted_at.desc())
        .first()
    )

    tech = scan.overall_score if scan else None
    human = assessment.overall_score if assessment else None
    controls = _compute_controls_score_for_preview(account, db)

    tw = config.get("technical_weight", 0.40)
    aw = config.get("assessment_weight", 0.35)
    cw = config.get("controls_weight", 0.25)

    pillars: list[tuple[float, float]] = []
    if tech is not None and tech > 0:
        pillars.append((tech, tw))
    if human is not None and human > 0:
        pillars.append((human, aw))
    if controls is not None and controls > 0:
        pillars.append((controls, cw))

    total_w = sum(w for _, w in pillars)
    overall = round(sum(s * w for s, w in pillars) / total_w) if total_w > 0 else None

    return overall, _grade(overall)


@router.get("/settings/scoring", response_model=ScoringConfigResponse)
def get_scoring_config(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    config = _get_scoring_config(account)
    return ScoringConfigResponse(
        technicalWeight=config.get("technical_weight", 0.40),
        assessmentWeight=config.get("assessment_weight", 0.35),
        controlsWeight=config.get("controls_weight", 0.25),
        preset=config.get("preset"),
    )


@router.put("/settings/scoring", response_model=ScoringConfigUpdateResponse)
def update_scoring_config(
    req: ScoringConfig,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    previous = _get_scoring_config(account)

    new_config = {
        "technical_weight": req.technical_weight,
        "assessment_weight": req.assessment_weight,
        "controls_weight": req.controls_weight,
        "preset": req.preset,
    }
    account.scoring_config = json.dumps(new_config)
    db.commit()
    db.refresh(account)

    log_scoring_config_changed(account.id, previous, new_config)

    overall, grade = _preview_score(account, new_config, db)

    return ScoringConfigUpdateResponse(
        technicalWeight=new_config["technical_weight"],
        assessmentWeight=new_config["assessment_weight"],
        controlsWeight=new_config["controls_weight"],
        preset=new_config.get("preset"),
        previewOverallScore=overall,
        previewGrade=grade,
    )
