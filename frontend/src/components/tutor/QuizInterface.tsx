import { useState } from "react";

export type Question = {
    question: string;
    type: string;
    options?: string[]; // For MCQs
    correct_answer?: string; // If we want to validate locally or show it
};

type QuizInterfaceProps = {
    question: Question;
    questionIndex: number;
    totalQuestions: number;
    onSubmitAnswer: (answer: string) => Promise<{ is_correct: boolean; feedback: string }>;
    onNext: () => void;
};

export default function QuizInterface({
    question,
    questionIndex,
    totalQuestions,
    onSubmitAnswer,
    onNext,
}: QuizInterfaceProps) {
    const [selectedOption, setSelectedOption] = useState<string>("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [feedback, setFeedback] = useState<{ is_correct: boolean; text: string } | null>(null);

    // If options are missing (e.g. mock mode sometimes acts up), generate generic ones or show error
    // For now, let's assume if it's "short_text" type or missing options, we treat as text input?
    // But our prompt asks for "practice questions" which might come back as just text list.
    // The backend mock generator we fixed returns a list of question STRINGS, not detailed objects with options.
    // We need to handle that.

    // If the backend returns simple text questions without options, we might need to use a text area.
    // Or, since this is "Practice", maybe we just show the question and a "Reveal Answer" button?
    // Re-reading implementation plan: "Multiple Choice selection" was proposed.
    // But the mock generator just returns text questions like "1. What is...".

    // Let's make it flexible:
    // If options exist -> MCQ
    // If no options -> Text Area for self-reflection / typing answer.

    const handleSubmit = async () => {
        if (!selectedOption.trim()) return;

        setIsSubmitting(true);
        try {
            const result = await onSubmitAnswer(selectedOption);
            setFeedback({ is_correct: result.is_correct, text: result.feedback });
        } catch (error) {
            console.error(error);
            setFeedback({ is_correct: false, text: "Error submitting answer." });
        } finally {
            setIsSubmitting(false);
        }
    };

    // Guard against undefined question
    if (!question) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="text-4xl mb-4">⏳</div>
                <p className="text-gray-600">Loading question...</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b pb-4">
                <span className="text-sm font-medium text-gray-500">
                    Question {questionIndex + 1} of {totalQuestions}
                </span>
                <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600">
                    Practice Mode
                </span>
            </div>

            {/* Question */}
            <div>
                <h3 className="text-xl font-semibold text-gray-900">{question.question}</h3>
            </div>

            {/* Answer Input */}
            <div className="space-y-4">
                {question.options ? (
                    <div className="grid gap-3">
                        {question.options.map((opt, idx) => (
                            <button
                                key={idx}
                                onClick={() => !feedback && setSelectedOption(opt)}
                                disabled={!!feedback || isSubmitting}
                                className={`flex items-center justify-between rounded-xl border p-4 text-left transition ${selectedOption === opt
                                        ? "border-indigo-600 bg-indigo-50 ring-1 ring-indigo-600 text-indigo-900"
                                        : "border-gray-200 hover:border-indigo-200 hover:bg-gray-50 text-gray-800"
                                    } ${feedback ? "cursor-default opacity-80" : ""}`}
                            >
                                <span className="font-medium">{opt}</span>
                            </button>
                        ))}
                    </div>
                ) : (
                    <textarea
                        value={selectedOption}
                        onChange={(e) => setSelectedOption(e.target.value)}
                        disabled={!!feedback || isSubmitting}
                        placeholder="Type your answer here..."
                        className="w-full rounded-xl border border-gray-200 p-4 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
                        rows={4}
                    />
                )}
            </div>

            {/* Feedback Area */}
            {feedback && (
                <div className={`rounded-xl border p-4 ${feedback.is_correct ? "bg-green-50 border-green-100" : "bg-amber-50 border-amber-100"}`}>
                    <div className="flex items-start gap-3">
                        <span className="mt-1 text-xl">{feedback.is_correct ? "✅" : "💡"}</span>
                        <div>
                            <p className={`font-semibold ${feedback.is_correct ? "text-green-800" : "text-amber-800"}`}>
                                {feedback.is_correct ? "Correct!" : "Feedback"}
                            </p>
                            <p className={`mt-1 text-sm ${feedback.is_correct ? "text-green-700" : "text-amber-700"}`}>
                                {feedback.text}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Actions */}
            <div className="flex justify-end pt-4">
                {!feedback ? (
                    <button
                        onClick={handleSubmit}
                        disabled={!selectedOption.trim() || isSubmitting}
                        className="rounded-xl bg-indigo-600 px-6 py-2.5 font-semibold text-white transition hover:bg-indigo-700 disabled:bg-indigo-300"
                    >
                        {isSubmitting ? "Checking..." : "Check Answer"}
                    </button>
                ) : (
                    <button
                        onClick={() => {
                            setFeedback(null);
                            setSelectedOption("");
                            onNext();
                        }}
                        className="rounded-xl bg-gray-900 px-6 py-2.5 font-semibold text-white transition hover:bg-gray-800"
                    >
                        {questionIndex + 1 === totalQuestions ? "Finish Quiz" : "Next Question →"}
                    </button>
                )}
            </div>
        </div>
    );
}
