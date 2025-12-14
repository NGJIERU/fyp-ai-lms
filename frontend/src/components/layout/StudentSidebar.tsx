"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { apiFetch } from "@/lib/api";

type EnrolledCourse = {
    course_id: number;
    code: string;
    name: string;
    weak_topics_count: number;
};

type StudentDashboardData = {
    enrolled_courses: EnrolledCourse[];
};

export default function StudentSidebar() {
    const pathname = usePathname();
    const [isOpen, setIsOpen] = useState(false);
    const [courses, setCourses] = useState<EnrolledCourse[]>([]);
    const [loading, setLoading] = useState(true);

    // Close sidebar on route change (mobile)
    useEffect(() => {
        setIsOpen(false);
    }, [pathname]);

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                const token = localStorage.getItem("access_token");
                if (!token) return;

                // We reuse the dashboard endpoint to get enrolled courses
                const data = await apiFetch<StudentDashboardData>("/api/v1/dashboard/student", {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setCourses(data.enrolled_courses || []);
            } catch (err) {
                console.error("Failed to load sidebar courses", err);
            } finally {
                setLoading(false);
            }
        };

        fetchCourses();
    }, []);

    // Derive current course ID from URL
    const courseIdMatch = pathname.match(/\/student\/course\/(\d+)/);
    const currentCourseId = courseIdMatch ? parseInt(courseIdMatch[1]) : null;

    // Determine target course ID: Current > First Enrolled > Null
    const targetCourseId = currentCourseId || (courses.length > 0 ? courses[0].course_id : null);

    const navItems = [
        {
            name: "Dashboard",
            href: "/student/dashboard",
            icon: "📊",
            disabled: false
        },
        {
            name: "AI Tutor",
            href: targetCourseId ? `/student/course/${targetCourseId}/chat` : "#",
            icon: "🤖",
            disabled: !targetCourseId // Disable if no course context and no enrolled courses
        },
        {
            name: "Practice",
            href: targetCourseId ? `/student/course/${targetCourseId}/practice` : "#",
            icon: "📝",
            disabled: !targetCourseId
        },
    ];

    return (
        <>
            {/* Mobile Top Bar */}
            <div className="flex h-16 items-center justify-between border-b bg-white px-4 md:hidden">
                <span className="text-xl font-bold text-indigo-600">LMS Student</span>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="rounded p-2 text-gray-600 hover:bg-gray-100"
                >
                    <span className="text-2xl">☰</span>
                </button>
            </div>

            {/* Sidebar Overlay (Mobile) */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 md:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar Container */}
            <aside
                className={`fixed inset-y-0 left-0 z-50 w-64 transform border-r bg-white transition-transform md:translate-x-0 ${isOpen ? "translate-x-0" : "-translate-x-full"
                    } md:static md:block`}
            >
                <div className="flex h-full flex-col">
                    {/* Logo Area (Desktop) */}
                    <div className="hidden h-16 items-center border-b px-6 md:flex">
                        <span className="text-xl font-bold text-indigo-600">LMS Student</span>
                    </div>

                    {/* Navigation */}
                    <div className="flex-1 overflow-y-auto px-4 py-6">
                        <nav className="space-y-1">
                            {navItems.map((item) => {
                                const isActive = pathname === item.href;
                                const isDisabled = item.disabled;

                                if (isDisabled) {
                                    return (
                                        <div
                                            key={item.name}
                                            className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-400"
                                            title="Select a course first"
                                        >
                                            <span>{item.icon}</span>
                                            {item.name}
                                        </div>
                                    );
                                }

                                return (
                                    <Link
                                        key={item.name}
                                        href={item.href}
                                        className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive
                                                ? "bg-indigo-50 text-indigo-700"
                                                : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                                            }`}
                                    >
                                        <span>{item.icon}</span>
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </nav>

                        {/* Quick Access Section */}
                        <div className="mt-8">
                            <h3 className="mb-3 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                                Quick Access
                            </h3>
                            {loading ? (
                                <div className="px-3 text-xs text-gray-400">Loading courses...</div>
                            ) : courses.length === 0 ? (
                                <div className="px-3 text-xs text-gray-400">No courses enrolled</div>
                            ) : (
                                <nav className="space-y-1">
                                    {courses.map((course) => {
                                        const isActive = pathname.startsWith(`/student/course/${course.course_id}`);
                                        return (
                                            <Link
                                                key={course.course_id}
                                                href={`/student/course/${course.course_id}`}
                                                className={`group flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive
                                                    ? "bg-indigo-50 text-indigo-700"
                                                    : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                                                    }`}
                                            >
                                                <span className="truncate">{course.code}</span>
                                                {course.weak_topics_count > 0 && (
                                                    <span className="ml-2 inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                                                        {course.weak_topics_count}
                                                    </span>
                                                )}
                                            </Link>
                                        );
                                    })}
                                </nav>
                            )}
                        </div>
                    </div>

                    {/* User Profile / Logout Placeholder */}
                    <div className="border-t p-4">
                        <Link href="/login" onClick={() => localStorage.removeItem("access_token")} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50">
                            <span>🚪</span>
                            Sign Out
                        </Link>
                    </div>
                </div>
            </aside>
        </>
    );
}
