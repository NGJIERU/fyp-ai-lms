"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type QuizAttempt = {
    id: number;
    week_number: number;
    score: number;
    max_score: number;
    is_correct: boolean;
    attempted_at: string;
    question_type: string;
    question_preview: string;
};

export default function PracticeHistory({ courseId }: { courseId: number }) {
    const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiFetch<QuizAttempt[]>(`/api/v1/tutor/practice/history?course_id=${courseId}`)
            .then((data) => setAttempts(data))
            .catch((err) => console.error("Failed to load history", err))
            .finally(() => setLoading(false));
    }, [courseId]);

    if (loading) return <div className="text-center py-4 text-gray-500">Loading history...</div>;

    if (attempts.length === 0) {
        return (
            <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center">
                <p className="text-gray-500">No practice attempts yet.</p>
                <p className="text-sm text-gray-400">Try generating a quiz!</p>
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-100 bg-gray-50 px-6 py-4">
                <h3 className="font-semibold text-gray-900">Recent Practice</h3>
            </div>
            <div className="divide-y divide-gray-100">
                {attempts.map((attempt) => (
                    <div key={attempt.id} className="flex items-center justify-between p-4 hover:bg-gray-50">
                        <div>
                            <p className="font-medium text-gray-900">{attempt.question_preview}</p>
                            <p className="text-xs text-gray-500">
                                Week {attempt.week_number} • {new Date(attempt.attempted_at).toLocaleDateString()}
                            </p>
                        </div>
                        <div className="flex items-center gap-3">
                            <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${attempt.is_correct
                                    ? "bg-green-100 text-green-800"
                                    : "bg-red-100 text-red-800"
                                    }`}
                            >
                                {attempt.is_correct ? "Correct" : "Incorrect"}
                            </span>
                            <span className="text-sm font-semibold text-gray-700">
                                {attempt.score}/{attempt.max_score}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
