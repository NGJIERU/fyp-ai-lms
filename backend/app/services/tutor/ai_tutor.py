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
Your task is to explain the following topic clearly and thoroughly, ensuring the student understands the underlying principles.

Guidelines:
- **Academic Integrity**: If the topic appears to be an assignment question, DO NOT provide a direct solution. Instead, explain the relevant concepts and provide a similar example.
- Use simple language first, then introduce technical terms.
- Provide concrete examples, but distinct from potential assignment problems.
- Break down complex concepts into smaller parts.
- Reference the provided course materials explicitly.

Topic to explain: {topic}

Course Materials Context:
{context}

Student's specific question (if any): {question}

Provide a clear, educational explanation.
IMPORTANT: Do NOT generate practice questions or quizzes at the end. Your goal is purely to explain the concept.""",

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

Provide feedback that is encouraging but identifies areas for improvement. Do not just give the correct answer if they are wrong; explain *why* they are wrong and guide them to the correct reasoning.""",

        "hint": """You are an AI tutor providing hints without giving away the answer.
The student is working on a problem and needs guidance.

Problem: {problem}
Student's current attempt: {attempt}

Course Materials Context:
{context}

Provide a helpful hint that:
1. Points them in the right direction
2. **DOES NOT reveal the answer** (Critical)
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

        "generate_questions": """You are an AI tutor generating structured practice questions.
Based on the topic and materials, generate multiple-choice questions (MCQs) in JSON format.

Topic: {topic}
Cognitive Level: {cognitive_level}
Number of questions: {num_questions}

Course Materials Context:
{context}

BLOOM'S TAXONOMY LEVELS (use the specified cognitive_level):
- remember: Recall facts, terms, basic concepts (e.g., "What is...", "Define...", "List...")
- understand: Explain ideas, interpret meaning (e.g., "Explain why...", "Summarize...", "Compare...")  
- apply: Use information in new situations (e.g., "Calculate...", "Solve...", "Implement...")
- analyze: Break down into parts, identify patterns (e.g., "Why does...", "What is the relationship...")
- evaluate: Justify decisions, critique (e.g., "Which approach is best...", "Evaluate...")
- create: Produce new ideas, design solutions (e.g., "Design...", "Propose...", "What if...")

DISTRACTOR GUIDELINES:
- Option A-D should all be plausible to someone who hasn't mastered the topic
- Wrong answers should reflect common misconceptions or partial understanding
- Avoid obviously wrong answers that can be eliminated without knowledge

OUTPUT FORMAT - Return ONLY a valid JSON array, no other text:
```json
[
  {{
    "question": "Clear question text here?",
    "options": {{
      "A": "First option",
      "B": "Second option", 
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct_answer": "B",
    "explanation": "Why B is correct and why other options are wrong",
    "cognitive_level": "{cognitive_level}",
    "distractors_rationale": "Why the wrong options are plausible misconceptions"
  }}
]
```

Generate exactly {num_questions} questions following this JSON format.""",

        "chat": """You are an AI Personal Tutor having a conversation with a university student.
Your goal is to be helpful, encouraging, and educational, **but you must adhere to strict academic integrity guidelines.**

Course: {course_name}
Topic context: {topic}

Relevant Course Materials:
{context}

Conversation History:
{history}

Student's new message: {message}

**CRITICAL PEDAGOGICAL GUARDRAILS:**
1. **NO DIRECT ANSWERS**: If the student asks you to write code, solve a math problem, or write an essay for an assignment, **REFUSE politely**.
   - Example refusal: "I cannot write the code for you, as that would be academic dishonesty. However, I can help you structure your approach. What have you tried so far?"
2. **SOCRATIC METHOD**: Instead of giving answers, ask guiding questions to lead the student to the solution.
3. **CODE HELP**: If asked for code, provide *snippets* for specific concepts or syntax examples, but **NEVER** full solutions to valid assignment problems.
4. **SOURCE GROUNDING**: Base your answers on the provided Course Materials. If the information comes from the materials, explicitly mention it (e.g., "As seen in Week 3 slides...").

General Guidelines:
1. Answer the student's question using the provided course materials.
2. If the answer isn't in the materials, use your general knowledge but mention that it's general info.
3. Be concise but thorough.
4. Maintain a friendly, supportive tone.

