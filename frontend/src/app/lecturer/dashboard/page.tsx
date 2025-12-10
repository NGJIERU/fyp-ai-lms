"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

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
  lecturer_id: number;
  lecturer_name: string;
  courses: LecturerCourseStats[];
  total_students: number;
  pending_material_approvals: number;
  recent_submissions: Submission[];
};

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

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header>
          <p className="text-sm uppercase tracking-wide text-indigo-600">Lecturer Dashboard</p>
          <h1 className="mt-2 text-3xl font-semibold text-gray-900">
            Welcome back, {data.lecturer_name}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor course performance, student progress, and pending approvals.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          <SummaryCard label="Courses" value={totalCourses} subtext="Assigned to you" />
          <SummaryCard label="Students" value={data.total_students} subtext="Enrolled across courses" />
          <SummaryCard
            label="Avg class score"
            value={`${avgClassScore.toFixed(1)}%`}
            subtext="Across all courses"
          />
          <SummaryCard
            label="Pending approvals"
            value={data.pending_material_approvals}
            subtext="Materials awaiting review"
            variant="warning"
          />
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Courses overview</h2>
            </div>
            <div className="mt-6 space-y-4">
              {data.courses.length === 0 && (
                <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
                  You have no active courses yet.
                </p>
              )}
              {data.courses.map((course) => (
                <CourseRow key={course.course_id} course={course} />
              ))}
            </div>
          </section>

          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Recent submissions</h2>
            <div className="mt-4 space-y-4">
              {data.recent_submissions.length === 0 && (
                <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
                  No recent submissions.
                </p>
              )}
              {data.recent_submissions.map((submission, index) => (
                <div key={`${submission.student_id}-${index}`} className="rounded-lg border border-gray-100 p-4">
                  <p className="text-sm font-medium text-gray-900">
                    Student #{submission.student_id} · Week {submission.week_number}
                  </p>
                  <p className="text-xs text-gray-500">
                    Course #{submission.course_id} · Score {submission.score?.toFixed(1) ?? "-"}%
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {submission.attempted_at
                      ? new Date(submission.attempted_at).toLocaleString()
                      : "Timestamp unavailable"}
                  </p>
                </div>
              ))}
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

function CourseRow({ course }: { course: LecturerCourseStats }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-indigo-600">{course.course_code}</p>
          <h3 className="text-lg font-semibold text-gray-900">{course.course_name}</h3>
          <p className="text-xs text-gray-500">
            {course.enrolled_students} students · {course.materials_count} materials
          </p>
        </div>
        {course.pending_approvals > 0 && (
          <span className="self-start rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            {course.pending_approvals} pending approvals
          </span>
        )}
      </div>
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Avg class score</span>
          <span>{course.avg_class_score.toFixed(1)}%</span>
        </div>
        <div className="mt-2 h-3 rounded-full bg-white shadow-inner">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-indigo-500 to-indigo-600"
            style={{ width: `${Math.min(Math.max(course.avg_class_score, 0), 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
