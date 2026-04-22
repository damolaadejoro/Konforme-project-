"""Question-control mapping endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import AssessmentQuestionControl
from schemas import QuestionControlMappingResponse

router = APIRouter()


@router.get("/mappings/question-controls", response_model=list[QuestionControlMappingResponse])
def get_all_mappings(db: Session = Depends(get_db)):
    """Get all question-to-control mappings."""
    rows = db.query(AssessmentQuestionControl).all()
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
    rows = db.query(AssessmentQuestionControl).filter(
        AssessmentQuestionControl.question_id == question_id,
    ).all()
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
    rows = db.query(AssessmentQuestionControl).filter(
        AssessmentQuestionControl.control_id == control_id,
    ).all()
    return [
        QuestionControlMappingResponse(
            questionId=r.question_id,
            controlId=r.control_id,
            weight=r.weight,
        )
        for r in rows
    ]
