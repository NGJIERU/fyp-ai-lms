"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";
import { AdminLayout } from "@/components/admin/AdminLayout";

type Course = {
    id: number;
    code: string;
    name: string;
    enrolled_students: number;
    lecturer_name: string | null;
    lecturer_id: number | null;
    is_active: boolean;
};

type User = {
    id: number;
    full_name: string;
    email: string;
};

export default function AdminCoursesPage() {
    const { loading: authLoading, authorized } = useRequireRole(["super_admin"]);
    const [courses, setCourses] = useState<Course[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [assignModalOpen, setAssignModalOpen] = useState(false);
    const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
    const [lecturers, setLecturers] = useState<User[]>([]);
    const [selectedLecturerId, setSelectedLecturerId] = useState<number | string>("");
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (authLoading) return;
        if (!authorized) return;
        const token = localStorage.getItem("access_token");
        if (!token) return;

        async function loadData() {
            try {
                const res = await apiFetch<Course[]>("/api/v1/admin/courses/all", {
                    headers: { Authorization: `Bearer ${token}` },
                });
                setCourses(res);
            } catch (err: any) {
                setError(err.message ?? "Failed to load courses");
            } finally {
                setIsLoading(false);
            }
        }

        loadData();
    }, [authLoading, authorized]);

    // Fetch lecturers when modal opens
    useEffect(() => {
        if (!assignModalOpen) return;
        const token = localStorage.getItem("access_token");
        if (!token) return;

        async function loadLecturers() {
            try {
                const res = await apiFetch<User[]>("/api/v1/admin/users?role=lecturer", {
                    headers: { Authorization: `Bearer ${token}` },
                });
                setLecturers(res);
            } catch (err) {
                console.error("Failed to load lecturers", err);
            }
        }
        loadLecturers();
    }, [assignModalOpen]);

    function openAssignModal(course: Course) {
        setSelectedCourse(course);
        setSelectedLecturerId(course.lecturer_id || "");
        setAssignModalOpen(true);
    }

    async function handleAssign() {
        if (!selectedCourse) return;
        setSubmitting(true);
        const token = localStorage.getItem("access_token");
        try {
            await apiFetch(`/api/v1/admin/courses/${selectedCourse.id}/assign-lecturer?lecturer_id=${selectedLecturerId}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
            });

            // Update local state
            const lecturer = lecturers.find(l => l.id === Number(selectedLecturerId));
            setCourses(prev => prev.map(c =>
                c.id === selectedCourse.id
                    ? { ...c, lecturer_id: Number(selectedLecturerId), lecturer_name: lecturer?.full_name ?? "Unknown" }
                    : c
            ));

            setAssignModalOpen(false);
        } catch (err: any) {
            alert(err.message || "Failed to assign lecturer");
        } finally {
            setSubmitting(false);
        }
    }

    if (authLoading || isLoading) {
        return (
            <AdminLayout headerTitle="Course Management">
                <div className="rounded-xl bg-white p-6 shadow-sm">
                    <p className="text-sm text-gray-500">Loading courses...</p>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout headerTitle="Course Management" headerSubtitle="Manage courses and assign lecturers">
            <div className="rounded-2xl bg-white p-6 shadow-sm">
                {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

                <div className="overflow-hidden rounded-xl border border-gray-100">
                    <table className="min-w-full divide-y divide-gray-100 text-sm">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">Code</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">Name</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">Enrolled</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">Lecturer</th>
                                <th className="px-4 py-3 text-right font-semibold text-gray-700">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50 bg-white">
                            {courses.map((course) => (
                                <tr key={course.id}>
                                    <td className="px-4 py-3 font-medium text-gray-900">{course.code}</td>
                                    <td className="px-4 py-3 text-gray-600">{course.name}</td>
                                    <td className="px-4 py-3 text-gray-600">{course.enrolled_students}</td>
                                    <td className="px-4 py-3 text-gray-600">
                                        {course.lecturer_name ? (
                                            <span className="inline-flex items-center rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700">
                                                {course.lecturer_name}
                                            </span>
                                        ) : (
                                            <span className="text-xs italic text-gray-400">Unassigned</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <button
                                            className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                                            onClick={() => openAssignModal(course)}
                                        >
                                            Assign Lecturer
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {courses.length === 0 && (
                        <div className="p-8 text-center text-gray-500">No courses found.</div>
                    )}
                </div>
            </div>

            {assignModalOpen && selectedCourse && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
                    <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
                        <h3 className="text-lg font-semibold text-gray-900">
                            Assign Lecturer to {selectedCourse.code}
                        </h3>

                        <div className="mt-4">
                            <label className="block text-sm font-medium text-gray-700">Select Lecturer</label>
                            <select
                                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                value={selectedLecturerId}
                                onChange={(e) => setSelectedLecturerId(e.target.value)}
                            >
                                <option value="">-- Select --</option>
                                {lecturers.map(l => (
                                    <option key={l.id} value={l.id}>
                                        {l.full_name} ({l.email})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="mt-6 flex justify-end gap-3">
                            <button
                                className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                                onClick={() => setAssignModalOpen(false)}
                            >
                                Cancel
                            </button>
                            <button
                                disabled={submitting || !selectedLecturerId}
                                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-60"
                                onClick={handleAssign}
                            >
                                {submitting ? "Saving..." : "Save Assignment"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </AdminLayout>
    );
}
