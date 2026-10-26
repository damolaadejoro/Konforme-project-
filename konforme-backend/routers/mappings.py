"""Question-control mapping endpoints."""

from fastapi import APIRouter, Depends
from database import Session, get_db
from models import AssessmentQuestionControl
from schemas import QuestionControlMappingResponse

router = APIRouter()


@router.get("/mappings/question-controls", response_model=list[QuestionControlMappingResponse])
def get_all_mappings(db: Session = Depends(get_db)):
    """Get all question-to-control mappings."""
    rows = db.all(AssessmentQuestionControl)
    return [
        QuestionControlMappingResponse(
            questionId=r.question_id,
            controlId=r.control_id,
            weight=r.weight,
        )
        for r in rows
    ]


@router.get("/mappings/question/{question_id}/controls", response_model=list[QuestionControlMappingResponse])
def get_controls_for_question(question_id: str, db: Session = Depends(get_db)):
    """Get controls mapped to a specific assessment question."""
    rows = [r for r in db.all(AssessmentQuestionControl) if r.question_id == question_id]
    return [
        QuestionControlMappingResponse(
            questionId=r.question_id,
            controlId=r.control_id,
            weight=r.weight,
        )
        for r in rows
    ]


@router.get("/mappings/control/{control_id}/questions", response_model=list[QuestionControlMappingResponse])
def get_questions_for_control(control_id: str, db: Session = Depends(get_db)):
    """Get assessment questions mapped to a specific control."""
    rows = [r for r in db.all(AssessmentQuestionControl) if r.control_id == control_id]
    return [
        QuestionControlMappingResponse(
            questionId=r.question_id,
            controlId=r.control_id,
            weight=r.weight,
        )
        for r in rows
    ]
