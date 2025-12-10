"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

type EnrolledCourse = {
  course_id: number;
  code: string;
  name: string;
  lecturer_name?: string | null;
  progress_percent: number;
  weak_topics_count: number;
};

type RecentActivity = {
  action: string;
  resource_type?: string | null;
  created_at?: string | null;
};

type StudentDashboardResponse = {
  student_id: number;
  student_name: string;
  enrolled_courses: EnrolledCourse[];
  recent_activity: RecentActivity[];
  weak_topics_summary: Record<string, number>;
  total_study_time_hours: number;
};

export default function StudentDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<StudentDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = window.localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    const controller = new AbortController();

    async function loadDashboard() {
      try {
        const payload = await apiFetch<StudentDashboardResponse>(
          "/api/v1/dashboard/student",
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
        setError(err.message ?? "Unable to load student dashboard");
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
    return () => controller.abort();
  }, [router]);

  const totalWeakTopics = useMemo(() => {
    if (!data) return 0;
    return Object.values(data.weak_topics_summary || {}).reduce(
      (acc: number, value: number) => acc + value,
      0
    );
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

  if (!data) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header>
          <p className="text-sm uppercase tracking-wide text-indigo-600">
            Student Dashboard
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-gray-900">
            Welcome back, {data.student_name}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Track your course progress, study time, and weak topics at a glance.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <SummaryCard
            label="Enrolled courses"
            value={data.enrolled_courses.length}
            subtext="Active this semester"
          />
          <SummaryCard
            label="Total study time"
            value={`${data.total_study_time_hours.toFixed(1)} hrs`}
            subtext="Recorded via sessions"
          />
          <SummaryCard
            label="Weak topics"
            value={totalWeakTopics}
            subtext="Needs revision"
            variant="warning"
          />
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Enrolled courses
              </h2>
            </div>
            <div className="mt-6 space-y-4">
              {data.enrolled_courses.length === 0 && (
                <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
                  You aren&apos;t enrolled in any courses yet.
                </p>
              )}
              {data.enrolled_courses.map((course) => (
                <CourseCard key={course.course_id} course={course} />
              ))}
            </div>
          </section>

          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">
              Recent activity
            </h2>
            <div className="mt-4 space-y-4">
              {data.recent_activity.length === 0 && (
                <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
                  No activity yet.
                </p>
              )}
              {data.recent_activity.map((item, index) => (
                <div key={`${item.action}-${index}`} className="flex gap-3">
                  <div className="mt-2 h-2 w-2 rounded-full bg-indigo-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {item.action}
                    </p>
                    <p className="text-xs text-gray-500">
                      {item.resource_type ?? "General"} · {" "}
                      {item.created_at
                        ? new Date(item.created_at).toLocaleString()
                        : "time unknown"}
                    </p>
                  </div>
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

function CourseCard({ course }: { course: EnrolledCourse }) {
  const progress = Math.min(Math.max(course.progress_percent, 0), 100);
  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-indigo-600">
            {course.code}
          </p>
          <h3 className="text-lg font-semibold text-gray-900">
            {course.name}
          </h3>
          <p className="text-xs text-gray-500">
            Lecturer: {course.lecturer_name ?? "TBA"}
          </p>
        </div>
        {course.weak_topics_count > 0 && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            {course.weak_topics_count} weak topics
          </span>
        )}
      </div>
      <div className="mt-4">
        <div className="flex items-center justify_between text-xs text-gray-500">
          <span>Progress</span>
          <span>{progress.toFixed(0)}%</span>
        </div>
        <div className="mt-2 h-3 rounded-full bg-white shadow-inner">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-indigo-500 to-indigo-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
