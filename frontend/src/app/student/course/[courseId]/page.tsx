"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";

type WeeklyProgress = {
  week_number: number;
  topic: string;
  status: string;
  score?: number | null;
  materials_count: number;
};

type MaterialItem = {
  id: number;
  title: string;
  url: string;
  source: string;
  type: string;
  quality_score: number;
};

type WeakTopicItem = {
  week_number: number;
  topic: string;
  average_score: number;
  attempts: number;
  recommended_materials: MaterialItem[];
};

type CourseDetailResponse = {
  course_id: number;
  course_name: string;
  course_code: string;
  lecturer_name?: string | null;
  weekly_progress: WeeklyProgress[];
  weak_topics: WeakTopicItem[];
  overall_score: number;
  materials_accessed: number;
  total_materials: number;
};

type PracticeQuestionsResponse = {
  topic: string;
  week_number: number;
  difficulty: string;
  questions: { question: string; type?: string }[];
  sources: string[];
};

type ExplainResponse = {
  explanation: string;
  topic: string;
  sources: { title: string; url?: string; source?: string }[];
  course_id: number;
  week_number?: number | null;
};

const STATUS_COLOR: Record<string, string> = {
  mastered: "bg-emerald-100 text-emerald-800",
  proficient: "bg-emerald-100 text-emerald-800",
  learning: "bg-sky-100 text-sky-700",
  in_progress: "bg-sky-100 text-sky-700",
  not_started: "bg-gray-100 text-gray-600",
  default: "bg-gray-100 text-gray-600",
};

