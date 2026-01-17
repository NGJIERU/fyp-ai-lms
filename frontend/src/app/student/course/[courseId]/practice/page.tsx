"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";
import PracticeHistory from "@/components/dashboard/PracticeHistory";

import QuizModal from "@/components/tutor/QuizModal";

// Topic Performance Chart - shows all practiced topics with color-coded scores
function TopicPerformanceChart({ topics }: { topics: any[] }) {
    if (!topics.length) return (
        <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="text-4xl mb-3">📝</div>
            <p className="text-gray-500">No practice data yet.</p>
            <p className="text-xs text-gray-400 mt-1">Complete a quiz to see your performance!</p>
        </div>
    );

    return (
        <div className="space-y-4">
            {topics.map((t) => (
                <div key={t.week_number} className="space-y-1">
                    <div className="flex justify-between text-sm">
                        <span className="font-medium text-gray-700">{t.topic}</span>
                        <span className={`font-medium ${t.score >= 70 ? "text-green-600" : t.score >= 50 ? "text-yellow-600" : "text-red-600"}`}>
                            {t.score.toFixed(0)}%
                        </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                        <div
                            className={`h-full rounded-full ${t.score >= 70 ? "bg-green-500" : t.score >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                            style={{ width: `${Math.min(t.score, 100)}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-400">{t.attempts} attempt{t.attempts !== 1 ? 's' : ''}</p>
                </div>
            ))}
        </div>
    );
}

export default function PracticeDashboardPage() {
    const params = useParams<{ courseId: string }>();
    const courseId = Number(params?.courseId);
    const { loading: authLoading, authorized } = useRequireRole(["student"]);
    const [stats, setStats] = useState<any>(null);
    const [isQuizOpen, setIsQuizOpen] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);

    useEffect(() => {
        if (!authorized || !courseId || isNaN(courseId)) return;

        // Fetch weak topics/stats
        apiFetch(`/api/v1/tutor/weak-topics?course_id=${courseId}`)
            .then(data => setStats(data))
            .catch(err => console.error("Failed to load stats", err));
    }, [authorized, courseId, refreshKey]); // Refetch when refreshKey updates

    if (authLoading) return null;

    const handleQuizClose = () => {
        setIsQuizOpen(false);
        setRefreshKey(prev => prev + 1); // Trigger data refresh
    };

    return (
        <div className="min-h-screen bg-gray-50 px-4 py-10">
            <div className="mx-auto flex max-w-5xl flex-col gap-6">
                <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex flex-col gap-2">
                        <Link href={`/student/course/${courseId}`} className="text-sm font-medium text-indigo-600">
                            ← Back to Course
                        </Link>
                        <h1 className="text-3xl font-semibold text-gray-900">Practice Dashboard</h1>
                        <p className="text-gray-500">Track your progress and mastery over time.</p>
                    </div>
                    <button
                        onClick={() => setIsQuizOpen(true)}
                        className="rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 hover:shadow-indigo-300"
                    >
                        Start Practice Session
                    </button>
                </header>

                <div className="grid gap-6 md:grid-cols-2">
                    <section className="rounded-2xl bg-white p-6 shadow-sm">
                        <h2 className="mb-4 text-lg font-semibold text-gray-900">Topic Performance</h2>
                        <div className="min-h-[200px]">
                            {stats ? <TopicPerformanceChart topics={stats.weak_topics} /> : <p>Loading...</p>}
                        </div>
                    </section>

                    <section className="rounded-2xl bg-white p-6 shadow-sm">
                        <h2 className="mb-4 text-lg font-semibold text-gray-900">Recommendations</h2>
                        {stats && stats.recommendations.length > 0 ? (
                            <ul className="space-y-2">
                                {stats.recommendations.map((rec: string, i: number) => (
                                    <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                                        <span className="text-indigo-500">📚</span> {rec}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-sm text-gray-500">Keep practicing to generate recommendations!</p>
                        )}
                    </section>
                </div>

                <section>
                    <PracticeHistory key={refreshKey} courseId={courseId} />
                </section>
            </div>

            <QuizModal
                courseId={courseId}
                isOpen={isQuizOpen}
                onClose={handleQuizClose}
            />
        </div>
    );
}
