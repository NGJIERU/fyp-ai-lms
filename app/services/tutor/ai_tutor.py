"""
AI Personal Tutor - Main tutor service
Provides explanations, feedback, weak topic detection, and personalized learning
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.course import Course
from app.models.syllabus import Syllabus
from app.services.tutor.rag_pipeline import RAGPipeline, ContextBuilder
from app.services.tutor.answer_checker import AnswerChecker, QuestionType, GradingMode
from app.services.processing.embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class AITutor:
    """
    AI Personal Tutor service.
    Provides concept explanations, answer checking, weak topic detection,
    and personalized revision suggestions.
    """
    
    # System prompts for different tutor modes
    PROMPTS = {
        "explain": """You are an expert tutor explaining concepts to a university student.
Your task is to explain the following topic clearly and thoroughly.

Guidelines:
- Use simple language first, then introduce technical terms
- Provide concrete examples
- Break down complex concepts into smaller parts
- Use analogies when helpful
- Reference the provided course materials

Topic to explain: {topic}

Course Materials Context:
{context}

Student's specific question (if any): {question}

Provide a clear, educational explanation:""",

        "check_understanding": """You are an AI tutor checking a student's understanding.
Analyze their response and provide constructive feedback.

Topic: {topic}
Student's explanation/answer: {student_response}

Course Materials Context:
{context}

Evaluate:
1. Accuracy of their understanding
2. Completeness of their explanation
3. Any misconceptions

Provide feedback that is encouraging but identifies areas for improvement:""",

        "hint": """You are an AI tutor providing hints without giving away the answer.
The student is working on a problem and needs guidance.

Problem: {problem}
Student's current attempt: {attempt}

Course Materials Context:
{context}

Provide a helpful hint that:
1. Points them in the right direction
2. Does NOT reveal the answer
3. Encourages independent thinking
4. References relevant concepts from the materials

Hint:""",

        "summarize": """You are an AI tutor summarizing educational content.
Create a concise but comprehensive summary of the following material.

Material to summarize:
{content}

Create a summary that:
1. Captures the key concepts
2. Highlights important definitions
3. Notes any formulas or procedures
4. Is suitable for exam revision

Summary:""",

        "generate_questions": """You are an AI tutor generating practice questions.
Based on the following topic and materials, generate practice questions.

Topic: {topic}
Difficulty level: {difficulty}

Course Materials Context:
{context}

Generate {num_questions} practice questions that:
1. Test understanding of key concepts
2. Include a mix of question types (conceptual, application, analysis)
3. Are appropriate for the specified difficulty level
4. Have clear, unambiguous answers

