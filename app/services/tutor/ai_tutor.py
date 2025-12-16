"""
AI Personal Tutor - Main tutor service
Provides explanations, feedback, weak topic detection, and personalized learning
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
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

Questions:""",

        "chat": """You are an AI Personal Tutor having a conversation with a student.
Your goal is to be helpful, encouraging, and educational.

Course: {course_name}
Topic context (based on current discussion): {topic}

Relevant Course Materials:
{context}

Conversation History:
{history}

Student's new message: {message}

Guidelines:
1. Answer the student's question using the provided course materials.
2. If the answer isn't in the materials, use your general knowledge but mention that it's general info.
3. Be concise but thorough.
4. Encourage critical thinking - if they ask for an answer, guide them instead of just giving it (unless it's a simple fact).
5. Maintain a friendly, supportive tone.

Response:"""
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
            "sources": [{"title": c.get("title", "Unknown"), "source": c.get("source", "Unknown")} for c in context_chunks],
            "course_id": course_id,
            "week_number": week_number
        }
    
    def chat(
        self,
        db: Session,
        course_id: int,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        week_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Have a multi-turn conversation with the tutor.
        
        Args:
            db: Database session
            course_id: Course ID
            message: Current user message
            conversation_history: List of {"role": "user"|"assistant", "content": "..."}
            week_number: Optional week context
            
        Returns:
            Response with sources
        """
        # Get course name for context
        course = db.query(Course).filter(Course.id == course_id).first()
        course_name = course.name if course else "Unknown Course"
        
        # Format history for prompt
        history_str = ""
        if conversation_history:
            # Limit history to last 6 messages to save tokens
            recent_history = conversation_history[-6:]
            for msg in recent_history:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"
        
        # Retrieve context based on the current message (and maybe last message for context)
        # Using just current message for query is usually sufficient for RAG if message represents the intent
        context_chunks = self.rag_pipeline.retrieve_context(
            db=db,
            query=message,
            course_id=course_id,
            week_number=week_number,
            top_k=5
        )
        
        context_str = self.rag_pipeline.build_prompt_context(context_chunks)
        
        # Generate response
        prompt = self.PROMPTS["chat"].format(
            course_name=course_name,
            topic=message, # Using message as loose topic proxy
            context=context_str,
            history=history_str,
            message=message
        )
        
        response = self._call_llm(prompt)
        
        return {
            "response": response,
            "sources": [
                {"title": c["title"], "url": c["url"], "source": c["source"]}
                for c in context_chunks
            ],
            "suggested_topics": [] # Could implement suggestion logic later
        }
    
    def check_answer(
        self,
        db: Session,
        student_id: int,
        course_id: int,
        week_number: int,
        question_type: str,
        question: Dict[str, Any],
        student_answer: str,
        mode: str = "practice"
    ) -> Dict[str, Any]:
        """
        Check a student's answer and record performance.
        
        Args:
            db: Database session
            student_id: Student ID
            course_id: Course ID
            week_number: Week number
            question_type: Type of question
            question: Question data
            student_answer: Student's answer
            mode: Grading mode
            
        Returns:
            Grading result with feedback
        """
        from app.models.performance import QuizAttempt, TopicPerformance, ActivityLog
        
        q_type = QuestionType(question_type)
        g_mode = GradingMode(mode)
        
        # 1. Check answer using logic
        result = self.answer_checker.check_answer(
            question_type=q_type,
            question=question,
            student_answer=student_answer,
            mode=g_mode
        )
        
        # 2. Record attempt
        attempt = QuizAttempt(
            student_id=student_id,
            course_id=course_id,
            week_number=week_number,
            question_type=question_type,
            question_data=question,
            student_answer=student_answer,
            score=result.get("score", 0),
            max_score=result.get("max_score", 1),
            is_correct=result.get("is_correct", False),
            feedback=result.get("feedback"),
            mode=mode
        )
        db.add(attempt)
        
        # 3. Update aggregated Topic Performance
        topic_perf = (
            db.query(TopicPerformance)
            .filter(
                TopicPerformance.student_id == student_id,
                TopicPerformance.course_id == course_id,
                TopicPerformance.week_number == week_number
            )
            .first()
        )
        
        if not topic_perf:
            topic_perf = TopicPerformance(
                student_id=student_id,
                course_id=course_id,
                week_number=week_number,
                total_attempts=0,
                correct_attempts=0,
                average_score=0.0
            )
            db.add(topic_perf)
        
        # Update stats
        old_total = topic_perf.total_attempts
        new_total = old_total + 1
        
        current_score_pct = (result.get("score", 0) / result.get("max_score", 1)) * 100
        new_avg = ((topic_perf.average_score * old_total) + current_score_pct) / new_total
        
        topic_perf.total_attempts = new_total
        if result.get("is_correct", False):
            topic_perf.correct_attempts += 1
        
        topic_perf.average_score = new_avg
        topic_perf.last_attempt_at = datetime.now(timezone.utc)
        
        # Determine mastery/weakness
        if new_avg < 60 and new_total >= 3:
            topic_perf.is_weak_topic = True
            topic_perf.mastery_level = "remedial"
        elif new_avg >= 85 and new_total >= 3:
            topic_perf.is_weak_topic = False
            topic_perf.mastery_level = "mastered"
        elif new_avg >= 70:
            topic_perf.is_weak_topic = False
            topic_perf.mastery_level = "proficient"
        else:
            topic_perf.mastery_level = "learning"
            
        # 4. Log activity
        activity = ActivityLog(
            user_id=student_id,
            action="submit_quiz_attempt",
            resource_type="quiz_attempt",
            resource_id=attempt.id, # attempt object is added but not flushed/refreshed yet, so ID might be None unless we flush first or let session handle it.
            # However, SQLAlchemy usually handles this if we add both to session. But to be safe on ID:
            course_id=course_id,
            extra_data={
                "week_number": week_number,
                "is_correct": result.get("is_correct", False),
                "score": result.get("score", 0),
                "mode": mode
            }
        )
        db.add(activity)

        db.commit()
        db.refresh(attempt)
        
        return result
    
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
        from app.models.performance import TopicPerformance
        from app.models.syllabus import Syllabus
        from app.models.material import Material
        
        # Find topics flagged as weak
        weak_perfs = (
            db.query(TopicPerformance)
            .filter(
                TopicPerformance.student_id == student_id,
                TopicPerformance.course_id == course_id,
                TopicPerformance.is_weak_topic == True
            )
            .all()
        )
        
        results = []
        recommendations = set()
        
        for perf in weak_perfs:
            # Get topic name
            syllabus = (
                db.query(Syllabus)
                .filter(
                    Syllabus.course_id == course_id, 
                    Syllabus.week_number == perf.week_number
                )
                .first()
            )
            topic_name = syllabus.topic if syllabus else f"Week {perf.week_number}"
            
            results.append({
                "topic": topic_name,
                "week_number": perf.week_number,
                "score": perf.average_score,
                "attempts": perf.total_attempts
            })
            
            # Find recommended materials for this weak topic via MaterialTopic
            from app.models.material import MaterialTopic
            material_topics = (
                db.query(MaterialTopic)
                .filter(
                    MaterialTopic.course_id == course_id,
                    MaterialTopic.week_number == perf.week_number,
                    MaterialTopic.approved_by_lecturer == True
                )
                .limit(2)
                .all()
            )
            for mt in material_topics:
                if mt.material:
                    recommendations.add(mt.material.title)
        
        return {
            "student_id": student_id,
            "course_id": course_id,
            "weak_topics": results,
            "recommendations": list(recommendations),
            "message": "Analysis based on practice performance"
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
        
        elif "chat" in prompt.lower() or "conversation" in prompt.lower():
            return """Hello! I'm your AI Tutor. Since I'm running in mock mode, I can't generate a dynamic response based on your specific question about the course materials. 

In a real deployment, I would use the RAG pipeline to find relevant content from your course documents and answer: "{}" 

How else can I help you today?""".format(prompt[-50:].replace("\n", " "))

        elif "hint" in prompt.lower():
            return "Consider reviewing the fundamental concepts related to this problem. Think about what approach might work best given the constraints."
        
        elif "summarize" in prompt.lower():
            return "This is a mock summary. The actual summary would condense the key points from the material into a concise review format."
        
        elif "question" in prompt.lower():
            # Extract topic if possible
            topic = "this topic"
            if "Topic:" in prompt:
                try:
                    topic = prompt.split("Topic:")[1].split("\n")[0].strip()
                except:
                    pass
            
            return f"""1. What are the core principles of {{topic}}?
2. Explain how {{topic}} applies to real-world scenarios.
3. Compare and contrast different approaches within {{topic}}.
4. Describe the step-by-step process involved in {{topic}}.
5. What are the common challenges when working with {{topic}}?""".format(topic=topic)
        
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
