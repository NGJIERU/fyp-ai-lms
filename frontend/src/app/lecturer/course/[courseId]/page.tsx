"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";

type LecturerCourseStats = {
  course_id: number;
  course_code: string;
  course_name: string;
  enrolled_students: number;
  avg_class_score: number;
  materials_count: number;
  pending_approvals: number;
};

type Submission = {
  student_id: number;
  course_id: number;
  week_number: number;
  score: number;
  attempted_at?: string | null;
};

type LecturerDashboardResponse = {
  courses: LecturerCourseStats[];
  recent_submissions: Submission[];
};

type CourseDetail = {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  lecturer_id?: number | null;
  lecturer_name?: string | null;
  created_at: string;
  updated_at: string;
};

type StudentPerformanceItem = {
  student_id: number;
  student_name: string;
  email: string;
  average_score: number;
  weak_topics: string[];
  last_active?: string | null;
};

type WeekAnalytics = {
  week_number: number;
  topic: string;
  avg_score: number;
  attempts_count: number;
  common_mistakes: string[];
};

export default function LecturerCourseDetailPage() {
  const router = useRouter();
  const params = useParams<{ courseId: string }>();
  const courseId = Number(params?.courseId);
  const { loading: authLoading, authorized } = useRequireRole(["lecturer", "super_admin"]);

  const [course, setCourse] = useState<LecturerCourseStats | null>(null);
  const [courseDetail, setCourseDetail] = useState<CourseDetail | null>(null);
  const [weekAnalytics, setWeekAnalytics] = useState<WeekAnalytics[]>([]);
  const [students, setStudents] = useState<StudentPerformanceItem[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<"score" | "last_active">("score");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    if (authLoading) return;
    if (!authorized) return;
    if (!courseId || Number.isNaN(courseId)) {
      setError("Invalid course");
      setIsLoading(false);
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    const controller = new AbortController();

    async function loadCourseData() {
      try {
        const [dashboardRes, analyticsRes, studentsRes, detailRes] = await Promise.all([
          apiFetch<LecturerDashboardResponse>("/api/v1/dashboard/lecturer", {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          }),
          apiFetch<WeekAnalytics[]>(`/api/v1/dashboard/lecturer/course/${courseId}/analytics`, {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          }),
          apiFetch<StudentPerformanceItem[]>(`/api/v1/dashboard/lecturer/course/${courseId}/students`, {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          }),
          apiFetch<CourseDetail>(`/api/v1/courses/${courseId}`, {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          }),
        ]);

        const selectedCourse = dashboardRes.courses.find((c) => c.course_id === courseId) || null;
        if (!selectedCourse) {
          setError("Course not found or not assigned to you");
        } else {
          setCourse(selectedCourse);
          setCourseDetail(detailRes);
          setSubmissions(dashboardRes.recent_submissions.filter((s) => s.course_id === courseId));
          setWeekAnalytics(analyticsRes);
          setStudents(studentsRes);
        }
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err.message ?? "Unable to load course analytics");
      } finally {
        setIsLoading(false);
      }
    }

    loadCourseData();
    return () => controller.abort();
  }, [authLoading, authorized, courseId, router]);

  const highestWeek = useMemo(() => {
    if (weekAnalytics.length === 0) return null;
    return [...weekAnalytics].sort((a, b) => b.avg_score - a.avg_score)[0];
  }, [weekAnalytics]);

  const lowestWeek = useMemo(() => {
    if (weekAnalytics.length === 0) return null;
    return [...weekAnalytics].sort((a, b) => a.avg_score - b.avg_score)[0];
  }, [weekAnalytics]);

  const sortedStudents = useMemo(() => {
    const copy = [...students];
    return copy.sort((a, b) => {
      if (sortField === "score") {
        return sortOrder === "desc" ? b.average_score - a.average_score : a.average_score - b.average_score;
      }
      const aTime = a.last_active ? new Date(a.last_active).getTime() : 0;
      const bTime = b.last_active ? new Date(b.last_active).getTime() : 0;
      return sortOrder === "desc" ? bTime - aTime : aTime - bTime;
    });
  }, [students, sortField, sortOrder]);

  const syllablesCount = weekAnalytics.length;
  const createdDate = courseDetail ? new Date(courseDetail.created_at).toLocaleDateString() : null;
  const updatedDate = courseDetail ? new Date(courseDetail.updated_at).toLocaleDateString() : null;

  // State for email copy feedback
  const [emailCopied, setEmailCopied] = useState(false);

  // State for submission modal
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null);

  const handleEmailAll = useCallback(async () => {
    if (students.length === 0) return;
    const emails = students.map((s) => s.email).join(", "); // Space for readability in clipboard

    try {
      await navigator.clipboard.writeText(emails);
      setEmailCopied(true);
      setTimeout(() => setEmailCopied(false), 3000);
    } catch (err) {
      console.error("Failed to copy emails", err);
      // Fallback to mailto if clipboard fails
      const subject = encodeURIComponent(`${course?.course_code ?? "Course"} update`);
      const body = encodeURIComponent("Hello team,\n\nLet's discuss upcoming course updates.\n\n");
      window.location.href = `mailto:?bcc=${encodeURIComponent(emails)}&subject=${subject}&body=${body}`;
    }
  }, [students, course?.course_code]);

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Loading course analytics…</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-red-600">{error ?? "Course not found"}</p>
            <Link href="/lecturer/dashboard" className="mt-4 inline-flex text-sm font-medium text-indigo-600">
              ← Back to dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <div className="flex flex-col gap-2">
          <Link href="/lecturer/dashboard" className="text-sm font-medium text-indigo-600">
            ← Back to dashboard
          </Link>
          <p className="text-sm uppercase tracking-wide text-indigo-600">Course analytics</p>
          <h1 className="text-3xl font-semibold text-gray-900">
            {course.course_name}
            <span className="ml-3 rounded-full bg-indigo-100 px-3 py-1 text-sm font-medium text-indigo-700">
              {course.course_code}
            </span>
          </h1>
          <p className="text-sm text-gray-500">Deep dive into enrollment, performance, and submissions.</p>
        </div>

        {courseDetail && (
          <section className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-2">
              <h2 className="text-lg font-semibold text-gray-900">Course description</h2>
              <p className="mt-2 text-sm text-gray-600">
                {courseDetail.description || "No description provided for this course yet."}
              </p>
              <dl className="mt-4 grid gap-4 sm:grid-cols-2 text-sm text-gray-500">
                <div>
                  <dt className="uppercase tracking-wide text-xs text-gray-400">Lecturer</dt>
                  <dd className="mt-1 text-gray-900">{courseDetail.lecturer_name || "Unassigned"}</dd>
                </div>
                <div>
                  <dt className="uppercase tracking-wide text-xs text-gray-400">Created</dt>
                  <dd className="mt-1 text-gray-900">{createdDate ?? "—"}</dd>
                </div>
                <div>
                  <dt className="uppercase tracking-wide text-xs text-gray-400">Last updated</dt>
                  <dd className="mt-1 text-gray-900">{updatedDate ?? "—"}</dd>
                </div>
                <div>
                  <dt className="uppercase tracking-wide text-xs text-gray-400">Syllabus weeks</dt>
                  <dd className="mt-1 text-gray-900">{syllablesCount}</dd>
                </div>
              </dl>
            </div>
            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">Quick actions</h2>
              <div className="mt-4 space-y-3">
                <Link
                  href={`/lecturer/materials?course=${courseId}`}
                  className="flex items-center justify-between rounded-xl border border-gray-100 px-4 py-3 text-sm font-medium text-gray-700 hover:border-indigo-200"
                >
                  Review pending materials
                  <span className="text-indigo-600">→</span>
                </Link>
                <button
                  type="button"
                  onClick={handleEmailAll}
                  className="w-full rounded-xl border border-gray-100 px-4 py-3 text-left text-sm font-medium text-gray-700 hover:border-indigo-200 transition-colors"
                  disabled={students.length === 0}
                >
                  <div className="flex items-center justify-between">
                    <span>Message enrolled students</span>
                    {emailCopied && (
                      <span className="text-xs font-semibold text-green-600 animate-pulse">
                        ✓ Emails Copied!
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {emailCopied
                      ? "Paste them into your email client's BCC field."
                      : `Copies ${students.length || "all"} student emails to clipboard`
                    }
                  </p>
                </button>
              </div>
            </div>
          </section>
        )}

        <section className="grid gap-4 md:grid-cols-4">
          <DetailStat label="Enrolled students" value={course.enrolled_students} subtext="Currently active" />
          <DetailStat label="Average class score" value={`${course.avg_class_score.toFixed(1)}%`} subtext="Across all weeks" />
          <DetailStat label="Approved materials" value={course.materials_count} subtext="Live in this course" />
          <DetailStat
            label="Pending approvals"
            value={course.pending_approvals}
            subtext="Awaiting review"
            variant={course.pending_approvals > 0 ? "warning" : "default"}
          />
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Scores by week</h2>
              {highestWeek && lowestWeek && (
                <p className="text-xs text-gray-500">
                  Best week: {highestWeek.topic} ({highestWeek.avg_score.toFixed(1)}%) · Struggling: {lowestWeek.topic} ({lowestWeek.avg_score.toFixed(1)}%)
                </p>
              )}
            </div>
            <div className="mt-6 space-y-4">
              {weekAnalytics.length === 0 && (
                <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">No analytics yet. Encourage students to submit quizzes.</p>
              )}
              {weekAnalytics.map((week) => (
                <div key={week.week_number} className="rounded-xl border border-gray-100 p-4">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>
                      Week {week.week_number}: <span className="font-medium text-gray-900">{week.topic}</span>
                    </span>
                    <span className="font-semibold text-gray-900">{week.avg_score.toFixed(1)}%</span>
                  </div>
                  <div className="mt-3 h-3 rounded-full bg-gray-100">
                    <div
                      className="h-3 rounded-full bg-gradient-to-r from-indigo-500 to-indigo-600"
                      style={{ width: `${Math.min(Math.max(week.avg_score, 0), 100)}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-gray-500">{week.attempts_count} attempts logged</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Recent submissions</h2>
            <div className="mt-4 space-y-4">
              {submissions.length === 0 && (
                <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">No recent submissions for this course.</p>
              )}
              {submissions.map((submission, index) => (
                <button
                  key={`${submission.student_id}-${index}`}
                  onClick={() => setSelectedSubmission(submission)}
                  className="w-full text-left rounded-lg border border-gray-100 p-4 hover:bg-gray-50 hover:border-indigo-200 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-900 group-hover:text-indigo-700">Student #{submission.student_id}</p>
                    <span className="text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">View details →</span>
                  </div>
                  <p className="text-xs text-gray-500">Week {submission.week_number} · Score {submission.score?.toFixed(1) ?? "-"}%</p>
                  <p className="mt-1 text-xs text-gray-400">
                    {submission.attempted_at ? new Date(submission.attempted_at).toLocaleString() : "Timestamp unavailable"}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Submission Details Modal */}
        {selectedSubmission && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" onClick={() => setSelectedSubmission(null)}>
            <div
              className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl animate-in fade-in zoom-in duration-200"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Submission Details</h3>
                <button
                  onClick={() => setSelectedSubmission(null)}
                  className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div className="rounded-lg bg-gray-50 p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Student ID</p>
                      <p className="mt-1 font-semibold text-gray-900">#{selectedSubmission.student_id}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Week</p>
                      <p className="mt-1 font-semibold text-gray-900">{selectedSubmission.week_number}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Score</p>
                      <p className={`mt-1 font-semibold ${(selectedSubmission.score || 0) >= 70 ? "text-green-600" : "text-amber-600"
                        }`}>
                        {selectedSubmission.score?.toFixed(1) ?? "-"}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Submitted</p>
                      <p className="mt-1 text-gray-900">
                        {selectedSubmission.attempted_at
                          ? new Date(selectedSubmission.attempted_at).toLocaleDateString()
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => {
                      // Navigate to full student analytics usually
                      // For now just close or maybe link to student profile if we had one
                      setSelectedSubmission(null);
                    }}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Student performance</h2>
              <p className="text-sm text-gray-500">Track averages, weak topics, and last activity.</p>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Sort by</label>
              <div className="relative">
                <select
                  className="appearance-none rounded-md border border-gray-300 bg-white py-1.5 pl-3 pr-8 text-sm font-medium text-gray-700 shadow-sm hover:border-indigo-300 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  value={`${sortField}-${sortOrder}`}
                  onChange={(e) => {
                    const [field, order] = e.target.value.split("-");
                    setSortField(field as "score" | "last_active");
                    setSortOrder(order as "asc" | "desc");
                  }}
                >
                  <option value="score-desc">Highest score</option>
                  <option value="score-asc">Lowest score</option>
                  <option value="last_active-desc">Most recently active</option>
                  <option value="last_active-asc">Longest inactive</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Student</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Average score</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Weak topics</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Last active</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sortedStudents.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">
                      No students enrolled yet.
                    </td>
                  </tr>
                )}
                {sortedStudents.map((student) => (
                  <tr key={student.student_id} className="hover:bg-gray-50/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{student.student_name}</p>
                      <a href={`mailto:${student.email}`} className="text-xs text-indigo-600 hover:text-indigo-800 hover:underline">
                        {student.email}
                      </a>
                    </td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{student.average_score.toFixed(1)}%</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {student.weak_topics.length === 0 ? (
                        <span className="text-gray-400 text-xs italic">No weak topics identified</span>
                      ) : (
                        <ul className="list-disc space-y-1 pl-4 text-xs">
                          {student.weak_topics.map((topic) => (
                            <li key={topic}>{topic}</li>
                          ))}
                        </ul>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(student.last_active)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <a
                        href={`mailto:${student.email}`}
                        className="inline-flex items-center justify-center rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                      >
                        Message
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

function DetailStat({
  label,
  value,
  subtext,
  variant = "default",
}: {
  label: string;
  value: string | number;
  subtext: string;
  variant?: "default" | "warning";
}) {
  const textClass = variant === "warning" ? "text-amber-600" : "text-gray-900";
  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${textClass}`}>{value}</p>
      <p className="mt-2 text-xs text-gray-500">{subtext}</p>
    </div>
  );
}

function formatDate(dateString: string | null | undefined) {
  if (!dateString) return "No activity logged";
  // If the string doesn't end in Z and doesn't have an offset, treat it as UTC by appending Z.
  // This handles naive datetimes from the backend which are typically stored as UTC but sent without info.
  const dateToParse = (dateString.endsWith("Z") || /[+-]\d\d:?\d\d/.test(dateString))
    ? dateString
    : `${dateString}Z`;

  try {
    const date = new Date(dateToParse);
    // Use user's local timezone (browser default)
    return date.toLocaleString(undefined, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch (e) {
    return dateString;
  }
}
