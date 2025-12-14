"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";
import ChatInterface from "@/components/tutor/ChatInterface";

export default function StudentChatPage() {
    const router = useRouter();
    const params = useParams<{ courseId: string }>();
    const courseId = Number(params?.courseId);
    const { loading: authLoading, authorized } = useRequireRole(["student", "super_admin"]);
    const [courseName, setCourseName] = useState<string>("");

    useEffect(() => {
        if (authLoading) return;
        if (!authorized) return;

        // Quick fetch for course name context
        const token = localStorage.getItem("access_token");
        if (!token || !courseId) return;

        apiFetch<{ course_name: string }>(`/api/v1/dashboard/student/course/${courseId}`, {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(data => setCourseName(data.course_name))
            .catch(err => console.error("Failed to load course info", err));

    }, [authLoading, authorized, courseId, router]);

    if (authLoading) return null;

    return (
        <div className="flex h-screen flex-col bg-gray-50">
            <header className="flex items-center justify-between border-b bg-white px-6 py-4 shadow-sm">
                <div className="flex items-center gap-4">
                    <Link
                        href={`/student/course/${courseId}`}
                        className="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
                            <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                        </svg>
                        Back to {courseName || "Course"}
                    </Link>
                </div>
            </header>

            <main className="flex-1 overflow-hidden p-0 md:p-6">
                <div className="h-full mx-auto max-w-4xl overflow-hidden rounded-xl border border-gray-200 shadow-xl md:h-[calc(100vh-8rem)]">
                    <ChatInterface courseId={courseId} />
                </div>
            </main>
        </div>
    );
}
