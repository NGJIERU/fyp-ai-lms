"""
Tests for AI Tutor Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.tutor.answer_checker import AnswerChecker, QuestionType, GradingMode
from app.services.tutor.rag_pipeline import RAGPipeline, ContextBuilder
from app.services.tutor.ai_tutor import AITutor


class TestAnswerChecker:
    """Tests for the AnswerChecker class."""
    
    @pytest.fixture
    def checker(self):
        return AnswerChecker()
    
    # ==================== MCQ Tests ====================
    
    def test_mcq_correct_answer(self, checker):
        """Test MCQ with correct answer."""
        question = {
            "question": "What is 2 + 2?",
            "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
            "correct_answer": "B",
            "explanation": "2 + 2 equals 4"
        }
        
        result = checker.check_answer(
            QuestionType.MCQ,
            question,
            "B",
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == True
        assert result["score"] == 1
        assert "Correct" in result["feedback"]
    
    def test_mcq_incorrect_answer_practice(self, checker):
        """Test MCQ with incorrect answer in practice mode."""
        question = {
            "question": "What is 2 + 2?",
            "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
            "correct_answer": "B",
            "explanation": "2 + 2 equals 4"
        }
        
        result = checker.check_answer(
            QuestionType.MCQ,
            question,
            "A",
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == False
        assert result["score"] == 0
        assert result["correct_answer"] == "B"
        assert result["explanation"] == "2 + 2 equals 4"
    
    def test_mcq_incorrect_answer_graded(self, checker):
        """Test MCQ with incorrect answer in graded mode."""
        question = {
            "question": "What is 2 + 2?",
            "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
            "correct_answer": "B",
            "explanation": "2 + 2 equals 4"
        }
        
        result = checker.check_answer(
            QuestionType.MCQ,
            question,
            "A",
            GradingMode.GRADED
        )
        
        assert result["is_correct"] == False
        assert "correct_answer" not in result  # Should not reveal answer
        assert "hints" in result
    
    def test_mcq_case_insensitive(self, checker):
        """Test MCQ answer is case insensitive."""
        question = {
            "question": "Test",
            "correct_answer": "B"
        }
        
        result = checker.check_answer(
            QuestionType.MCQ,
            question,
            "b",
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == True
    
    # ==================== Short Text Tests ====================
    
    def test_short_text_full_match(self, checker):
        """Test short text with all keywords matched."""
        question = {
            "question": "Explain machine learning.",
            "expected_keywords": ["algorithm", "data", "patterns", "predictions"],
            "model_answer": "Machine learning uses algorithms to learn patterns from data and make predictions.",
            "min_length": 20
        }
        
        result = checker.check_answer(
            QuestionType.SHORT_TEXT,
            question,
            "Machine learning is a type of algorithm that learns patterns from data to make predictions about new data.",
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == True
        assert result["keyword_coverage"] >= 0.8
    
    def test_short_text_partial_match(self, checker):
        """Test short text with partial keyword match."""
        question = {
            "question": "Explain machine learning.",
            "expected_keywords": ["algorithm", "data", "patterns", "predictions"],
            "model_answer": "Machine learning uses algorithms to learn patterns from data.",
            "min_length": 20
        }
        
        result = checker.check_answer(
            QuestionType.SHORT_TEXT,
            question,
            "Machine learning uses data to find patterns.",
            GradingMode.PRACTICE
        )
        
        assert result["keyword_coverage"] == 0.5  # 2 out of 4 keywords
        assert result["score"] == 0.7  # Partial credit
    
    def test_short_text_too_short(self, checker):
        """Test short text that is too short."""
        question = {
            "question": "Explain machine learning.",
            "expected_keywords": ["algorithm", "data"],
            "min_length": 50
        }
        
        result = checker.check_answer(
            QuestionType.SHORT_TEXT,
            question,
            "ML uses data.",
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == False
        assert "hints" in result or "too short" in str(result.get("feedback", "")).lower() or result["score"] < 0.5
    
    # ==================== Python Code Tests ====================
    
    def test_python_code_syntax_error(self, checker):
        """Test Python code with syntax error."""
        question = {
            "function_name": "add",
            "test_cases": [{"input": [1, 2], "expected": 3}]
        }
        
        result = checker.check_answer(
            QuestionType.PYTHON_CODE,
            question,
            "def add(a, b)\n    return a + b",  # Missing colon
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == False
        assert result["score"] == 0
        assert "syntax" in result["feedback"].lower() or "error" in result["feedback"].lower()
    
    def test_python_code_correct(self, checker):
        """Test Python code with correct solution."""
        question = {
            "function_name": "add",
            "test_cases": [
                {"input": [1, 2], "expected": 3},
                {"input": [0, 0], "expected": 0},
                {"input": [-1, 1], "expected": 0}
            ],
            "model_solution": "def add(a, b): return a + b"
        }
        
        result = checker.check_answer(
            QuestionType.PYTHON_CODE,
            question,
            "def add(a, b):\n    return a + b",
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == True
        assert result["tests_passed"] == 3
        assert result["tests_total"] == 3
    
    def test_python_code_partial_correct(self, checker):
        """Test Python code with partial correctness."""
        question = {
            "function_name": "absolute",
            "test_cases": [
                {"input": [5], "expected": 5},
                {"input": [-5], "expected": 5},
                {"input": [0], "expected": 0}
            ]
        }
        
        # This implementation doesn't handle negative numbers
        result = checker.check_answer(
            QuestionType.PYTHON_CODE,
            question,
            "def absolute(x):\n    return x",  # Wrong for negative
            GradingMode.PRACTICE
        )
        
        assert result["tests_passed"] == 2  # Passes for 5 and 0
        assert result["tests_total"] == 3
        assert result["is_correct"] == False
    
    # ==================== Step by Step Tests ====================
    
    def test_step_by_step_correct(self, checker):
        """Test step-by-step with correct solution."""
        question = {
            "question": "Solve: 2x + 4 = 10",
            "steps": [
                {"description": "Subtract 4 from both sides", "expected": "2x = 6", "points": 1},
                {"description": "Divide by 2", "expected": "x = 3", "points": 1}
            ],
            "final_answer": "x = 3"
        }
        
        result = checker.check_answer(
            QuestionType.STEP_BY_STEP,
            question,
            "Step 1: 2x = 6\nStep 2: x = 3",
            GradingMode.PRACTICE
        )
        
        assert result["is_correct"] == True or result["score"] >= 0.8
    
    # ==================== Utility Method Tests ====================
    
    def test_validate_python_syntax_valid(self, checker):
        """Test syntax validation with valid code."""
        result = checker._validate_python_syntax("def foo(): return 42")
        assert result["valid"] == True
    
    def test_validate_python_syntax_invalid(self, checker):
        """Test syntax validation with invalid code."""
        result = checker._validate_python_syntax("def foo( return 42")
        assert result["valid"] == False
        assert "error" in result
    
    def test_normalize_math(self, checker):
        """Test math expression normalization."""
        assert checker._normalize_math("x = 3") == "x=3"
        assert checker._normalize_math("2 × 3") == "2*3"
        assert checker._normalize_math("x^2") == "x**2"


class TestRAGPipeline:
    """Tests for the RAGPipeline class."""
    
    def test_build_prompt_context_empty(self):
        """Test building prompt context with no chunks."""
        result = RAGPipeline().build_prompt_context([])
        assert result == ""
    
    def test_build_prompt_context_with_chunks(self):
        """Test building prompt context with chunks."""
        chunks = [
            {
                "content": "This is content 1",
                "source": "MIT OCW",
                "title": "Intro to Python",
                "url": "http://example.com/1",
                "type": "video",
                "similarity": 0.9
            },
            {
                "content": "This is content 2",
                "source": "YouTube",
                "title": "Python Tutorial",
                "url": "http://example.com/2",
                "type": "video",
                "similarity": 0.8
            }
        ]
        
        result = RAGPipeline().build_prompt_context(chunks, include_sources=True)
        
        assert "Intro to Python" in result
        assert "Python Tutorial" in result
        assert "MIT OCW" in result
        assert "This is content 1" in result


class TestContextBuilder:
    """Tests for the ContextBuilder class."""
    
    def test_build_system_prompt(self):
        """Test building system prompt."""
        prompt = ContextBuilder.build_system_prompt(
            course_name="Introduction to Python",
            topic="Variables and Data Types",
            context="Sample context about variables..."
        )
        
        assert "Introduction to Python" in prompt
        assert "Variables and Data Types" in prompt
        assert "Sample context" in prompt
        assert "ai tutor" in prompt.lower()


class TestAITutor:
    """Tests for the AITutor class."""
    
    @pytest.fixture
    def mock_tutor(self):
        """Create a tutor with mocked LLM."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
            tutor = AITutor()
            return tutor
    
    def test_get_mock_response_explain(self, mock_tutor):
        """Test mock response for explanation."""
        response = mock_tutor._get_mock_response("Please explain this concept")
        assert "mock explanation" in response.lower() or "key points" in response.lower()
    
    def test_get_mock_response_hint(self, mock_tutor):
        """Test mock response for hint."""
        response = mock_tutor._get_mock_response("Give me a hint for this problem")
        assert "consider" in response.lower() or "think" in response.lower()
    
    def test_get_mock_response_summarize(self, mock_tutor):
        """Test mock response for summarization."""
        response = mock_tutor._get_mock_response("Summarize this material")
        assert "summary" in response.lower()
    
    def test_parse_generated_questions(self, mock_tutor):
        """Test parsing generated questions."""
        text = """1. What is machine learning?
2. How does a neural network work?
3. Explain the difference between supervised and unsupervised learning."""
        
        questions = mock_tutor._parse_generated_questions(text)
        
        assert len(questions) == 3
        assert "machine learning" in questions[0]["question"].lower()
        assert "neural network" in questions[1]["question"].lower()
    
    def test_check_answer_delegates_to_checker(self, mock_tutor):
        """Test that check_answer delegates to AnswerChecker."""
        question = {
            "question": "What is 2+2?",
            "correct_answer": "B",
            "options": ["A) 3", "B) 4", "C) 5", "D) 6"]
        }
        
        result = mock_tutor.check_answer(
            question_type="mcq",
            question=question,
            student_answer="B",
            mode="practice"
        )
        
        assert result["is_correct"] == True
        assert result["score"] == 1


class TestGradingModes:
    """Tests for different grading modes."""
    
    @pytest.fixture
    def checker(self):
        return AnswerChecker()
    
    def test_practice_mode_shows_solution(self, checker):
        """Test that practice mode shows full solution."""
        question = {
            "question": "What is the capital of France?",
            "correct_answer": "A",
            "options": ["A) Paris", "B) London", "C) Berlin"],
            "explanation": "Paris is the capital of France."
        }
        
        result = checker.check_answer(
            QuestionType.MCQ,
            question,
            "B",  # Wrong answer
            GradingMode.PRACTICE
        )
        
        assert "correct_answer" in result
        assert result["correct_answer"] == "A"
        assert "explanation" in result
    
    def test_graded_mode_hides_solution(self, checker):
        """Test that graded mode hides full solution."""
        question = {
            "question": "What is the capital of France?",
            "correct_answer": "A",
            "options": ["A) Paris", "B) London", "C) Berlin"],
            "explanation": "Paris is the capital of France."
        }
        
        result = checker.check_answer(
            QuestionType.MCQ,
            question,
            "B",  # Wrong answer
            GradingMode.GRADED
        )
        
        assert "correct_answer" not in result
        assert "explanation" not in result
        assert "hints" in result