Response:"""
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        use_huggingface: Optional[bool] = None,
        use_openai: Optional[bool] = None,
        rag_pipeline: Optional[RAGPipeline] = None
    ):
        """
        Initialize the AI Tutor.
        
        Args:
            api_key: API key (HuggingFace token or OpenAI key)
            model: LLM model to use
            use_huggingface: Force enable/disable HuggingFace usage
            use_openai: Force enable/disable OpenAI usage (fallback)
            rag_pipeline: Injected RAG pipeline (mainly for testing)
        """
        # Determine which LLM provider to use (HuggingFace takes priority)
        self.use_huggingface = settings.USE_HUGGINGFACE_TUTOR if use_huggingface is None else use_huggingface
        self.use_openai = settings.USE_OPENAI_TUTOR if use_openai is None else use_openai
        
        # Set API key and model based on provider
        if self.use_huggingface:
            self.api_key = api_key or settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")
            self.model = model or settings.HUGGINGFACE_MODEL
            self.provider = "huggingface"
        elif self.use_openai:
            self.api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            self.model = model or settings.AI_TUTOR_MODEL
            self.provider = "openai"
        else:
            self.api_key = None
            self.model = None
            self.provider = "mock"

        self.rag_pipeline = rag_pipeline or RAGPipeline(
            embedding_service=get_embedding_service(
                model_name=settings.EMBEDDING_MODEL_NAME,
                use_openai=settings.USE_OPENAI_EMBEDDINGS,
                openai_api_key=settings.OPENAI_API_KEY
            )
        )
        self.answer_checker = AnswerChecker()
        self.llm_client = None
        
        if self.api_key and self.provider != "mock":
            self._init_llm_client()
        else:
            logger.info("AI Tutor running in mock mode (no API key configured)")
    
    def _init_llm_client(self):
        """Initialize the LLM client based on the configured provider."""
        if self.provider == "huggingface":
            self._init_huggingface_client()
        elif self.provider == "openai":
            self._init_openai_client()
    
    def _init_huggingface_client(self):
        """Initialize the HuggingFace InferenceClient."""
        logger.info(f"Attempting to initialize HuggingFace client with model: {self.model}")
        try:
            from huggingface_hub import InferenceClient
            self.llm_client = InferenceClient(
                model=self.model,
                token=self.api_key
            )
            logger.info(f"✅ Initialized HuggingFace InferenceClient with model {self.model}")
        except ImportError as e:
            logger.error(f"❌ huggingface_hub package not installed: {e}")
        except Exception as e:
            logger.error(f"❌ Error initializing HuggingFace client: {e}", exc_info=True)
    
    def _init_openai_client(self):
        """Initialize the OpenAI client (fallback)."""
        logger.info(f"Attempting to initialize OpenAI client with model: {self.model}")
        try:
            from openai import OpenAI
            self.llm_client = OpenAI(api_key=self.api_key)
            logger.info(f"✅ Initialized OpenAI client with model {self.model}")
        except ImportError as e:
            logger.error(f"❌ OpenAI package not installed: {e}")
        except Exception as e:
            logger.error(f"❌ Error initializing OpenAI client: {e}", exc_info=True)
    
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
                {"title": c["title"], "url": c["url"], "source": c["source"], "type": c.get("type", "document")}
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
        # Map difficulty to Bloom's taxonomy cognitive levels
        DIFFICULTY_TO_COGNITIVE = {
            "easy": "remember",
            "medium": "apply", 
            "hard": "analyze"
        }
        cognitive_level = DIFFICULTY_TO_COGNITIVE.get(difficulty, "understand")
        
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
            cognitive_level=cognitive_level,
            context=context_str,
            num_questions=num_questions
        )
        
        questions_text = self._call_llm(prompt)
        
        # Parse questions - try JSON first, fallback to regex
        questions = self._parse_mcq_json(questions_text)
        if not questions:
            logger.warning("JSON parsing failed, falling back to regex parser")
            questions = self._parse_generated_questions(questions_text)
            if not questions:
                logger.error(f"Failed to generate questions - LLM returned no parseable content. Raw text: {questions_text[:500]}...")
        
        # If still no questions, return error
        if not questions:
            logger.error("Failed to generate questions - LLM returned no parseable content")
            return {"error": "Failed to generate questions. Please try again."}
        
        return {
            "topic": syllabus.topic,
            "week_number": week_number,
            "difficulty": difficulty,
            "cognitive_level": cognitive_level,
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
            if self.provider == "huggingface":
                return self._call_huggingface(prompt)
            else:
                return self._call_openai(prompt)
        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return self._get_mock_response(prompt)
    
    def _call_huggingface(self, prompt: str) -> str:
        """Call the HuggingFace Inference API."""
        messages = [
            {"role": "system", "content": "You are a helpful AI tutor for university students."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _call_openai(self, prompt: str) -> str:
        """Call the OpenAI API (fallback)."""
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
    
    def _get_mock_response(self, prompt: str) -> str:
        """
        Generate a 'Smart Offline' response using retrieved context when LLM is unavailable.
        Uses regex to extract the RAG context from the detailed prompt.
        """
        import re
        
        # 1. Extract Context from the prompt structure
        context = ""
        # Prompts are formatted like "Course Materials Context:\n{context}\n\n"
        context_match = re.search(r"(?:Course Materials Context|Relevant Course Materials):\s*\n(.*?)(?:\n\n|\n[A-Z][a-zA-Z\s]+:|$)", prompt, re.DOTALL)
        
        if context_match:
            raw_context = context_match.group(1).strip()
            # If we found something substantial (more than just a label)
            if len(raw_context) > 20:
                context = raw_context
                # Truncate if extremely long to avoid massive logs/UI clutter, but keep enough for user
                if len(context) > 2000:
                    context = context[:2000] + "\n... (content truncated for display)"
        
        if not context:
            context = "No specific course materials found for this query in the database."
            logger.warning(f"RAG context retrieval empty for prompt: {prompt[:50]}...")

        # 2. Return context-aware responses based on prompt type
        prompt_lower = prompt.lower()
        
        if "explain" in prompt_lower or "chat" in prompt_lower or "conversation" in prompt_lower:
            return f"""✨ **Smart Offline Mode** (AI Tutor)

