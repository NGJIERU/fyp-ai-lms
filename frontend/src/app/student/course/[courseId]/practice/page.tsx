"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";
import PracticeHistory from "@/components/dashboard/PracticeHistory";

// Simple Chart Component (since we don't have recharts installed, using CSS bars)
function WeakTopicsChart({ topics }: { topics: any[] }) {
    if (!topics.length) return <p className="text-gray-500">No data available.</p>;

    return (
        <div className="space-y-4">
            {topics.map((t) => (
                <div key={t.week_number} className="space-y-1">
                    <div className="flex justify-between text-sm">
                        <span className="font-medium text-gray-700">{t.topic}</span>
                        <span className="text-gray-500">{t.score.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                        <div
                            className={`h-full rounded-full ${t.score < 60 ? "bg-red-500" : "bg-yellow-500"}`}
                            style={{ width: `${t.score}%` }}
                        />
                    </div>
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

    useEffect(() => {
        if (!authorized || !courseId || isNaN(courseId)) return;

        // Fetch weak topics/stats
        apiFetch(`/api/v1/tutor/weak-topics?course_id=${courseId}`)
            .then(data => setStats(data))
            .catch(err => console.error("Failed to load stats", err));
    }, [authorized, courseId]);

    if (authLoading) return null;

    return (
        <div className="min-h-screen bg-gray-50 px-4 py-10">
            <div className="mx-auto flex max-w-5xl flex-col gap-6">
                <div className="flex flex-col gap-2">
                    <Link href={`/student/course/${courseId}`} className="text-sm font-medium text-indigo-600">
                        ← Back to Course
                    </Link>
                    <h1 className="text-3xl font-semibold text-gray-900">Practice Dashboard</h1>
                    <p className="text-gray-500">Track your progress and mastery over time.</p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    <section className="rounded-2xl bg-white p-6 shadow-sm">
                        <h2 className="mb-4 text-lg font-semibold text-gray-900">Weak Topics Analysis</h2>
                        <div className="min-h-[200px]">
                            {stats ? <WeakTopicsChart topics={stats.weak_topics} /> : <p>Loading...</p>}
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
                    <PracticeHistory courseId={courseId} />
                </section>
            </div>
        </div>
    );
}
