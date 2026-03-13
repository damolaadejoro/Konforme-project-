import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_account
from database import get_db
from models import Account, Country, CountryAssessmentQuestion, CountryControl, CountryDeadline, EntityTier
from schemas import (
    CountryAssessmentQuestionResponse,
    CountryControlResponse,
    CountryDeadlineResponse,
    CountryListItem,
    CountryResponse,
    EntityTierResponse,
    SetCountryRequest,
)

router = APIRouter()


def _parse_json(text: str, fallback=None):
    """Safely parse a JSON text field."""
    if not text:
        return fallback if fallback is not None else []
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return fallback if fallback is not None else []


def _get_country_or_404(code: str, db: Session) -> Country:
    country = db.query(Country).filter(Country.code == code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail=f"Country not found: {code}")
    return country


@router.get("/countries", response_model=list[CountryListItem])
def list_countries(db: Session = Depends(get_db)):
    """List all countries with transposition status."""
    countries = db.query(Country).order_by(Country.name).all()
    return [
        CountryListItem(
            code=c.code,
            name=c.name,
            nameLocal=c.name_local,
            transpositionStatus=c.transposition_status,
            transpositionLawName=c.transposition_law_name,
            dateEffective=str(c.date_effective) if c.date_effective else None,
            competentAuthorityName=c.competent_authority_name,
            researchConfidence=c.research_confidence,
        )
        for c in countries
    ]


@router.get("/countries/{code}", response_model=CountryResponse)
def get_country(code: str, db: Session = Depends(get_db)):
    """Get full country detail."""
    c = _get_country_or_404(code, db)
    return CountryResponse(
        code=c.code,
        name=c.name,
        nameLocal=c.name_local,
        transpositionStatus=c.transposition_status,
        transpositionLawName=c.transposition_law_name,
        transpositionLawReference=c.transposition_law_reference,
        transpositionLawUrl=c.transposition_law_url,
        datePublished=str(c.date_published) if c.date_published else None,
        dateEffective=str(c.date_effective) if c.date_effective else None,
        competentAuthorityName=c.competent_authority_name,
        competentAuthorityUrl=c.competent_authority_url,
        csirtName=c.csirt_name,
        csirtUrl=c.csirt_url,
        researchConfidence=c.research_confidence,
        researchNotes=c.research_notes,
    )


@router.get("/countries/{code}/tiers", response_model=list[EntityTierResponse])
def get_country_tiers(code: str, db: Session = Depends(get_db)):
    """Get entity tiers for a country."""
    country = _get_country_or_404(code, db)
    tiers = db.query(EntityTier).filter(EntityTier.country_id == country.id).all()
    return [
        EntityTierResponse(
            id=t.id,
            tierKey=t.tier_key,
            localName=t.local_name,
            description=t.description,
            sectors=_parse_json(t.sectors, []),
            sizeThresholds=_parse_json(t.size_thresholds, {}),
            obligations=_parse_json(t.obligations, {}),
            penalties=_parse_json(t.penalties, {}),
        )
        for t in tiers
    ]


@router.get("/countries/{code}/controls", response_model=list[CountryControlResponse])
def get_country_controls(code: str, db: Session = Depends(get_db)):
    """Get country-specific controls."""
    country = _get_country_or_404(code, db)
    controls = db.query(CountryControl).filter(CountryControl.country_id == country.id).all()
    return [
        CountryControlResponse(
            id=cc.id,
            controlId=cc.control_id,
            euArticle=cc.eu_article,
            nationalLegalReference=cc.national_legal_reference,
            nationalSpecification=cc.national_specification,
            goesBeyondEu=cc.goes_beyond_eu,
            appliesToTiers=_parse_json(cc.applies_to_tiers, []),
            additionalRequirements=_parse_json(cc.additional_requirements, []),
            isMandatory=cc.is_mandatory,
        )
        for cc in controls
    ]


@router.get("/countries/{code}/deadlines", response_model=list[CountryDeadlineResponse])
def get_country_deadlines(code: str, db: Session = Depends(get_db)):
    """Get country deadlines."""
    country = _get_country_or_404(code, db)
    deadlines = (
        db.query(CountryDeadline)
        .filter(CountryDeadline.country_id == country.id)
        .order_by(CountryDeadline.deadline_date)
        .all()
    )
    return [
        CountryDeadlineResponse(
            id=d.id,
            deadlineDate=str(d.deadline_date),
            description=d.description,
            appliesToTiers=_parse_json(d.applies_to_tiers, []),
            legalReference=d.legal_reference,
        )
        for d in deadlines
    ]


@router.get("/countries/{code}/assessment", response_model=list[CountryAssessmentQuestionResponse])
def get_country_assessment_questions(code: str, db: Session = Depends(get_db)):
    """Get country-specific assessment questions."""
    country = _get_country_or_404(code, db)
    questions = (
        db.query(CountryAssessmentQuestion)
        .filter(CountryAssessmentQuestion.country_id == country.id)
        .all()
    )
    return [
        CountryAssessmentQuestionResponse(
            id=q.id,
            baseQuestionId=q.base_question_id,
            questionText=q.question_text,
            helpText=q.help_text,
            euArticle=q.eu_article,
            nationalLegalReference=q.national_legal_reference,
            appliesToTiers=_parse_json(q.applies_to_tiers, []),
            domain=q.domain,
            weight=q.weight,
            isAdditional=q.is_additional,
        )
        for q in questions
    ]


@router.put("/accounts/country")
def set_account_country(
    req: SetCountryRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Set the account's country and entity tier for compliance purposes."""
    country = _get_country_or_404(req.country_code, db)

    account.country_id = country.id
    account.country = country.code  # Keep the ISO code in sync

    if req.entity_tier:
        tier = (
            db.query(EntityTier)
            .filter(EntityTier.country_id == country.id, EntityTier.tier_key == req.entity_tier)
            .first()
        )
        if not tier:
            valid_tiers = [
                t.tier_key
                for t in db.query(EntityTier).filter(EntityTier.country_id == country.id).all()
            ]
            raise HTTPException(
                status_code=422,
                detail=f"Invalid entity tier '{req.entity_tier}' for {country.code}. Valid: {valid_tiers}",
            )
        account.entity_tier_id = tier.id
    else:
        account.entity_tier_id = None

    db.commit()
    db.refresh(account)

    return {
        "account_id": account.id,
        "country_code": country.code,
        "country_name": country.name,
        "entity_tier": req.entity_tier,
    }
