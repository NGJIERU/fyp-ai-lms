"""
API endpoints for AI Personal Tutor
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from app import models
from app.api import deps
from app.core.database import get_db
from app.services.tutor import get_ai_tutor

router = APIRouter()


# Enums
class QuestionTypeEnum(str, Enum):
    mcq = "mcq"
    short_text = "short_text"
    python_code = "python_code"
    step_by_step = "step_by_step"


class GradingModeEnum(str, Enum):
    practice = "practice"
    graded = "graded"


class DifficultyEnum(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


# Request/Response schemas
class ExplainRequest(BaseModel):
    topic: str = Field(..., description="Topic to explain")
    question: Optional[str] = Field(None, description="Specific question about the topic")
    week_number: Optional[int] = Field(None, ge=1, le=14)


class ExplainResponse(BaseModel):
    explanation: str
    topic: str
    sources: List[Dict[str, str]]
    course_id: int
    week_number: Optional[int]


class CheckAnswerRequest(BaseModel):
    question_type: QuestionTypeEnum
    question: Dict[str, Any] = Field(..., description="Question data with correct answer")
    student_answer: str
    mode: GradingModeEnum = GradingModeEnum.practice
    course_id: int = Field(..., description="ID of the course")
    week_number: int = Field(..., description="Week number for the topic")


class CheckAnswerResponse(BaseModel):
    score: float
    max_score: float
    is_correct: bool
    feedback: str
    hints: Optional[List[str]] = None
    explanation: Optional[str] = None
    model_answer: Optional[str] = None
    correct_answer: Optional[str] = None


class HintRequest(BaseModel):
    problem: str = Field(..., description="The problem statement")
    student_attempt: str = Field(..., description="Student's current attempt")
    week_number: Optional[int] = Field(None, ge=1, le=14)


class HintResponse(BaseModel):
    hint: str
    problem: str
    relevant_topics: List[str]


class GenerateQuestionsRequest(BaseModel):
    week_number: int = Field(..., ge=1, le=14)
    num_questions: int = Field(5, ge=1, le=20)
    difficulty: DifficultyEnum = DifficultyEnum.medium


class GenerateQuestionsResponse(BaseModel):
    topic: str
    week_number: int
    difficulty: str
    questions: List[Dict[str, Any]]
    sources: List[str]


class SummarizeResponse(BaseModel):
    summary: str
    material_id: int
    material_title: str
    original_length: int
    summary_length: int


class WeakTopicItem(BaseModel):
    topic: str
    week_number: int
    score: float
    attempts: int


class WeakTopicsResponse(BaseModel):
    student_id: int
    course_id: int
    weak_topics: List[WeakTopicItem]
    recommendations: List[str]


class RevisionSuggestion(BaseModel):
    topic: str
    priority: str
    estimated_time: str
    materials: List[Dict[str, str]]


class RevisionResponse(BaseModel):
    student_id: int
    course_id: int
    priority_topics: List[str]
    suggestions: List[RevisionSuggestion]
    total_estimated_time: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    week_number: Optional[int] = Field(None, ge=1, le=14)
    conversation_history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, str]]
    suggested_topics: Optional[List[str]] = None


# Endpoints
@router.post("/explain", response_model=ExplainResponse)
def explain_concept(
    course_id: int,
    request: ExplainRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get an AI-generated explanation of a concept.
    Uses lecturer-approved materials as the knowledge base.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    tutor = get_ai_tutor()
    result = tutor.explain_concept(
        db=db,
        course_id=course_id,
        topic=request.topic,
        question=request.question,
        week_number=request.week_number
    )
    
    return ExplainResponse(**result)


@router.post("/check-answer", response_model=CheckAnswerResponse)
def check_answer(
    request: CheckAnswerRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Check a student's answer and provide feedback.
    
    In practice mode: Full solutions and explanations are shown.
    In graded mode: Only hints are provided, no full solutions.
    """
    tutor = get_ai_tutor()
    result = tutor.check_answer(
        db=db,
        student_id=current_user.id,
        course_id=request.course_id,
        week_number=request.week_number,
        question_type=request.question_type.value,
        question=request.question,
        student_answer=request.student_answer,
        mode=request.mode.value
    )
    
    return CheckAnswerResponse(
        score=result.get("score", 0),
        max_score=result.get("max_score", 1),
        is_correct=result.get("is_correct", False),
        feedback=result.get("feedback", ""),
        hints=result.get("hints"),
        explanation=result.get("explanation"),
        model_answer=result.get("model_answer"),
        correct_answer=result.get("correct_answer")
    )


