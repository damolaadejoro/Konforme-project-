import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from assessment_questions import (
    ARTICLES,
    QUESTION_IDS,
    QUESTION_MAP,
    QUESTIONS,
    QUESTIONS_BY_ARTICLE,
    RECOMMENDATIONS,
    RESPONSE_SCORES,
    calculate_assessment_score,
    calculate_human_score,
)
from auth import enforce_account_access, get_current_account
from database import get_db
from models import Account, Assessment, AssessmentResponse, AssessmentVersion
from schemas import (
    ArticleScoreOut,
    AssessmentCompareResponse,
    AssessmentDetailResponse,
    AssessmentDetailResponseV2,
    AssessmentHistoryResponse,
    AssessmentResponse as AssessmentResponseSchema,
    AssessmentSubmitRequest,
    AssessmentSubmitRequestV2,
    AssessmentVersionResponse,
    AssessmentVersionSummary,
    GapResponse,
    MaturityResponseItem,
    QuestionDelta,
    QuestionOut,
    QuestionOutV2,
)

router = APIRouter()


# --- Legacy V1 endpoints (kept for backwards compatibility) ---


def _build_gaps(responses: list[dict]) -> list[GapResponse]:
    gaps = []
    for resp in responses:
        q = QUESTION_MAP.get(resp["question_id"])
        if not q:
            continue
        if resp["response"] in ("no", "partial"):
            gaps.append(
                GapResponse(
                    questionId=q["id"],
                    question=q["question"],
                    category=q.get("category", q["article"]),
                    article=q["article"],
                    severity=q["severity"],
                    response=resp["response"],
                    recommendation=RECOMMENDATIONS.get(q["id"], ""),
                )
            )
    return gaps


