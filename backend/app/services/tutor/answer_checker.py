"""
Answer Checker - Auto-grading for different question types
Supports MCQ, short text, Python code, and step-by-step problem solving
"""
import logging
import re
import ast
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_TEXT = "short_text"
    PYTHON_CODE = "python_code"
    STEP_BY_STEP = "step_by_step"


class GradingMode(str, Enum):
    PRACTICE = "practice"  # Full solutions shown
    GRADED = "graded"      # Only hints, no full solutions


class AnswerChecker:
    """
    Auto-grading service for different question types.
    Provides feedback based on grading mode (practice vs graded).
    """
    
    def __init__(self):
        self.llm_client = None  # Will be initialized when needed
    
    def check_answer(
        self,
        question_type: QuestionType,
        question: Dict[str, Any],
        student_answer: str,
        mode: GradingMode = GradingMode.PRACTICE
    ) -> Dict[str, Any]:
        """
        Check a student's answer and provide feedback.
        
        Args:
            question_type: Type of question
            question: Question data including correct answer
            student_answer: Student's submitted answer
            mode: Grading mode (practice or graded)
            
        Returns:
            Grading result with score, feedback, and hints
        """
        if question_type == QuestionType.MCQ:
            return self._check_mcq(question, student_answer, mode)
        elif question_type == QuestionType.SHORT_TEXT:
            return self._check_short_text(question, student_answer, mode)
        elif question_type == QuestionType.PYTHON_CODE:
            return self._check_python_code(question, student_answer, mode)
        elif question_type == QuestionType.STEP_BY_STEP:
            return self._check_step_by_step(question, student_answer, mode)
        else:
            return {
                "score": 0,
                "max_score": 1,
                "is_correct": False,
                "feedback": "Unknown question type",
                "hints": []
            }
    
    def _check_mcq(
        self,
        question: Dict[str, Any],
        student_answer: str,
        mode: GradingMode
    ) -> Dict[str, Any]:
        """
        Check multiple choice question.
        
        Question format:
        {
            "question": "What is...?",
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "B",
            "explanation": "..."
        }
        """
        correct_answer = question.get("correct_answer", "").strip().upper()
        student_answer = student_answer.strip().upper()
        
        # Extract just the letter if full option was provided
        if len(student_answer) > 1:
            student_answer = student_answer[0]
        
        is_correct = student_answer == correct_answer
        
        result = {
            "score": 1 if is_correct else 0,
            "max_score": 1,
            "is_correct": is_correct,
            "student_answer": student_answer,
        }
        
        if is_correct:
            result["feedback"] = "Correct! Well done."
            if mode == GradingMode.PRACTICE:
                result["explanation"] = question.get("explanation", "")
        else:
            if mode == GradingMode.PRACTICE:
                result["feedback"] = f"Incorrect. The correct answer is {correct_answer}."
                result["explanation"] = question.get("explanation", "")
                result["correct_answer"] = correct_answer
            else:
                result["feedback"] = "Incorrect. Review the relevant material and try again."
                result["hints"] = self._generate_mcq_hints(question, student_answer)
        
        return result
    
    def _check_short_text(
        self,
        question: Dict[str, Any],
        student_answer: str,
        mode: GradingMode
    ) -> Dict[str, Any]:
        """
        Check short text answer using keyword matching and semantic similarity.
        
        Question format:
        {
            "question": "Explain...",
            "expected_keywords": ["keyword1", "keyword2"],
            "model_answer": "...",
            "rubric": {...}
        }
        """
        expected_keywords = question.get("expected_keywords", [])
        model_answer = question.get("model_answer", "")
        
        # Keyword matching
        student_lower = student_answer.lower()
        matched_keywords = [
            kw for kw in expected_keywords
            if kw.lower() in student_lower
        ]
        
        keyword_score = len(matched_keywords) / max(len(expected_keywords), 1)
        
        # Length check (too short answers are likely incomplete)
        min_length = question.get("min_length", 20)
        length_ok = len(student_answer.strip()) >= min_length
        
        # Calculate score
        if keyword_score >= 0.8 and length_ok:
            score = 1.0
            is_correct = True
        elif keyword_score >= 0.5 and length_ok:
            score = 0.7
            is_correct = False
        elif keyword_score >= 0.3:
            score = 0.4
            is_correct = False
        else:
            score = 0.1 if len(student_answer.strip()) > 10 else 0
            is_correct = False
        
        result = {
            "score": score,
            "max_score": 1,
            "is_correct": is_correct,
            "keyword_coverage": keyword_score,
            "matched_keywords": matched_keywords,
        }
        
        if is_correct:
            result["feedback"] = "Good answer! You covered the key concepts."
        else:
            missing_keywords = [kw for kw in expected_keywords if kw not in matched_keywords]
            
            if mode == GradingMode.PRACTICE:
                result["feedback"] = "Your answer is partially correct."
                result["model_answer"] = model_answer
                result["missing_concepts"] = missing_keywords
            else:
                result["feedback"] = "Your answer needs improvement."
                result["hints"] = [
                    f"Consider discussing: {', '.join(missing_keywords[:2])}" if missing_keywords else "Add more detail to your answer."
                ]
                if not length_ok:
                    result["hints"].append(f"Your answer seems too short. Aim for at least {min_length} characters.")
        
        return result
    
    def _check_python_code(
        self,
        question: Dict[str, Any],
        student_answer: str,
        mode: GradingMode
    ) -> Dict[str, Any]:
        """
        Check Python code by running test cases.
        
        Question format:
        {
            "question": "Write a function...",
            "function_name": "my_function",
            "test_cases": [
                {"input": [1, 2], "expected": 3},
                {"input": [0, 0], "expected": 0}
            ],
            "model_solution": "def my_function(a, b): return a + b"
        }
        """
        function_name = question.get("function_name", "solution")
        test_cases = question.get("test_cases", [])
        
        # Validate syntax first
        syntax_result = self._validate_python_syntax(student_answer)
        if not syntax_result["valid"]:
            return {
                "score": 0,
                "max_score": len(test_cases),
                "is_correct": False,
                "feedback": f"Syntax error: {syntax_result['error']}",
                "hints": ["Check your code for syntax errors."]
            }
        
        # Run test cases
        passed_tests = 0
        test_results = []
        
        for i, test_case in enumerate(test_cases):
            result = self._run_test_case(
                student_answer,
                function_name,
                test_case["input"],
                test_case["expected"]
            )
            test_results.append(result)
            if result["passed"]:
                passed_tests += 1
        
        score = passed_tests / max(len(test_cases), 1)
        is_correct = passed_tests == len(test_cases)
        
        result = {
            "score": score,
            "max_score": 1,
            "is_correct": is_correct,
            "tests_passed": passed_tests,
            "tests_total": len(test_cases),
        }
        
        if is_correct:
            result["feedback"] = f"All {len(test_cases)} test cases passed! Great job!"
        else:
            failed_tests = [r for r in test_results if not r["passed"]]
            
            if mode == GradingMode.PRACTICE:
                result["feedback"] = f"Passed {passed_tests}/{len(test_cases)} test cases."
                result["test_results"] = test_results
                result["model_solution"] = question.get("model_solution", "")
            else:
                result["feedback"] = f"Passed {passed_tests}/{len(test_cases)} test cases."
                result["hints"] = self._generate_code_hints(failed_tests, question)
                # Show only first failing test input (not expected output)
                if failed_tests:
                    result["failing_input"] = failed_tests[0].get("input")
        
        return result
    
    def _check_step_by_step(
        self,
        question: Dict[str, Any],
        student_answer: str,
        mode: GradingMode
    ) -> Dict[str, Any]:
        """
        Check step-by-step problem solving.
        
        Question format:
        {
            "question": "Solve...",
            "steps": [
                {"description": "Step 1", "expected": "...", "points": 2},
                {"description": "Step 2", "expected": "...", "points": 3}
            ],
            "final_answer": "42"
        }
        """
        steps = question.get("steps", [])
        final_answer = question.get("final_answer", "")
        
        # Parse student's steps
        student_steps = self._parse_student_steps(student_answer)
        
        total_points = sum(step.get("points", 1) for step in steps)
        earned_points = 0
        step_results = []
        
        for i, expected_step in enumerate(steps):
            if i < len(student_steps):
                student_step = student_steps[i]
                step_correct = self._compare_step(
                    student_step,
                    expected_step["expected"]
                )
                if step_correct:
                    earned_points += expected_step.get("points", 1)
            else:
                step_correct = False
                student_step = ""
            
            step_results.append({
                "step_number": i + 1,
                "description": expected_step["description"],
                "correct": step_correct,
                "student_answer": student_step,
                "points": expected_step.get("points", 1)
            })
        
        # Check final answer
        final_correct = self._compare_answers(
            student_steps[-1] if student_steps else "",
            final_answer
        )
        
        score = earned_points / max(total_points, 1)
        is_correct = score >= 0.9 and final_correct
        
        result = {
            "score": score,
            "max_score": 1,
            "is_correct": is_correct,
            "points_earned": earned_points,
            "points_total": total_points,
            "final_answer_correct": final_correct,
        }
        
        if is_correct:
            result["feedback"] = "Excellent! All steps are correct."
        else:
            incorrect_steps = [r for r in step_results if not r["correct"]]
            
            if mode == GradingMode.PRACTICE:
                result["feedback"] = f"Scored {earned_points}/{total_points} points."
                result["step_results"] = step_results
                result["expected_steps"] = [
                    {"step": i+1, "expected": s["expected"]}
                    for i, s in enumerate(steps)
                ]
                result["final_answer"] = final_answer
            else:
                result["feedback"] = f"Scored {earned_points}/{total_points} points."
                if incorrect_steps:
                    first_wrong = incorrect_steps[0]
                    result["hints"] = [
                        f"Review Step {first_wrong['step_number']}: {first_wrong['description']}"
                    ]
        
        return result
    
    def _validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python code syntax."""
        try:
            ast.parse(code)
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Line {e.lineno}: {e.msg}"
            }
    
    def _run_test_case(
        self,
        code: str,
        function_name: str,
        inputs: List[Any],
        expected: Any
    ) -> Dict[str, Any]:
        """Run a single test case safely."""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                # Write the student's code
                f.write(code)
                f.write("\n\n")
                
                # Write test execution
                f.write(f"result = {function_name}(*{inputs})\n")
                f.write(f"print(repr(result))\n")
                
                temp_file = f.name
            
            # Run with timeout
            result = subprocess.run(
                ["python3", temp_file],
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return {
                    "passed": False,
                    "input": inputs,
                    "expected": expected,
                    "error": result.stderr.strip()
                }
            
            # Parse output
            actual = eval(result.stdout.strip())
            passed = actual == expected
            
            return {
                "passed": passed,
                "input": inputs,
                "expected": expected,
                "actual": actual
            }
            
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "input": inputs,
                "expected": expected,
                "error": "Timeout: Code took too long to execute"
            }
        except Exception as e:
            return {
                "passed": False,
                "input": inputs,
                "expected": expected,
                "error": str(e)
            }
    
    def _generate_mcq_hints(
        self,
        question: Dict[str, Any],
        wrong_answer: str
    ) -> List[str]:
        """Generate hints for incorrect MCQ answer."""
        hints = []
        
        # Generic hint based on topic
        if question.get("topic"):
            hints.append(f"Review the section on {question['topic']}.")
        
        # Hint about common misconception
        if question.get("common_mistakes", {}).get(wrong_answer):
            hints.append(question["common_mistakes"][wrong_answer])
        
        if not hints:
            hints.append("Re-read the question carefully and consider all options.")
        
        return hints
    
    def _generate_code_hints(
        self,
        failed_tests: List[Dict],
        question: Dict[str, Any]
    ) -> List[str]:
        """Generate hints for failed code tests."""
        hints = []
        
        if not failed_tests:
            return hints
        
        first_fail = failed_tests[0]
        
        if "error" in first_fail:
            error = first_fail["error"]
            if "NameError" in error:
                hints.append("Check if all variables are defined before use.")
            elif "TypeError" in error:
                hints.append("Check the types of your variables and function arguments.")
            elif "IndexError" in error:
                hints.append("Check your list/array indexing - you might be going out of bounds.")
            elif "Timeout" in error:
                hints.append("Your code might have an infinite loop. Check your loop conditions.")
            else:
                hints.append("Your code has a runtime error. Check the logic carefully.")
        else:
            # Wrong output
            hints.append("Your function returns incorrect values for some inputs.")
            hints.append("Consider edge cases like empty inputs or zero values.")
        
        return hints
    
    def _parse_student_steps(self, answer: str) -> List[str]:
        """Parse student's step-by-step answer into individual steps."""
        # Try to split by common step indicators
        patterns = [
            r'(?:Step\s*\d+[:\.]?\s*)',
            r'(?:\d+[:\.\)]\s*)',
            r'(?:\n\s*[-•]\s*)',
        ]
        
        for pattern in patterns:
            parts = re.split(pattern, answer, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) > 1:
                return parts
        
        # Fall back to line splitting
        lines = [l.strip() for l in answer.split('\n') if l.strip()]
        return lines if lines else [answer]
    
    def _compare_step(self, student: str, expected: str) -> bool:
        """Compare a student's step with expected."""
        # Normalize both
        student_norm = self._normalize_math(student.lower())
        expected_norm = self._normalize_math(expected.lower())
        
        # Check for key components
        return student_norm == expected_norm or expected_norm in student_norm
    
    def _compare_answers(self, student: str, expected: str) -> bool:
        """Compare final answers."""
        student_norm = self._normalize_math(student)
        expected_norm = self._normalize_math(expected)
        
        return student_norm == expected_norm
    
    def _normalize_math(self, text: str) -> str:
        """Normalize mathematical expressions for comparison."""
        # Remove whitespace
        text = re.sub(r'\s+', '', text)
        # Normalize common variations
        text = text.replace('×', '*').replace('÷', '/')
        text = text.replace('^', '**')
        return text.lower()