@router.post("/hint", response_model=HintResponse)
def get_hint(
    course_id: int,
    request: HintRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get a hint for a problem without revealing the full answer.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    tutor = get_ai_tutor()
    result = tutor.provide_hint(
        db=db,
        course_id=course_id,
        problem=request.problem,
        student_attempt=request.student_attempt,
        week_number=request.week_number
    )
    
    return HintResponse(**result)


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
def generate_practice_questions(
    course_id: int,
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Generate practice questions for a specific topic.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    tutor = get_ai_tutor()
    result = tutor.generate_practice_questions(
        db=db,
        course_id=course_id,
        week_number=request.week_number,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return GenerateQuestionsResponse(**result)


@router.get("/summarize/{material_id}", response_model=SummarizeResponse)
def summarize_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get an AI-generated summary of a learning material.
    """
    tutor = get_ai_tutor()
    result = tutor.summarize_material(db=db, material_id=material_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return SummarizeResponse(**result)


@router.get("/weak-topics", response_model=WeakTopicsResponse)
def get_weak_topics(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get weak topics for the current student.
    Based on quiz/assignment performance analysis.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    tutor = get_ai_tutor()
    result = tutor.detect_weak_topics(
        db=db,
        student_id=current_user.id,
        course_id=course_id
    )
    
    return WeakTopicsResponse(
        student_id=current_user.id,
        course_id=course_id,
        weak_topics=[WeakTopicItem(**t) for t in result.get("weak_topics", [])],
        recommendations=result.get("recommendations", [])
    )


@router.get("/revision-suggestions", response_model=RevisionResponse)
def get_revision_suggestions(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get personalized revision suggestions based on weak topics.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    tutor = get_ai_tutor()
    result = tutor.get_revision_suggestions(
        db=db,
        student_id=current_user.id,
        course_id=course_id
    )
    
    return RevisionResponse(
        student_id=current_user.id,
        course_id=course_id,
        priority_topics=result.get("priority_topics", []),
        suggestions=[],  # Would be populated from actual data
        total_estimated_time=result.get("estimated_study_time", "Unknown")
    )


@router.post("/chat", response_model=ChatResponse)
def chat_with_tutor(
    course_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Have a conversation with the AI tutor.
    The tutor uses course materials as context.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    tutor = get_ai_tutor()
    
    # Convert Pydantic models to dicts for the service
    history = None
    if request.conversation_history:
        history = [msg.dict() for msg in request.conversation_history]
    
    result = tutor.chat(
        db=db,
        course_id=course_id,
        message=request.message,
        conversation_history=history,
        week_number=request.week_number
    )
    
    return ChatResponse(
        response=result.get("response", "I couldn't generate a response."),
        sources=result.get("sources", []),
        suggested_topics=result.get("suggested_topics", [])
    )


# MCQ-specific endpoints
class MCQQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    topic: Optional[str] = None


class MCQSubmission(BaseModel):
    question_id: int
    selected_answer: str


class MCQResult(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: Optional[str]
    score: int


@router.post("/mcq/check", response_model=MCQResult)
def check_mcq_answer(
    question_id: int,
    submission: MCQSubmission,
    mode: GradingModeEnum = GradingModeEnum.practice,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Quick endpoint for checking MCQ answers.
    """
    # In a real implementation, you would fetch the question from DB
    # For now, this is a simplified version
    
    tutor = get_ai_tutor()
    
    # Mock question data - in production, fetch from database
    mock_question = {
        "question": "Sample question",
        "correct_answer": "A",
        "explanation": "This is the explanation."
    }
    
    result = tutor.check_answer(
        question_type="mcq",
        question=mock_question,
        student_answer=submission.selected_answer,
        mode=mode.value
    )
    
    return MCQResult(
        question_id=question_id,
        is_correct=result.get("is_correct", False),
        correct_answer=result.get("correct_answer", "") if mode == GradingModeEnum.practice else "",
        explanation=result.get("explanation") if mode == GradingModeEnum.practice else None,
        score=result.get("score", 0)
    )


@router.get("/practice/history", response_model=List[Dict[str, Any]])
def get_practice_history(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get practice history for a student in a course.
    """
    from app.models.performance import QuizAttempt
    
    attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.student_id == current_user.id,
            QuizAttempt.course_id == course_id
        )
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(50)
        .all()
    )
    
    return [
        {
            "id": a.id,
            "week_number": a.week_number,
            "score": a.score,
            "max_score": a.max_score,
            "is_correct": a.is_correct,
            "attempted_at": a.attempted_at,
            "question_type": a.question_type,
            "question_preview": a.question_data.get("question") if a.question_data else "Question"
        }
        for a in attempts
    ]


# Code execution endpoint
class CodeExecutionRequest(BaseModel):
    code: str
    function_name: str = "solution"
    test_cases: List[Dict[str, Any]]


class CodeExecutionResponse(BaseModel):
    passed: int
    total: int
    results: List[Dict[str, Any]]
    feedback: str


@router.post("/code/execute", response_model=CodeExecutionResponse)
def execute_code(
    request: CodeExecutionRequest,
    mode: GradingModeEnum = GradingModeEnum.practice,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Execute Python code against test cases.
    """
    tutor = get_ai_tutor()
    
    question = {
        "function_name": request.function_name,
        "test_cases": request.test_cases
    }
    
    result = tutor.check_answer(
        question_type="python_code",
        question=question,
        student_answer=request.code,
        mode=mode.value
    )
    
    return CodeExecutionResponse(
        passed=result.get("tests_passed", 0),
        total=result.get("tests_total", len(request.test_cases)),
        results=result.get("test_results", []) if mode == GradingModeEnum.practice else [],
        feedback=result.get("feedback", "")
    )
