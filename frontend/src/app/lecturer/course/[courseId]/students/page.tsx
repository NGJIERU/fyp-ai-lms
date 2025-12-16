"use client";

import { useState, FormEvent, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";

type StudentPerformanceItem = {
    student_id: number;
    student_name: string;
    email: string;
    average_score: number;
    weak_topics: string[];
    last_active?: string | null;
};

export default function CourseStudentsPage() {
    const router = useRouter();
    const params = useParams<{ courseId: string }>();
    const courseId = Number(params?.courseId);
    const { loading: authLoading, authorized } = useRequireRole(["lecturer", "super_admin"]);

    const [students, setStudents] = useState<StudentPerformanceItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [isEnrolling, setIsEnrolling] = useState(false);
    const [enrollEmail, setEnrollEmail] = useState("");
    const [enrollError, setEnrollError] = useState<string | null>(null);
    const [enrollSuccess, setEnrollSuccess] = useState<string | null>(null);

    useEffect(() => {
        if (authLoading || !authorized) return;
        if (!courseId) return;

        loadStudents();
    }, [authLoading, authorized, courseId]);

    const loadStudents = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem("access_token");
            const data = await apiFetch<StudentPerformanceItem[]>(`/api/v1/dashboard/lecturer/course/${courseId}/students`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setStudents(data);
            setError(null);
        } catch (err: any) {
            setError(err.message || "Failed to load students");
        } finally {
            setLoading(false);
        }
    };

    const handleEnroll = async (e: FormEvent) => {
        e.preventDefault();
        if (!enrollEmail) return;

        setIsEnrolling(true);
        setEnrollError(null);
        setEnrollSuccess(null);

        try {
            const token = localStorage.getItem("access_token");
            await apiFetch(`/api/v1/courses/${courseId}/students`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email: enrollEmail }),
            });
            setEnrollSuccess(`Successfully enrolled ${enrollEmail}`);
            setEnrollEmail("");
            loadStudents(); // Reload list
        } catch (err: any) {
            setEnrollError(err.message || "Failed to enroll student. Ensure email is correct.");
        } finally {
            setIsEnrolling(false);
        }
    };

    const handleRemove = async (studentId: number) => {
        if (!confirm("Are you sure you want to remove this student from the course?")) return;

        try {
            const token = localStorage.getItem("access_token");
            await apiFetch(`/api/v1/courses/${courseId}/students/${studentId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
            });
            // Optimistic update
            setStudents(prev => prev.filter(s => s.student_id !== studentId));
        } catch (err: any) {
            alert(err.message || "Failed to remove student");
        }
    };

    if (authLoading || loading && students.length === 0) {
        return <div className="p-10 text-center text-gray-500">Loading students...</div>;
    }

    if (!authorized) return null;

    return (
        <div className="min-h-screen bg-gray-50 px-4 py-10">
            <div className="mx-auto max-w-5xl">
                <Link href={`/lecturer/course/${courseId}`} className="mb-6 inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-800">
                    ← Back to Course Analytics
                </Link>

                <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Manage Students</h1>
                        <p className="text-sm text-gray-500 mt-1">Add or remove students for this course.</p>
                    </div>
                </div>

                {/* Enroll Section */}
                <div className="mb-8 rounded-xl bg-white p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Enroll New Student</h2>
                    <form onSubmit={handleEnroll} className="flex flex-col sm:flex-row gap-3 items-start">
                        <div className="w-full sm:max-w-md">
                            <input
                                type="email"
                                required
                                placeholder="Enter student email address"
                                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                value={enrollEmail}
                                onChange={(e) => setEnrollEmail(e.target.value)}
                            />
                            {enrollError && <p className="mt-1 text-sm text-red-600">{enrollError}</p>}
                            {enrollSuccess && <p className="mt-1 text-sm text-green-600">{enrollSuccess}</p>}
                        </div>
                        <button
                            type="submit"
                            disabled={isEnrolling}
                            className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors"
                        >
                            {isEnrolling ? "Enrolling..." : "Enroll Student"}
                        </button>
                    </form>
                </div>

                {/* Student List */}
                <div className="rounded-xl bg-white shadow-sm overflow-hidden border border-gray-100">
                    <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                        <h2 className="font-semibold text-gray-900">Enrolled Students ({students.length})</h2>
                    </div>

                    {students.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">
                            No students enrolled yet. Use the form above to add someone.
                        </div>
                    ) : (
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {students.map(student => (
                                    <tr key={student.student_id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {student.student_name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {student.email}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            Avg Score: <span className="font-medium text-gray-900">{student.average_score.toFixed(1)}%</span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button
                                                onClick={() => handleRemove(student.student_id)}
                                                className="text-red-600 hover:text-red-900 hover:bg-red-50 px-3 py-1 rounded transition-colors"
                                            >
                                                Remove
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}
