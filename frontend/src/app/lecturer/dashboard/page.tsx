"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

type LecturerCourseStats = {
  course_id: number;
  course_code: string;
  course_name: string;
  enrolled_students: number;
  at_risk_students: number;
  avg_class_score: number;
  materials_count: number;
  pending_approvals: number;
};

type Submission = {
  student_id: number;
  course_id: number;
  week_number: number;
  score: number;
  questions_answered?: number;
  attempted_at?: string | null;
};

type LecturerBundleMaterial = {
  id: number;
  title: string;
  url: string;
  source: string;
  type: string;
};

type LecturerBundleItem = {
  course_id: number;
  week_number: number;
  topic: string;
  summary: string;
  materials: LecturerBundleMaterial[];
};

type RatingInsightItem = {
  material_id: number;
  title: string;
  course_id: number;
  course_name?: string | null;
  average_rating: number;
  total_ratings: number;
  upvotes: number;
  downvotes: number;
};

type LecturerDashboardResponse = {
  lecturer_id: number;
  lecturer_name: string;
  courses: LecturerCourseStats[];
  total_students: number;
  pending_material_approvals: number;
  recent_submissions: Submission[];
  context_bundles: LecturerBundleItem[];
  rating_insights: RatingInsightItem[];
};

function getRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export default function LecturerDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<LecturerDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    const controller = new AbortController();

    async function loadDashboard() {
      try {
        const payload = await apiFetch<LecturerDashboardResponse>(
          "/api/v1/dashboard/lecturer",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
          }
        );
        setData(payload);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err.message ?? "Unable to load lecturer dashboard");
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
    return () => controller.abort();
  }, [router]);

  const totalCourses = data?.courses.length ?? 0;
  const totalAtRiskStudents = useMemo(() => {
    if (!data || data.courses.length === 0) return 0;
    return data.courses.reduce((sum, course) => sum + course.at_risk_students, 0);
  }, [data]);
  const avgClassScore = useMemo(() => {
    if (!data || data.courses.length === 0) return 0;
    const total = data.courses.reduce((sum, course) => sum + course.avg_class_score, 0);
    return Math.round((total / data.courses.length) * 10) / 10;
  }, [data]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Loading dashboard…</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const handleSignOut = () => {
    localStorage.removeItem("access_token");
    router.replace("/login");
  };



  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header>
          <div className="flex items-center justify-between">
            <p className="text-sm uppercase tracking-wide text-indigo-600">Lecturer Dashboard</p>
            <button
              onClick={handleSignOut}
              className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50 ring-1 ring-inset ring-gray-300"
            >
              Sign out
            </button>
          </div>
          <h1 className="mt-2 text-3xl font-semibold text-gray-900">
            Welcome back, {data.lecturer_name}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor course performance, student progress, and pending approvals.
          </p>
        </header>
        <div className="flex items-center justify-end gap-3 mb-4">
          <Link
            href="/lecturer/materials/upload"
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:bg-indigo-700"
          >
            <span>+</span> Add Material
          </Link>
        </div>
        <section className="grid gap-4 md:grid-cols-4">
          <SummaryCard label="Courses" value={totalCourses} subtext="Assigned to you" />
          <SummaryCard
            label="Active Enrollments"
            value={data.total_students}
            subtext="Total student-course pairs"
            tooltip="Count of active enrollments across all your courses (students may be counted multiple times)."
          />
          <SummaryCard
            label="Students needing help"
            value={totalAtRiskStudents}
            subtext="Scoring below 60%"
            variant={totalAtRiskStudents > 0 ? "warning" : undefined}
            tooltip="Students with average quiz scores below 60% who may need additional support."
          />
          <Link href="/lecturer/materials" className="block">
            <SummaryCard
              label="Pending approvals"
              value={data.pending_material_approvals}
              subtext="Click to review →"
              variant="warning"
            />
          </Link>
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Courses overview</h2>
            </div>
            <div className="mt-6 space-y-4">
              {data.courses.length === 0 && (
                <div className="rounded-lg bg-gradient-to-br from-indigo-50 to-purple-50 p-6 text-center">
                  <span className="text-3xl">📚</span>
                  <p className="mt-2 text-sm font-medium text-gray-700">No courses assigned yet</p>
                  <p className="mt-1 text-xs text-gray-500">Contact your administrator to get courses assigned to your account.</p>
                </div>
              )}
              {data.courses.map((course) => (
                <CourseRow key={course.course_id} course={course} />
              ))}
            </div>
          </section>

          <section className="flex flex-col gap-4 rounded-2xl bg-white p-6 shadow-sm">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Recent submissions</h2>
              <div className="mt-4 space-y-4">
                {data.recent_submissions.length === 0 && (
                  <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
                    No recent submissions.
                  </p>
                )}
                {data.recent_submissions.map((submission, index) => {
                  const score = submission.score ?? 0;
                  const questionsAnswered = submission.questions_answered ?? 1;
                  const scoreColor = score >= 70 ? "text-emerald-600 bg-emerald-50" : score >= 40 ? "text-amber-600 bg-amber-50" : "text-red-600 bg-red-50";
                  const scoreIcon = score >= 70 ? "✅" : score >= 40 ? "📊" : "📝";
                  const timeAgo = submission.attempted_at ? getRelativeTime(new Date(submission.attempted_at)) : "Unknown";
                  
                  return (
                    <div key={`${submission.student_id}-${index}`} className="flex items-center gap-4 rounded-xl border border-gray-100 p-4 hover:border-gray-200 hover:bg-gray-50 transition">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-full ${scoreColor}`}>
                        <span className="text-lg">{scoreIcon}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-gray-900 truncate">
                            Student #{submission.student_id}
                          </p>
                          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${scoreColor}`}>
                            {score.toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">
                          Week {submission.week_number} · {questionsAnswered} Q · {timeAgo}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <StudyBundlesSection bundles={data.context_bundles} courses={data.courses} />

            <div>
              <h2 className="text-lg font-semibold text-gray-900">Low-rated materials</h2>
              <p className="mt-1 text-sm text-gray-500">
                Resources students consistently downvote across your courses.
              </p>
              <div className="mt-4 space-y-3">
                {data.rating_insights.length === 0 && (
                  <div className="rounded-lg bg-emerald-50 p-4 text-center">
                    <span className="text-2xl">✨</span>
                    <p className="mt-1 text-xs font-medium text-emerald-700">All materials performing well!</p>
                    <p className="mt-1 text-xs text-emerald-600">No low-rated content to review.</p>
                  </div>
                )}
                {data.rating_insights.map((insight) => (
                  <div
                    key={insight.material_id}
                    className="rounded-lg border border-gray-100 p-3 text-xs"
                  >
                    <p className="font-semibold text-gray-900 truncate">{insight.title}</p>
                    <p className="text-gray-500">
                      {insight.course_name ?? `Course #${insight.course_id}`} · {insight.upvotes}↑ / {insight.downvotes}↓ ({
                        insight.total_ratings
                      }{" "}
                      ratings)
                    </p>
                    <p className="mt-1 text-[0.65rem] text-gray-400">
                      Avg rating: {insight.average_rating.toFixed(2)} (−1 to +1)
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  subtext,
  variant = "default",
  tooltip,
}: {
  label: string;
  value: string | number;
  subtext: string;
  variant?: "default" | "warning";
  tooltip?: string;
}) {
  const textClass = variant === "warning" ? "text-amber-600" : "text-gray-900";
  return (
    <div className="group relative rounded-2xl bg-white p-6 shadow-sm">
      <div className="flex items-center gap-1">
        <p className="text-sm text-gray-500">{label}</p>
        {tooltip && (
          <div className="group/tooltip relative flex h-4 w-4 cursor-help items-center justify-center rounded-full bg-gray-100 text-[10px] text-gray-500">
            ?
            <div className="absolute bottom-full left-1/2 mb-2 hidden w-48 -translate-x-1/2 rounded bg-gray-800 px-2 py-1 text-xs text-white shadow-lg group-hover/tooltip:block">
              {tooltip}
              <div className="absolute left-1/2 top-full -mt-1 h-2 w-2 -translate-x-1/2 rotate-45 bg-gray-800" />
            </div>
          </div>
        )}
      </div>
      <p className={`mt-2 text-3xl font-semibold ${textClass}`}>{value}</p>
      <p className="mt-2 text-xs text-gray-500">{subtext}</p>
    </div>
  );
}

function CourseRow({ course }: { course: LecturerCourseStats }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-4 transition hover:border-indigo-200 hover:bg-white">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <Link href={`/lecturer/course/${course.course_id}`} className="group block">
          <p className="text-sm uppercase tracking-wide text-indigo-600 group-hover:text-indigo-700">{course.course_code}</p>
          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-indigo-700">{course.course_name}</h3>
          <p className="text-xs text-gray-500">
            {course.enrolled_students} students · {course.materials_count} materials
          </p>
        </Link>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          {course.pending_approvals > 0 && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              {course.pending_approvals} pending approvals
            </span>
          )}
          <div className="flex items-center gap-3 mt-1">
            <Link
              href={`/lecturer/course/${course.course_id}/students`}
              className="text-xs font-semibold text-gray-600 hover:text-indigo-600 px-2 py-1 rounded hover:bg-white border border-transparent hover:border-gray-200 transition-all"
            >
              Manage Students
            </Link>
            <Link
              href={`/lecturer/course/${course.course_id}`}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
            >
              View analytics →
            </Link>
          </div>
        </div>
      </div>
      <Link href={`/lecturer/course/${course.course_id}`} className="mt-4 flex items-center justify-between rounded-lg bg-white px-3 py-2 text-xs text-gray-500 shadow-sm hover:bg-gray-50">
        <span>Class Avg Score</span>
        <span className="font-mono font-medium text-gray-900">{course.avg_class_score.toFixed(1)}%</span>
      </Link>
      {course.at_risk_students > 0 && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-amber-600">
          <span className="inline-block h-2 w-2 rounded-full bg-amber-500"></span>
          {course.at_risk_students} student{course.at_risk_students !== 1 ? "s" : ""} need{course.at_risk_students === 1 ? "s" : ""} help
        </div>
      )}
    </div>
  );
}

function StudyBundlesSection({
  bundles,
  courses,
}: {
  bundles: LecturerBundleItem[];
  courses: LecturerCourseStats[];
}) {
  const [expandedCourses, setExpandedCourses] = useState<Set<number>>(new Set());
  const [showAll, setShowAll] = useState(false);

  // Group bundles by course
  const bundlesByCourse = useMemo(() => {
    const grouped: Record<number, LecturerBundleItem[]> = {};
    bundles.forEach((bundle) => {
      if (!grouped[bundle.course_id]) {
        grouped[bundle.course_id] = [];
      }
      grouped[bundle.course_id].push(bundle);
    });
    return grouped;
  }, [bundles]);

  const courseIds = Object.keys(bundlesByCourse).map(Number);
  const displayedCourseIds = showAll ? courseIds : courseIds.slice(0, 2);

  const toggleCourse = (courseId: number) => {
    setExpandedCourses((prev) => {
      const next = new Set(prev);
      if (next.has(courseId)) {
        next.delete(courseId);
      } else {
        next.add(courseId);
      }
      return next;
    });
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900">Study bundles</h2>
      <p className="mt-1 text-sm text-gray-500">
        AI-curated kits per week, built from your approved materials.
      </p>
      <div className="mt-4 space-y-2">
        {bundles.length === 0 && (
          <div className="rounded-lg bg-indigo-50 p-4 text-center">
            <span className="text-2xl">📦</span>
            <p className="mt-1 text-xs font-medium text-indigo-700">No study bundles yet</p>
            <p className="mt-1 text-xs text-indigo-600">Approve materials to generate AI-curated weekly kits.</p>
          </div>
        )}
        {displayedCourseIds.map((courseId) => {
          const course = courses.find((c) => c.course_id === courseId);
          const courseBundles = bundlesByCourse[courseId] || [];
          const isExpanded = expandedCourses.has(courseId);

          return (
            <div
              key={courseId}
              className="rounded-lg border border-gray-100 overflow-hidden"
            >
              <button
                onClick={() => toggleCourse(courseId)}
                className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-indigo-600">
                    {course?.course_code}
                  </span>
                  <span className="text-xs text-gray-600 truncate">
                    {course?.course_name}
                  </span>
                  <span className="text-[0.65rem] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full">
                    {courseBundles.length} weeks
                  </span>
                </div>
                <svg
                  className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {isExpanded && (
                <div className="px-3 py-2 space-y-2 bg-white">
                  {courseBundles.map((bundle, idx) => (
                    <div key={idx} className="border-l-2 border-indigo-200 pl-3 py-1">
                      <p className="text-xs font-medium text-gray-900">
                        Week {bundle.week_number}: {bundle.topic}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {bundle.materials.slice(0, 3).map((mat) => (
                          <a
                            key={mat.id}
                            href={mat.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-[0.65rem] bg-gray-100 hover:bg-indigo-100 text-gray-600 hover:text-indigo-700 px-2 py-0.5 rounded transition-colors"
                            title={mat.title}
                          >
                            <span className="truncate max-w-[100px]">{mat.title}</span>
                            <span className="text-gray-400">↗</span>
                          </a>
                        ))}
                        {bundle.materials.length > 3 && (
                          <span className="text-[0.65rem] text-gray-400 px-1">
                            +{bundle.materials.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        {courseIds.length > 2 && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="w-full text-xs text-indigo-600 hover:text-indigo-800 py-2 text-center"
          >
            {showAll ? "Show less" : `Show ${courseIds.length - 2} more courses`}
          </button>
        )}
      </div>
    </div>
  );
}