export default function StudentCourseDetailPage() {
  const router = useRouter();
  const params = useParams<{ courseId: string }>();
  const courseId = Number(params?.courseId);
  const { loading: authLoading, authorized } = useRequireRole(["student", "super_admin"]);

  const [data, setData] = useState<CourseDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [practiceResults, setPracticeResults] = useState<Record<number, PracticeQuestionsResponse | null>>({});
  const [tutorResponses, setTutorResponses] = useState<Record<number, ExplainResponse | null>>({});
  const [practiceLoadingWeek, setPracticeLoadingWeek] = useState<number | null>(null);
  const [tutorLoadingWeek, setTutorLoadingWeek] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

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
    async function loadDetail() {
      try {
        const payload = await apiFetch<CourseDetailResponse>(`/api/v1/dashboard/student/course/${courseId}`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        setData(payload);
        setPracticeResults({});
        setTutorResponses({});
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err.message ?? "Unable to load course details");
      } finally {
        setIsLoading(false);
      }
    }

    loadDetail();
    return () => controller.abort();
  }, [authLoading, authorized, courseId, router]);

  const completedWeeks = useMemo(() => {
    if (!data) return 0;
    return data.weekly_progress.filter((week) => ["mastered", "proficient"].includes(week.status)).length;
  }, [data]);

  const totalWeeks = data?.weekly_progress.length ?? 0;

  async function handleGenerateQuestions(weekNumber: number) {
    if (!data) return;
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    setPracticeLoadingWeek(weekNumber);
    setActionError(null);
    try {
      const response = await apiFetch<PracticeQuestionsResponse>(
        `/api/v1/tutor/generate-questions?course_id=${data.course_id}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            week_number: weekNumber,
            num_questions: 5,
            difficulty: "medium",
          }),
        }
      );
      setPracticeResults((prev) => ({
        ...prev,
        [weekNumber]: response,
      }));
    } catch (err: any) {
      setActionError(err.message ?? "Unable to generate questions right now.");
    } finally {
      setPracticeLoadingWeek(null);
    }
  }

  async function handleAskTutor(weekNumber: number, topic: string) {
    if (!data) return;
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    setTutorLoadingWeek(weekNumber);
    setActionError(null);
    try {
      const response = await apiFetch<ExplainResponse>(`/api/v1/tutor/explain?course_id=${data.course_id}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          topic,
          week_number: weekNumber,
        }),
      });
      setTutorResponses((prev) => ({
        ...prev,
        [weekNumber]: response,
      }));
    } catch (err: any) {
      setActionError(err.message ?? "Tutor is unavailable right now.");
    } finally {
      setTutorLoadingWeek(null);
    }
  }

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-5xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Loading course insights…</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-5xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-red-600">{error ?? "Course not found"}</p>
            <Link href="/student/dashboard" className="mt-4 inline-flex text-sm font-medium text-indigo-600">
              ← Back to dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <div className="flex flex-col gap-2">
          <Link href="/student/dashboard" className="text-sm font-medium text-indigo-600">
            ← Back to dashboard
          </Link>
          <p className="text-sm uppercase tracking-wide text-indigo-600">Course focus</p>
          <h1 className="text-3xl font-semibold text-gray-900">
            {data.course_name}
            <span className="ml-3 rounded-full bg-indigo-100 px-3 py-1 text-sm font-medium text-indigo-700">
              {data.course_code}
            </span>
          </h1>
          <p className="text-sm text-gray-500">
            {data.lecturer_name ? `Led by ${data.lecturer_name}.` : "Lecturer TBD."} Track your mastery week by week.
          </p>
        </div>

        <section className="grid gap-4 md:grid-cols-4">
          <DetailStat label="Overall score" value={`${data.overall_score.toFixed(1)}%`} subtext="Across completed weeks" />
          <DetailStat label="Weeks completed" value={`${completedWeeks}/${totalWeeks}`} subtext="Proficient or mastered" />
          <DetailStat
            label="Materials viewed"
            value={`${data.materials_accessed}/${data.total_materials}`}
            subtext="Resources explored"
          />
          <DetailStat label="Weak topics" value={data.weak_topics.length} subtext="Needs attention" variant={data.weak_topics.length ? "warning" : "default"} />
        </section>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Weekly progress</h2>
              <p className="text-sm text-gray-500">Stay on pace with the syllabus.</p>
            </div>
          </div>
          {actionError && <p className="mt-3 text-sm text-red-600">{actionError}</p>}
          <div className="mt-6 space-y-4">
            {data.weekly_progress.map((week) => {
              const statusClass = STATUS_COLOR[week.status] ?? STATUS_COLOR.default;
              return (
                <div key={week.week_number} className="rounded-xl border border-gray-100 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900">Week {week.week_number}</p>
                      <p className="text-xs text-gray-500">{week.topic}</p>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}>
                      {formatStatusLabel(week.status)}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-gray-500">
                    <span>{week.materials_count} materials available</span>
                    <span>
                      Score: {typeof week.score === "number" ? `${(week.score * 100).toFixed(0)}%` : "—"}
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={() => handleGenerateQuestions(week.week_number)}
                      disabled={practiceLoadingWeek === week.week_number}
                      className="rounded-md border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:border-indigo-200 disabled:opacity-60"
                    >
                      {practiceLoadingWeek === week.week_number ? "Generating…" : "Practice quiz"}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleAskTutor(week.week_number, week.topic)}
                      disabled={tutorLoadingWeek === week.week_number}
                      className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-60"
                    >
                      {tutorLoadingWeek === week.week_number ? "Connecting…" : "Ask AI tutor"}
                    </button>
                  </div>
                  {practiceResults[week.week_number] && (
                    <div className="mt-4 rounded-lg bg-indigo-50 p-4 text-sm text-indigo-900">
                      <p className="font-semibold">
                        Practice set · Week {practiceResults[week.week_number]?.week_number}{" "}
                        ({practiceResults[week.week_number]?.difficulty})
                      </p>
                      <ul className="mt-2 space-y-2">
                        {practiceResults[week.week_number]?.questions.map((question, index) => (
                          <li key={index} className="leading-snug">
                            <span className="font-medium text-indigo-800">Q{index + 1}:</span> {question.question}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {tutorResponses[week.week_number] && (
                    <div className="mt-4 rounded-lg bg-gray-50 p-4 text-sm text-gray-700">
                      <p className="font-semibold text-gray-900">Tutor insight</p>
                      <p className="mt-2 whitespace-pre-line">{tutorResponses[week.week_number]?.explanation}</p>
                      {tutorResponses[week.week_number]?.sources?.length ? (
                        <div className="mt-3 text-xs text-gray-500">
                          Sources:{" "}
                          {tutorResponses[week.week_number]?.sources.map((source, index) => (
                            <span key={`${source.title}-${index}`}>
                              {source.url ? (
                                <a href={source.url} target="_blank" rel="noreferrer" className="text-indigo-600 underline">
                                  {source.title}
                                </a>
                              ) : (
                                source.title
                              )}
                              {index < (tutorResponses[week.week_number]?.sources.length ?? 0) - 1 ? ", " : ""}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Weak topics & recommended materials</h2>
              <p className="text-sm text-gray-500">Use curated resources to close gaps quickly.</p>
            </div>
          </div>
          <div className="mt-6 space-y-4">
            {data.weak_topics.length === 0 && (
              <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">Great work! No weak topics flagged right now.</p>
            )}
            {data.weak_topics.map((topic) => (
              <div key={topic.week_number} className="rounded-xl border border-gray-100 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      Week {topic.week_number}: {topic.topic}
                    </p>
                    <p className="text-xs text-gray-500">
                      Avg score {(topic.average_score * 100).toFixed(0)}% · {topic.attempts} attempts
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">Needs review</span>
                </div>
                <div className="mt-4 space-y-2">
                  {topic.recommended_materials.map((material) => (
                    <a
                      key={material.id}
                      href={material.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 text-sm text-gray-700 hover:border-indigo-200"
                    >
                      <span>
                        <span className="font-medium text-gray-900">{material.title}</span>
                        <span className="ml-2 text-xs uppercase text-gray-400">{material.source}</span>
                      </span>
                      <span className="text-xs text-gray-500">Quality {(material.quality_score * 100).toFixed(0)}%</span>
                    </a>
                  ))}
                </div>
              </div>
            ))}
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

function formatStatusLabel(status: string) {
  switch (status) {
    case "mastered":
      return "Mastered";
    case "proficient":
      return "Proficient";
    case "learning":
    case "in_progress":
      return "In progress";
    case "not_started":
      return "Not started";
    default:
      return status.replace("_", " ");
  }
}
