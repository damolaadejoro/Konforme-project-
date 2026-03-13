import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from audit import log_scoring_config_changed
from auth import get_current_account
from database import get_db
from models import Account, AssessmentVersion, Scan
from schemas import ScoringConfig, ScoringConfigResponse, ScoringConfigUpdateResponse

router = APIRouter()

DEFAULT_SCORING_CONFIG = {"technical_weight": 0.6, "organizational_weight": 0.4}


def _get_scoring_config(account: Account) -> dict:
    if account.scoring_config:
        try:
            return json.loads(account.scoring_config)
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

    tw = config.get("technical_weight", 0.6)
    ow = config.get("organizational_weight", 0.4)

    overall = None
    if tech is not None and human is not None:
        overall = round(tech * tw + human * ow, 1)
    elif tech is not None:
        overall = tech
    elif human is not None:
        overall = human

    return overall, _grade(overall)


@router.get("/settings/scoring", response_model=ScoringConfigResponse)
def get_scoring_config(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    config = _get_scoring_config(account)
    return ScoringConfigResponse(
        technicalWeight=config.get("technical_weight", 0.6),
        organizationalWeight=config.get("organizational_weight", 0.4),
        domainWeights=config.get("domain_weights"),
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
        "organizational_weight": req.organizational_weight,
        "domain_weights": req.domain_weights,
        "preset": req.preset,
    }
    account.scoring_config = json.dumps(new_config)
    db.commit()
    db.refresh(account)

    log_scoring_config_changed(account.id, previous, new_config)

    overall, grade = _preview_score(account, new_config, db)

    return ScoringConfigUpdateResponse(
        technicalWeight=new_config["technical_weight"],
        organizationalWeight=new_config["organizational_weight"],
        domainWeights=new_config.get("domain_weights"),
        preset=new_config.get("preset"),
        previewOverallScore=overall,
        previewGrade=grade,
    )