Questions:"""
    }
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: Optional[str] = None,
        use_openai: Optional[bool] = None,
        rag_pipeline: Optional[RAGPipeline] = None
    ):
        """
        Initialize the AI Tutor.
        
        Args:
            openai_api_key: OpenAI API key
            model: LLM model to use
            use_openai: Force enable/disable OpenAI usage
            rag_pipeline: Injected RAG pipeline (mainly for testing)
        """
        self.use_openai = settings.USE_OPENAI_TUTOR if use_openai is None else use_openai
        if self.use_openai:
            self.api_key = openai_api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        else:
            self.api_key = None

        self.model = model or settings.AI_TUTOR_MODEL
        self.rag_pipeline = rag_pipeline or RAGPipeline(
            embedding_service=get_embedding_service(
                model_name=settings.EMBEDDING_MODEL_NAME,
                use_openai=settings.USE_OPENAI_EMBEDDINGS,
                openai_api_key=settings.OPENAI_API_KEY
            )
        )
        self.answer_checker = AnswerChecker()
        self.llm_client = None
        
        if self.use_openai and self.api_key:
            self._init_llm_client()
        else:
            logger.info("AI Tutor running in mock mode (OpenAI disabled or missing API key)")
    
    def _init_llm_client(self):
        """Initialize the LLM client."""
        try:
            from openai import OpenAI
            self.llm_client = OpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAI client with model {self.model}")
        except ImportError:
            logger.warning("OpenAI package not installed")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
    
    def explain_concept(
        self,
        db: Session,
        course_id: int,
        topic: str,
        question: Optional[str] = None,
        week_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Explain a concept using course materials.
        
        Args:
            db: Database session
            course_id: Course ID
            topic: Topic to explain
            question: Optional specific question
            week_number: Optional week to focus on
            
        Returns:
            Explanation with sources
        """
        # Retrieve relevant context
        context_chunks = self.rag_pipeline.retrieve_context(
            db=db,
            query=topic + (" " + question if question else ""),
            course_id=course_id,
            week_number=week_number,
            top_k=5
        )
        
        context_str = self.rag_pipeline.build_prompt_context(context_chunks)
        
        # Generate explanation
        prompt = self.PROMPTS["explain"].format(
            topic=topic,
            context=context_str,
            question=question or "No specific question"
        )
        
        explanation = self._call_llm(prompt)
        
        return {
            "explanation": explanation,
            "topic": topic,
            "sources": [
                {"title": c["title"], "url": c["url"], "source": c["source"]}
                for c in context_chunks
            ],
            "course_id": course_id,
            "week_number": week_number
        }
    
    def check_answer(
        self,
        question_type: str,
        question: Dict[str, Any],
        student_answer: str,
        mode: str = "practice"
    ) -> Dict[str, Any]:
        """
        Check a student's answer.
        
        Args:
            question_type: Type of question (mcq, short_text, python_code, step_by_step)
            question: Question data
            student_answer: Student's answer
            mode: Grading mode (practice or graded)
            
        Returns:
            Grading result with feedback
        """
        q_type = QuestionType(question_type)
        g_mode = GradingMode(mode)
        
        return self.answer_checker.check_answer(
            question_type=q_type,
            question=question,
            student_answer=student_answer,
            mode=g_mode
        )
    
    def provide_hint(
        self,
        db: Session,
        course_id: int,
        problem: str,
        student_attempt: str,
        week_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Provide a hint for a problem without revealing the answer.
        
        Args:
            db: Database session
            course_id: Course ID
            problem: The problem statement
            student_attempt: Student's current attempt
            week_number: Optional week number
            
        Returns:
            Hint with guidance
        """
        # Get context
        context_chunks = self.rag_pipeline.retrieve_context(
            db=db,
            query=problem,
            course_id=course_id,
            week_number=week_number,
            top_k=3
        )
        
        context_str = self.rag_pipeline.build_prompt_context(context_chunks)
        
        prompt = self.PROMPTS["hint"].format(
            problem=problem,
            attempt=student_attempt,
            context=context_str
        )
        
        hint = self._call_llm(prompt)
        
        return {
            "hint": hint,
            "problem": problem,
            "relevant_topics": [c["title"] for c in context_chunks]
        }
    
    def summarize_material(
        self,
        db: Session,
        material_id: int
    ) -> Dict[str, Any]:
        """
        Summarize a learning material.
        
        Args:
            db: Database session
            material_id: Material ID to summarize
            
        Returns:
            Summary of the material
        """
        from app.models.material import Material
        
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return {"error": "Material not found"}
        
        content = material.content_text or material.description or material.snippet
        if not content:
            return {"error": "No content available to summarize"}
        
        prompt = self.PROMPTS["summarize"].format(content=content[:4000])
        
        summary = self._call_llm(prompt)
        
        return {
            "summary": summary,
            "material_id": material_id,
            "material_title": material.title,
            "original_length": len(content),
            "summary_length": len(summary)
        }
    
    def generate_practice_questions(
        self,
        db: Session,
        course_id: int,
        week_number: int,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate practice questions for a topic.
        
        Args:
            db: Database session
            course_id: Course ID
            week_number: Week number
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Generated practice questions
        """
        # Get syllabus topic
        syllabus = (
            db.query(Syllabus)
            .filter(
                Syllabus.course_id == course_id,
                Syllabus.week_number == week_number,
                Syllabus.is_active == True
            )
            .first()
        )
        
        if not syllabus:
            return {"error": "Syllabus not found"}
        
        # Get context
        context_chunks = self.rag_pipeline.retrieve_context(
            db=db,
            query=syllabus.topic,
            course_id=course_id,
            week_number=week_number,
            top_k=5
        )
        
        context_str = self.rag_pipeline.build_prompt_context(context_chunks)
        
        prompt = self.PROMPTS["generate_questions"].format(
            topic=syllabus.topic,
            difficulty=difficulty,
            context=context_str,
            num_questions=num_questions
        )
        
        questions_text = self._call_llm(prompt)
        
        # Parse questions (simple parsing - could be improved)
        questions = self._parse_generated_questions(questions_text)
        
        return {
            "topic": syllabus.topic,
            "week_number": week_number,
            "difficulty": difficulty,
            "questions": questions,
            "sources": [c["title"] for c in context_chunks]
        }
    
    def detect_weak_topics(
        self,
        db: Session,
        student_id: int,
        course_id: int
    ) -> Dict[str, Any]:
        """
        Detect weak topics for a student based on their performance.
        
        Args:
            db: Database session
            student_id: Student user ID
            course_id: Course ID
            
        Returns:
            List of weak topics with recommendations
        """
        # This would typically query a student_performance table
        # For now, return a placeholder structure
        
        # TODO: Implement actual performance tracking
        # Query student's quiz/assignment results
        # Aggregate scores by topic/week
        # Identify topics below threshold
        
        return {
            "student_id": student_id,
            "course_id": course_id,
            "weak_topics": [],
            "recommendations": [],
            "message": "Performance tracking not yet implemented"
        }
    
    def get_revision_suggestions(
        self,
        db: Session,
        student_id: int,
        course_id: int
    ) -> Dict[str, Any]:
        """
        Get personalized revision suggestions.
        
        Args:
            db: Database session
            student_id: Student ID
            course_id: Course ID
            
        Returns:
            Revision plan with prioritized topics
        """
        weak_topics = self.detect_weak_topics(db, student_id, course_id)
        
        suggestions = {
            "student_id": student_id,
            "course_id": course_id,
            "priority_topics": weak_topics.get("weak_topics", []),
            "recommended_materials": [],
            "practice_questions_available": True,
            "estimated_study_time": "2-3 hours"
        }
        
        return suggestions
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM with a prompt.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            LLM response text
        """
        if not self.llm_client:
            return self._get_mock_response(prompt)
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI tutor for university students."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return self._get_mock_response(prompt)
    
    def _get_mock_response(self, prompt: str) -> str:
        """Generate a mock response when LLM is not available."""
        if "explain" in prompt.lower():
            return """This is a mock explanation. In a production environment, this would be generated by the AI model using the course materials as context.

Key points:
1. The concept involves understanding fundamental principles
2. It builds upon previous knowledge
3. Practical applications include real-world scenarios

For a complete explanation, please ensure the OpenAI API key is configured."""
        
        elif "hint" in prompt.lower():
            return "Consider reviewing the fundamental concepts related to this problem. Think about what approach might work best given the constraints."
        
        elif "summarize" in prompt.lower():
            return "This is a mock summary. The actual summary would condense the key points from the material into a concise review format."
        
        elif "question" in prompt.lower():
            return """1. What is the main concept discussed in this topic?
2. How does this concept apply to real-world scenarios?
3. What are the key differences between related approaches?
4. Explain the process step by step.
5. What are the advantages and limitations?"""
        
        return "Mock response - LLM not configured."
    
    def _parse_generated_questions(self, text: str) -> List[Dict[str, Any]]:
        """Parse generated questions text into structured format."""
        questions = []
        lines = text.strip().split('\n')
        
        current_question = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a new question (starts with number)
            if line[0].isdigit() and '.' in line[:3]:
                if current_question:
                    questions.append(current_question)
                current_question = {
                    "question": line.split('.', 1)[1].strip(),
                    "type": "short_text"  # Default type
                }
            elif current_question:
                # Append to current question
                current_question["question"] += " " + line
        
        if current_question:
            questions.append(current_question)
        
        return questions


# Singleton instance
_ai_tutor: Optional[AITutor] = None


def get_ai_tutor() -> AITutor:
    """Get or create the AI tutor singleton."""
    global _ai_tutor
    if _ai_tutor is None:
        _ai_tutor = AITutor()
    return _ai_tutor