I found the following relevant information in your course materials that answers your question:

---------------------------------------------------
{context}
---------------------------------------------------

*(Note: The OpenAI API key is currently invalid/missing, so I cannot generate a custom explanation. However, the search results above are accurate from your uploaded documents.)*"""
            
        elif "generate" in prompt_lower and "questions" in prompt_lower:
             # Extract topic
            topic = "the topic"
            topic_match = re.search(r"Topic: (.*)", prompt)
            if topic_match:
                topic = topic_match.group(1).strip()

            return f"""Here are some practice questions based on **{topic}** (Offline Mode):

1. Define the core concepts of {topic} based on the course notes.
2. Explain the significance of {topic} in the context of this course.
3. Compare and contrast the key elements found in the materials regarding {topic}.
4. Discuss the practical applications of {topic}.

*Study Tip: Use the search feature or 'Auto-Discover' to find more detailed slides on this topic!*"""
            
        elif "check" in prompt_lower or "evaluate" in prompt_lower:
             return f"""✨ **Smart Offline Feedback**

I've analyzed your answer against the course materials:

**Relevant Context:**
{context[:1000]}...

**Assessment:**
I cannot perform detailed grading without the AI model, but please ensure your answer aligns with the definitions provided in the context above.

*(Running in Offline Mode)*"""
             
        elif "hint" in prompt_lower:
             return f"""💡 **Hint (Offline Mode)**
             
Review this section of your notes:

"{context[:500]}..."

Focus on how this concept applies to the problem statement."""

        elif "summarize" in prompt_lower:
             return f"""📝 **Material Summary (Offline)**

Here is the start of the material content:

{context[:1000]}...

*(Full summarization requires active AI connection)*"""

        return "Offline Mode: Unable to process request without AI connection."
    
    def _parse_mcq_json(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse MCQ questions from JSON format.
        
        Args:
            text: LLM response text (may contain markdown code blocks)
            
        Returns:
            List of validated MCQ dictionaries, or empty list if parsing fails
        """
        import json
        import re
        
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # Try to find raw JSON array
                json_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', text)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.warning("No JSON found in LLM response")
                    return []
            
            # Parse JSON
            questions = json.loads(json_str)
            
            if not isinstance(questions, list):
                logger.warning("Parsed JSON is not a list")
                return []
            
            # Validate and normalize each question
            validated_questions = []
            for q in questions:
                if not isinstance(q, dict):
                    continue
                    
                # Check required fields
                if "question" not in q or "options" not in q or "correct_answer" not in q:
                    logger.warning(f"Question missing required fields: {q.keys()}")
                    continue
                
                # Normalize options to ensure A, B, C, D format
                options = q.get("options", {})
                if isinstance(options, dict):
                    # Already in dict format
                    normalized_options = options
                elif isinstance(options, list):
                    # Convert list to dict
                    normalized_options = {
                        chr(65 + i): opt for i, opt in enumerate(options[:4])
                    }
                else:
                    continue
                
                validated_q = {
                    "question": q["question"],
                    "options": normalized_options,
                    "correct_answer": q["correct_answer"].upper() if isinstance(q["correct_answer"], str) else q["correct_answer"],
                    "explanation": q.get("explanation", ""),
                    "cognitive_level": q.get("cognitive_level", "understand"),
                    "distractors_rationale": q.get("distractors_rationale", ""),
                    "type": "mcq"
                }
                validated_questions.append(validated_q)
            
            logger.info(f"Successfully parsed {len(validated_questions)} MCQ questions from JSON")
            return validated_questions
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing MCQ JSON: {e}")
            return []
    
    def _parse_generated_questions(self, text: str) -> List[Dict[str, Any]]:
        """Parse generated questions text into structured format."""
        import re
        questions = []
        
        # Regex to find numbered lines: "1. Question..." or "1) Question..." or "**1.** Question..."
        # It captures the question text in group 2
        question_pattern = re.compile(r'^\s*(?:[\*\#]*\s*)?\d+[\.\)]\s+(.+)$')
        
        lines = text.strip().split('\n')
        current_question = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = question_pattern.match(line)
            if match:
                if current_question:
                    questions.append(current_question)
                
                # Start new question
                current_question = {
                    "question": match.group(1).strip(),
                    "type": "short_text"
                }
            elif current_question:
                # Continuation of previous question
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
        logger.info(f"🔧 Creating new AITutor instance. USE_OPENAI_TUTOR={settings.USE_OPENAI_TUTOR}, API_KEY_SET={bool(settings.OPENAI_API_KEY)}, MODEL={settings.AI_TUTOR_MODEL}")
        _ai_tutor = AITutor()
        logger.info(f"✅ AITutor created. LLM client initialized: {_ai_tutor.llm_client is not None}")
    return _ai_tutor
