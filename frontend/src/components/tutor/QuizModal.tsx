import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import QuizInterface, { Question } from "./QuizInterface";

type QuizModalProps = {
    courseId: number;
    isOpen: boolean;
    onClose: () => void;
    initialTopic?: string;
    initialWeek?: number;
};

export default function QuizModal({
    courseId,
    isOpen,
    onClose,
    initialTopic,
    initialWeek,
}: QuizModalProps) {
    const [questions, setQuestions] = useState<Question[]>([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [completed, setCompleted] = useState(false);

    // Custom topic input state
    const [customTopic, setCustomTopic] = useState(initialTopic || "");
    const [selectedWeek, setSelectedWeek] = useState(initialWeek || 1);
    const [hasStarted, setHasStarted] = useState(false);
    const [correctCount, setCorrectCount] = useState(0);

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setQuestions([]);
            setCurrentQuestionIndex(0);
            setCompleted(false);
            setHasStarted(false);
            setCorrectCount(0);
            setCustomTopic(initialTopic || "");
            setSelectedWeek(initialWeek || 1);
            setError(null);
        }
    }, [isOpen, initialTopic, initialWeek]);

    const startQuiz = async () => {
        setLoading(true);
        setError(null);

        try {
            // 1. Generate Questions
            const data = await apiFetch<any>(`/api/v1/tutor/generate-questions?course_id=${courseId}`, {
                method: "POST",
                body: JSON.stringify({
                    week_number: selectedWeek,
                    num_questions: 5,
                    difficulty: "medium",
                    // Note: Backend might ignore topic if we just send week_number, 
                    // or we might need to modify backend to accept topic override.
                    // For now, let's rely on week_number as per API spec.
                }),
            });

            // 2. Parse questions - normalize options from dict to array
            const parsedQuestions: Question[] = data.questions.map((q: any) => {
                let normalizedOptions: string[] | undefined = undefined;
                
                if (q.options) {
                    if (Array.isArray(q.options)) {
                        normalizedOptions = q.options;
                    } else if (typeof q.options === 'object') {
                        // Convert dict {"A": "text", "B": "text"} to array ["A. text", "B. text"]
                        normalizedOptions = Object.entries(q.options)
                            .sort(([a], [b]) => a.localeCompare(b))
                            .map(([key, value]) => `${key}. ${value}`);
                    }
                }
                
                return {
                    question: q.question,
                    type: normalizedOptions ? "mcq" : (q.type || "short_text"),
                    options: normalizedOptions,
                    correct_answer: q.correct_answer,
                };
            });

            setQuestions(parsedQuestions);
            setHasStarted(true);
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Failed to generate quiz. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleAnswerSubmit = async (answer: string) => {
        const currentQ = questions[currentQuestionIndex];

        // Call check-answer endpoint
        const result = await apiFetch<any>("/api/v1/tutor/check-answer", {
            method: "POST",
            body: JSON.stringify({
                question_type: currentQ.type || "short_text",
                question: {
                    question: currentQ.question,
                    correct_answer: currentQ.correct_answer // If available, passing it back helps mock checker
                },
                student_answer: answer,
                mode: "practice",
                course_id: courseId,
                week_number: selectedWeek
            }),
        });

        if (result.is_correct) {
            setCorrectCount((prev) => prev + 1);
        }

        return {
            is_correct: result.is_correct,
            feedback: result.feedback || result.explanation || "No feedback provided."
        };
    };

    const handleNext = () => {
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex((prev) => prev + 1);
        } else {
            setCompleted(true);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <div className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-xl">
                {/* Header */}
                <div className="flex items-center justify-between border-b px-6 py-4">
                    <h2 className="text-lg font-semibold text-gray-900">
                        {completed ? "Quiz Results" : hasStarted ? "Practice Quiz" : "New Practice Session"}
                    </h2>
                    <button onClick={onClose} className="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
                        ✕
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {error && (
                        <div className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-600">
                            {error}
                        </div>
                    )}

                    {!hasStarted ? (
                        <div className="space-y-6">
                            <div>
                                <label className="mb-2 block text-sm font-medium text-gray-700">Select Week / Topic</label>
                                <select
                                    value={selectedWeek}
                                    onChange={(e) => setSelectedWeek(Number(e.target.value))}
                                    className="w-full rounded-xl border border-gray-300 p-3"
                                >
                                    {Array.from({ length: 14 }, (_, i) => i + 1).map((w) => (
                                        <option key={w} value={w}>
                                            Week {w}
                                        </option>
                                    ))}
                                </select>
                                <p className="mt-2 text-xs text-gray-500">
                                    The AI Tutor will generate unique questions for this week's material.
                                </p>
                            </div>

                            <div className="flex justify-end pt-4">
                                <button
                                    onClick={startQuiz}
                                    disabled={loading}
                                    className="rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:bg-indigo-400"
                                >
                                    {loading ? "Generating Questions..." : "Start Practice Session →"}
                                </button>
                            </div>
                        </div>
                    ) : completed ? (
                        <div className="text-center py-8">
                            <div className="mb-4 text-5xl">🎉</div>
                            <h3 className="text-2xl font-bold text-gray-900">Session Complete!</h3>
                            <p className="mt-2 text-gray-600">
                                You got <span className="font-bold text-indigo-600">{correctCount}</span> out of <span className="font-bold">{questions.length}</span> correct.
                            </p>
                            <div className="mt-8 flex justify-center gap-3">
                                <button
                                    onClick={onClose}
                                    className="rounded-xl border border-gray-300 px-6 py-2.5 font-medium text-gray-700 hover:bg-gray-50"
                                >
                                    Close
                                </button>
                                <button
                                    onClick={() => {
                                        setHasStarted(false);
                                        setCompleted(false);
                                    }}
                                    className="rounded-xl bg-indigo-600 px-6 py-2.5 font-medium text-white hover:bg-indigo-700"
                                >
                                    Start New Session
                                </button>
                            </div>
                        </div>
                    ) : (
                        <QuizInterface
                            question={questions[currentQuestionIndex]}
                            questionIndex={currentQuestionIndex}
                            totalQuestions={questions.length}
                            onSubmitAnswer={handleAnswerSubmit}
                            onNext={handleNext}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