@router.post("/assessment/{account_id}", response_model=AssessmentResponseSchema)
def submit_assessment(
    account_id: str,
    req: AssessmentSubmitRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    submitted_ids = {r.question_id for r in req.responses}
    missing = QUESTION_IDS - submitted_ids
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing questions: {sorted(missing)}",
        )

    responses_raw = [{"question_id": r.question_id, "response": r.response, "notes": r.notes} for r in req.responses]
    score = calculate_human_score(responses_raw)

    assessment = Assessment(
        account_id=account_id,
        human_score=score,
        responses=json.dumps(responses_raw),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    gaps = _build_gaps(responses_raw)

    return AssessmentResponseSchema(
        id=assessment.id,
        completedAt=assessment.submitted_at.isoformat(),
        score=score,
        totalQuestions=len(QUESTIONS),
        answered=len(req.responses),
        gaps=gaps,
    )


@router.get("/assessment/{account_id}", response_model=AssessmentDetailResponseV2)
def get_assessment(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    # Try V2 first
    latest_v2 = (
        db.query(AssessmentVersion)
        .filter(AssessmentVersion.account_id == account_id)
        .order_by(AssessmentVersion.submitted_at.desc())
        .first()
    )

    questions = [
        QuestionOutV2(
            id=q["id"],
            article=q["article"],
            articleTitle=q["articleTitle"],
            severity=q["severity"],
            question=q["question"],
            description=q["description"],
            guidance=q.get("guidance", ""),
        )
        for q in QUESTIONS
    ]

    empty_articles = [
        ArticleScoreOut(article=a["article"], title=a["title"], score=0, answered=0, total=len(QUESTIONS_BY_ARTICLE.get(a["article"], [])))
        for a in ARTICLES
    ]

    if not latest_v2:
        return AssessmentDetailResponseV2(assessment=None, questions=questions, articles=empty_articles)

    # Build response from V2 data
    resp_items = []
    score_inputs = []
    for r in latest_v2.responses:
        resp_items.append(MaturityResponseItem(
            question_id=r.question_id,
            maturity_level=r.maturity_level,
            notes=r.notes,
            evidence_refs=json.loads(r.evidence_refs) if r.evidence_refs else [],
        ))
        score_inputs.append({"question_id": r.question_id, "maturity_level": r.maturity_level})

    scores = calculate_assessment_score(score_inputs)
    article_scores = [
        ArticleScoreOut(article=a["article"], title=a["title"], score=a["score"], answered=a["answered"], total=a["total"])
        for a in scores["article_scores"]
    ]

    return AssessmentDetailResponseV2(
        assessment=AssessmentVersionResponse(
            id=latest_v2.id,
            version=latest_v2.version,
            submittedAt=latest_v2.submitted_at.isoformat(),
            overallScore=latest_v2.overall_score,
            status=latest_v2.status,
            articleScores=article_scores,
            responses=resp_items,
        ),
        questions=questions,
        articles=article_scores,
    )


# --- V2 endpoints ---


@router.post("/assessment/{account_id}/v2", response_model=AssessmentVersionResponse)
def submit_assessment_v2(
    account_id: str,
    req: AssessmentSubmitRequestV2,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    # Validate question IDs
    submitted_ids = {r.question_id for r in req.responses}
    missing = QUESTION_IDS - submitted_ids
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing questions: {sorted(missing)}")

    # Calculate version number
    latest = (
        db.query(AssessmentVersion)
        .filter(AssessmentVersion.account_id == account_id)
        .order_by(AssessmentVersion.version.desc())
        .first()
    )
    next_version = (latest.version + 1) if latest else 1

    # Calculate score
    score_inputs = [{"question_id": r.question_id, "maturity_level": r.maturity_level} for r in req.responses]
    scores = calculate_assessment_score(score_inputs)

    # Create version
    version = AssessmentVersion(
        account_id=account_id,
        version=next_version,
        overall_score=scores["overall_score"],
        status="submitted",
    )
    db.add(version)
    db.flush()

    # Create responses
    for r in req.responses:
        db.add(AssessmentResponse(
            assessment_version_id=version.id,
            question_id=r.question_id,
            maturity_level=r.maturity_level,
            notes=r.notes,
            evidence_refs=json.dumps(r.evidence_refs),
        ))

    db.commit()
    db.refresh(version)

    resp_items = [
        MaturityResponseItem(
            question_id=r.question_id,
            maturity_level=r.maturity_level,
            notes=r.notes,
            evidence_refs=r.evidence_refs,
        )
        for r in req.responses
    ]

    article_scores = [
        ArticleScoreOut(article=a["article"], title=a["title"], score=a["score"], answered=a["answered"], total=a["total"])
        for a in scores["article_scores"]
    ]

    return AssessmentVersionResponse(
        id=version.id,
        version=version.version,
        submittedAt=version.submitted_at.isoformat(),
        overallScore=version.overall_score,
        status=version.status,
        articleScores=article_scores,
        responses=resp_items,
    )


@router.get("/assessment/{account_id}/history", response_model=AssessmentHistoryResponse)
def get_assessment_history(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    versions = (
        db.query(AssessmentVersion)
        .filter(AssessmentVersion.account_id == account_id)
        .order_by(AssessmentVersion.version.desc())
        .all()
    )

    summaries = []
    for v in versions:
        score = v.overall_score
        # Compute score on-the-fly for drafts that have responses
        if score is None and v.responses:
            score_inputs = [
                {"question_id": r.question_id, "maturity_level": r.maturity_level}
                for r in v.responses
            ]
            scores = calculate_assessment_score(score_inputs)
            score = scores["overall_score"]
        summaries.append(
            AssessmentVersionSummary(
                id=v.id,
                version=v.version,
                submittedAt=v.submitted_at.isoformat(),
                overallScore=score,
                status=v.status,
            )
        )

    return AssessmentHistoryResponse(versions=summaries)


@router.get("/assessment/{account_id}/version/{version_id}", response_model=AssessmentVersionResponse)
def get_assessment_version(
    account_id: str,
    version_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    version = (
        db.query(AssessmentVersion)
        .filter(AssessmentVersion.id == version_id, AssessmentVersion.account_id == account_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Assessment version not found")

    resp_items = []
    score_inputs = []
    for r in version.responses:
        resp_items.append(MaturityResponseItem(
            question_id=r.question_id,
            maturity_level=r.maturity_level,
            notes=r.notes,
            evidence_refs=json.loads(r.evidence_refs) if r.evidence_refs else [],
        ))
        score_inputs.append({"question_id": r.question_id, "maturity_level": r.maturity_level})

    scores = calculate_assessment_score(score_inputs)
    article_scores = [
        ArticleScoreOut(article=a["article"], title=a["title"], score=a["score"], answered=a["answered"], total=a["total"])
        for a in scores["article_scores"]
    ]

    return AssessmentVersionResponse(
        id=version.id,
        version=version.version,
        submittedAt=version.submitted_at.isoformat(),
        overallScore=version.overall_score,
        status=version.status,
        articleScores=article_scores,
        responses=resp_items,
    )


@router.patch("/assessment/{account_id}/response/{question_id}")
def auto_save_response(
    account_id: str,
    question_id: str,
    req: MaturityResponseItem,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    if question_id not in QUESTION_IDS:
        raise HTTPException(status_code=404, detail=f"Unknown question: {question_id}")

    # Find or create draft version
    draft = (
        db.query(AssessmentVersion)
        .filter(
            AssessmentVersion.account_id == account_id,
            AssessmentVersion.status == "draft",
        )
        .first()
    )

    if not draft:
        latest = (
            db.query(AssessmentVersion)
            .filter(AssessmentVersion.account_id == account_id)
            .order_by(AssessmentVersion.version.desc())
            .first()
        )
        next_version = (latest.version + 1) if latest else 1
        draft = AssessmentVersion(
            account_id=account_id,
            version=next_version,
            status="draft",
        )
        db.add(draft)
        db.flush()

    # Update or create response
    existing = (
        db.query(AssessmentResponse)
        .filter(
            AssessmentResponse.assessment_version_id == draft.id,
            AssessmentResponse.question_id == question_id,
        )
        .first()
    )

    if existing:
        existing.maturity_level = req.maturity_level
        existing.notes = req.notes
        existing.evidence_refs = json.dumps(req.evidence_refs)
    else:
        db.add(AssessmentResponse(
            assessment_version_id=draft.id,
            question_id=question_id,
            maturity_level=req.maturity_level,
            notes=req.notes,
            evidence_refs=json.dumps(req.evidence_refs),
        ))

    db.commit()
    return {"status": "saved", "versionId": draft.id}
