"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import TutorExplanation from "@/components/tutor/TutorExplanation";
import RecommendationCard from "@/components/recommendations/RecommendationCard";
import BundleCard from "@/components/recommendations/BundleCard";
import RecommendationFilters, { SortOption, FilterOption } from "@/components/recommendations/RecommendationFilters";
import { SmartFeedSkeleton } from "@/components/ui/Skeleton";
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
  total_attempts: number;
  weeks_attempted: number;
  weeks_completed: number;
  materials_accessed: number;
  total_materials: number;
};

type PersonalizedRecommendation = {
  course_id: number;
  week_number: number;
  topic: string;
  material: {
    id: number;
    title: string;
    url: string;
    source: string;
    type: string;
  };
  similarity_score: number;
  quality_score: number;
  base_score: number;
  personalized_score: number;
  reasons: string[];
};

type ContextBundle = {
  course_id: number;
  week_number: number;
  topic: string;
  summary: string;
  materials: {
    id: number;
    title: string;
    url: string;
    source: string;
    type: string;
    similarity_score?: number;
    quality_score?: number;
  }[];
};

type RatingSummary = {
  material_id: number;
  average_rating: number;
  total_ratings: number;
  upvotes: number;
  downvotes: number;
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
  const [personalizedRecs, setPersonalizedRecs] = useState<PersonalizedRecommendation[]>([]);
  const [bundles, setBundles] = useState<ContextBundle[]>([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [ratings, setRatings] = useState<Record<number, RatingSummary>>({});
  const [ratingInFlight, setRatingInFlight] = useState<number | null>(null);
  const [likedRecs, setLikedRecs] = useState<Set<number>>(new Set());
  const [hiddenRecs, setHiddenRecs] = useState<Set<number>>(new Set());
  const [sortBy, setSortBy] = useState<SortOption>("relevance");
  const [filterBy, setFilterBy] = useState<FilterOption>("all");

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
    const authToken = token;

    const controller = new AbortController();
    async function loadDetail() {
      try {
        const payload = await apiFetch<CourseDetailResponse>(`/api/v1/dashboard/student/course/${courseId}`, {
          headers: { Authorization: `Bearer ${authToken}` },
          signal: controller.signal,
        });
        setData(payload);
        setPracticeResults({});
        setTutorResponses({});
        fetchPersonalizedAndBundles(authToken, courseId);
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

  async function fetchPersonalizedAndBundles(token: string, courseId: number) {
    setRecsLoading(true);
    try {
      const [personalizedResp, bundlesResp] = await Promise.all([
        apiFetch<{ recommendations: PersonalizedRecommendation[] }>(
          `/api/v1/recommendations/personalized?course_id=${courseId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        ),
        apiFetch<{ bundles: ContextBundle[] }>(
          `/api/v1/recommendations/context-bundles?course_id=${courseId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        ),
      ]);
      setPersonalizedRecs(personalizedResp.recommendations ?? []);
      setBundles(bundlesResp.bundles ?? []);
    } catch (err) {
      console.error("Failed to load personalized content", err);
    } finally {
      setRecsLoading(false);
    }
  }

  const completedWeeks = useMemo(() => {
    if (!data) return 0;
    return data.weekly_progress.filter((week) => ["mastered", "proficient"].includes(week.status)).length;
  }, [data]);

  const totalWeeks = data?.weekly_progress.length ?? 0;

  // Computed set of material IDs already shown in bundles
  const bundleMaterialIds = useMemo(() => {
    const ids = new Set<number>();
    bundles.forEach(b => b.materials.forEach(m => ids.add(m.id)));
    return ids;
  }, [bundles]);

  // Filtered and sorted recommendations
  const filteredPersonalizedRecs = useMemo(() => {
    let recs = personalizedRecs.filter(r => !bundleMaterialIds.has(r.material.id));
    
    // Apply source filter
    if (filterBy !== "all") {
      recs = recs.filter(r => {
        const source = r.material.source.toLowerCase();
        if (filterBy === "youtube") return source.includes("youtube");
        if (filterBy === "arxiv") return source.includes("arxiv");
        if (filterBy === "github") return source.includes("github");
        if (filterBy === "manual") return source.includes("manual") || source.includes("upload");
        return true;
      });
    }
    
    // Apply sorting
    recs = [...recs].sort((a, b) => {
      if (sortBy === "relevance") return b.personalized_score - a.personalized_score;
      if (sortBy === "quality") return b.quality_score - a.quality_score;
      if (sortBy === "recent") return b.material.id - a.material.id; // Higher ID = more recent
      return 0;
    });
    
    return recs;
  }, [personalizedRecs, bundleMaterialIds, filterBy, sortBy]);
  
  // Total count before filtering (for display)
  const totalRecsCount = useMemo(() => {
    return personalizedRecs.filter(r => !bundleMaterialIds.has(r.material.id)).length;
  }, [personalizedRecs, bundleMaterialIds]);

  async function handleRateMaterial(materialId: number, score: number) {
    if (ratingInFlight) return;
    setRatingInFlight(materialId);

    // Optimistic UI updates
    if (score > 0) {
      setLikedRecs((prev) => {
        const next = new Set(prev);
        if (next.has(materialId)) next.delete(materialId);
        else next.add(materialId);
        return next;
      });
      setHiddenRecs((prev) => {
        const next = new Set(prev);
        next.delete(materialId);
        return next;
      });
    } else if (score < 0) {
      setHiddenRecs((prev) => {
        const next = new Set(prev);
        next.add(materialId);
        return next;
      });
    }

    try {
      await apiFetch(`/api/v1/materials/${materialId}/rate`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ rating: score }),
      });

      const summary = await apiFetch<RatingSummary>(
        `/api/v1/materials/${materialId}/ratings/summary`
      );
      setRatings((prev) => ({
        ...prev,
        [materialId]: summary,
      }));
    } catch (err: any) {
      console.error("Failed to rate material:", err);
    } finally {
      setRatingInFlight(null);
    }
  }

  function handleMaterialClick(materialId: number, resourceType: string = "material") {
    const token = localStorage.getItem("access_token");
    if (!token || !data) return;

    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || ""}/api/v1/analytics/log`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({
        action: "view_material",
        resource_type: resourceType,
        resource_id: materialId,
        course_id: data.course_id,
      }),
      keepalive: true,
    }).catch(() => { });
  }

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

    // Build context from existing quiz questions if available
    const existingQuestions = practiceResults[weekNumber];
    let questionsContext: string | undefined;
    if (existingQuestions && existingQuestions.questions.length > 0) {
      const questionList = existingQuestions.questions.map((q, i) => `${i + 1}. ${q.question}`).join("\n");
      questionsContext = `Explain the key concepts needed to answer these practice questions:\n${questionList}`;
    }

    try {
      const response = await apiFetch<ExplainResponse>(`/api/v1/tutor/explain?course_id=${data.course_id}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          topic: topic,
          week_number: weekNumber,
          context: questionsContext,
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

  const [activeTab, setActiveTab] = useState<"curriculum" | "smart-feed">("curriculum");

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

  const handleSignOut = () => {
    localStorage.removeItem("access_token");
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <div className="flex flex-col gap-2">
          <Link href="/student/dashboard" className="text-sm font-medium text-indigo-600">
            ← Back to dashboard
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-wide text-indigo-600">Course focus</p>
              <h1 className="text-3xl font-semibold text-gray-900">
                {data.course_name}
                <span className="ml-3 rounded-full bg-indigo-100 px-3 py-1 text-sm font-medium text-indigo-700">
                  {data.course_code}
                </span>
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href={`/student/course/${courseId}/chat`}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700"
              >
                <span>💬</span> Start Full Chat
              </Link>
              <button
                onClick={handleSignOut}
                className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:text-red-600"
              >
                Sign out
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-500">
            {data.lecturer_name ? `Led by ${data.lecturer_name}.` : "Lecturer TBD."} Track your mastery week by week.
          </p>
        </div>

        <section className="grid gap-4 md:grid-cols-4">
          <DetailStat
            label="Overall score"
            value={data.total_attempts < 5 ? "In Progress" : `${data.overall_score.toFixed(1)}%`}
            subtext={data.total_attempts < 5 ? `${data.total_attempts} attempts so far` : "Across completed weeks"}
            tooltip="Score stabilizes after 5+ quiz attempts"
          />
          <DetailStat
            label="Weeks completed"
            value={`${data.weeks_completed}/${totalWeeks}`}
            subtext="≥70% = Proficient, ≥85% = Mastered"
            tooltip="Completed = average score ≥70%"
          />
          <DetailStat
            label="Materials viewed"
            value={`${data.materials_accessed}/${data.total_materials}`}
            subtext="Resources explored"
          />
          <DetailStat label="Weak topics" value={data.weak_topics.length} subtext="Needs attention" variant={data.weak_topics.length ? "warning" : "default"} />
        </section>

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab("curriculum")}
            className={`mr-8 pb-4 text-sm font-medium transition-colors ${activeTab === "curriculum"
              ? "border-b-2 border-indigo-600 text-indigo-600"
              : "border-b-2 border-transparent text-gray-500 hover:text-gray-700"
              }`}
          >
            Curriculum
          </button>
          <button
            onClick={() => setActiveTab("smart-feed")}
            className={`pb-4 text-sm font-medium transition-colors ${activeTab === "smart-feed"
              ? "border-b-2 border-indigo-600 text-indigo-600"
              : "border-b-2 border-transparent text-gray-500 hover:text-gray-700"
              }`}
          >
            Smart Feed
            {(filteredPersonalizedRecs.length > 0 || data.weak_topics.length > 0) && (
              <span className="ml-2 rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700">
                {filteredPersonalizedRecs.length + data.weak_topics.length}
              </span>
            )}
          </button>
        </div>

        {activeTab === "curriculum" ? (
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Weekly progress</h2>
                <p className="text-sm text-gray-500">Stay on pace with the syllabus.</p>
              </div>
            </div>
            {actionError && <p className="mt-3 text-sm text-red-600">{actionError}</p>}
            <div className="mt-6 space-y-4">
              {data.weekly_progress.map((week) => (
                <WeekCard
                  key={`${week.week_number}-${practiceResults[week.week_number] ? 'loaded' : 'empty'}`}
                  week={week}
                  practiceResult={practiceResults[week.week_number] ?? null}
                  tutorResponse={tutorResponses[week.week_number] ?? null}
                  onGenerateQuestions={() => handleGenerateQuestions(week.week_number)}
                  onAskTutor={() => handleAskTutor(week.week_number, week.topic)}
                  isGenerating={practiceLoadingWeek === week.week_number}
                  isAskingTutor={tutorLoadingWeek === week.week_number}
                  error={actionError}
                  onClearError={() => setActionError(null)}
                />
              ))}
            </div>
          </section>
        ) : recsLoading && personalizedRecs.length === 0 && bundles.length === 0 ? (
          <SmartFeedSkeleton />
        ) : (
          <div className="flex flex-col gap-6">
            <section className="rounded-2xl bg-white p-6 shadow-sm">
              <header className="flex flex-col gap-1">
                <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Personalized feed</p>
                <div className="flex items-center gap-2">
                  <span className="text-xl">🎯</span>
                  <div className="group relative">
                    <h2 className="text-lg font-semibold text-gray-900 cursor-help border-b border-dotted border-gray-400">Targeted Practice</h2>
                    <div className="absolute bottom-full left-0 mb-2 hidden w-64 rounded-lg bg-gray-800 p-2 text-xs text-white shadow-lg group-hover:block z-10">
                      Resources specifically chosen to improve your weak topics based on quiz performance.
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-500">Resources specifically chosen to improve your weak topics.</p>
              </header>
              
              {/* Sort and Filter Controls */}
              {totalRecsCount > 0 && (
                <div className="mt-4">
                  <RecommendationFilters
                    sortBy={sortBy}
                    filterBy={filterBy}
                    onSortChange={setSortBy}
                    onFilterChange={setFilterBy}
                    totalCount={totalRecsCount}
                    filteredCount={filteredPersonalizedRecs.length}
                  />
                </div>
              )}
              
              <div className="mt-5 space-y-4">
                {filteredPersonalizedRecs.length === 0 && (
                  <div className="rounded-xl border-2 border-dashed border-gray-200 p-8 text-center">
                    <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-3">
                      <span className="text-2xl">🎯</span>
                    </div>
                    <p className="text-sm font-medium text-gray-700">
                      {personalizedRecs.length > 0 ? "You're all caught up!" : "No recommendations yet"}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {personalizedRecs.length > 0 
                        ? "Check the Weekly Review Kits below for general study materials." 
                        : "Complete a few practice questions to get tailored suggestions."}
                    </p>
                  </div>
                )}
                {filteredPersonalizedRecs
                  .filter(rec => !hiddenRecs.has(rec.material.id))
                  .map((rec) => (
                    <RecommendationCard
                      key={`${rec.material.id}-${rec.week_number}`}
                      material={rec.material}
                      weekNumber={rec.week_number}
                      topic={rec.topic}
                      reasons={rec.reasons}
                      personalizedScore={rec.personalized_score}
                      similarityScore={rec.similarity_score}
                      qualityScore={rec.quality_score}
                      isLiked={likedRecs.has(rec.material.id)}
                      ratingInFlight={ratingInFlight === rec.material.id}
                      ratings={ratings[rec.material.id]}
                      onRate={handleRateMaterial}
                      onMaterialClick={handleMaterialClick}
                    />
                  ))}
              </div>
            </section>
            {bundles.length > 0 && (
              <section className="rounded-2xl bg-white p-6 shadow-sm">
                <header className="flex flex-col gap-1">
                  <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Study bundles</p>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">📚</span>
                    <div className="group relative">
                      <h2 className="text-lg font-semibold text-gray-900 cursor-help border-b border-dotted border-gray-400">Weekly Review Kits</h2>
                      <div className="absolute bottom-full left-0 mb-2 hidden w-64 rounded-lg bg-gray-800 p-2 text-xs text-white shadow-lg group-hover:block z-10">
                        Complete collections of approved materials for each week, useful for general revision.
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-gray-500">Complete collections of approved materials for each week.</p>
                </header>
                <div className="mt-6 space-y-4">
                  {bundles.map((bundle) => (
                    <BundleCard
                      key={`${bundle.week_number}-${bundle.topic}`}
                      weekNumber={bundle.week_number}
                      topic={bundle.topic}
                      summary={bundle.summary}
                      materials={bundle.materials}
                      onMaterialClick={handleMaterialClick}
                    />
                  ))}
                </div>
              </section>
            )}
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
                        <a key={material.id} href={material.url} target="_blank" rel="noreferrer" className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 text-sm text-gray-700 hover:border-indigo-200" onClick={() => handleMaterialClick(material.id)}>
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
        )}
      </div>
    </div>
  );
}

function DetailStat({ label, value, subtext, variant = "default", tooltip }: { label: string; value: string | number; subtext: string; variant?: "default" | "warning"; tooltip?: string }) {
  const textClass = variant === "warning" ? "text-amber-600" : "text-gray-900";
  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm" title={tooltip}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${textClass}`}>{value}</p>
      <p className="mt-2 text-xs text-gray-500">{subtext}</p>
    </div>
  );
}

function formatStatusLabel(status: string) {
  switch (status) {
    case "mastered": return "Mastered";
    case "proficient": return "Proficient";
    case "learning":
    case "in_progress": return "In progress";
    case "not_started": return "Not started";
    default: return status.replace("_", " ");
  }
}

type WeekCardMode = "overview" | "practice" | "tutor";

function WeekCard({
  week,
  practiceResult,
  tutorResponse,
  onGenerateQuestions,
  onAskTutor,
  isGenerating,
  isAskingTutor,
  error,
  onClearError,
}: {
  week: WeeklyProgress;
  practiceResult: PracticeQuestionsResponse | null;
  tutorResponse: ExplainResponse | null;
  onGenerateQuestions: () => void;
  onAskTutor: () => void;
  isGenerating: boolean;
  isAskingTutor: boolean;
  error: string | null;
  onClearError: () => void;
}) {
  const [mode, setMode] = useState<WeekCardMode>("overview");

  // Force switch to practice tab when results arrive, using a more robust check
  useEffect(() => { 
    if (practiceResult && practiceResult.questions && practiceResult.questions.length > 0) {
      setMode("practice"); 
    }
  }, [practiceResult]);
  useEffect(() => { if (tutorResponse) setMode("tutor"); }, [tutorResponse]);

  const statusClass = STATUS_COLOR[week.status] ?? STATUS_COLOR.default;

  return (
    <div className="rounded-xl border border-gray-100 bg-white shadow-sm">
      <div className="p-4 border-b border-gray-50">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-gray-900">Week {week.week_number}</p>
            <p className="text-xs text-gray-500">{week.topic}</p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass}`}>
            {formatStatusLabel(week.status)}
          </span>
        </div>
      </div>
      <div className="flex border-b border-gray-100 bg-gray-50/50 px-4">
        <button onClick={() => setMode("overview")} className={`mr-4 border-b-2 py-3 text-xs font-medium transition-colors ${mode === "overview" ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200"}`}>
          Overview
        </button>
        <button onClick={() => setMode("practice")} className={`mr-4 border-b-2 py-3 text-xs font-medium transition-colors ${mode === "practice" ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200"}`}>
          Practice Quiz {practiceResult && "✓"}
        </button>
        <button onClick={() => setMode("tutor")} className={`border-b-2 py-3 text-xs font-medium transition-colors ${mode === "tutor" ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200"}`}>
          Tutor Insight {tutorResponse && "✓"}
        </button>
      </div>
      <div className="p-4">
        {mode === "overview" && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1"><span>📚</span> {week.materials_count} materials available</span>
              <span className="flex items-center gap-1"><span>🏆</span> Score: {typeof week.score === "number" ? `${(week.score * 100).toFixed(0)}%` : "—"}</span>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="flex items-start gap-3">
                <div className="mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-600">i</div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Ready to learn?</p>
                  <p className="mt-1 text-xs text-gray-500">Switch to the <strong>Practice Quiz</strong> tab to generate questions or ask the AI Tutor for a summary in the <strong>Tutor Insight</strong> tab.</p>
                </div>
              </div>
            </div>
          </div>
        )}
        {mode === "practice" && (
          <div>
            {!practiceResult ? (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-2xl">📝</div>
                <h3 className="text-sm font-semibold text-gray-900">Pop Quiz Time</h3>
                <p className="mt-1 mb-6 max-w-sm text-xs text-gray-500">Generate a custom 5-question quiz to test your mastery of {week.topic}.</p>
                <button type="button" onClick={onGenerateQuestions} disabled={isGenerating} className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-60 transition">
                  {isGenerating ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />Generating...</> : "Generate Questions"}
                </button>
                {error && (
                  <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200">
                    <p className="text-sm text-red-600">{error}</p>
                    <button onClick={onClearError} className="mt-2 text-xs text-red-500 hover:text-red-700 underline">Dismiss</button>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-indigo-50 px-4 py-3 border border-indigo-100">
                  <p className="text-sm font-semibold text-indigo-900">Practice set</p>
                  <button onClick={onGenerateQuestions} disabled={isGenerating} className="text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline transition">
                    {isGenerating ? "Refreshing..." : "Generate New Set ↻"}
                  </button>
                </div>
                <ul className="space-y-4">
                  {practiceResult.questions.map((question, index) => (
                    <li key={index} className="rounded-lg border border-gray-100 p-4 transition hover:border-indigo-100 hover:bg-gray-50">
                      <div className="flex gap-3">
                        <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">{index + 1}</span>
                        <p className="text-sm text-gray-800 leading-relaxed">{question.question}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        {mode === "tutor" && (
          <div>
            {!tutorResponse ? (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-2xl">🤖</div>
                <h3 className="text-sm font-semibold text-gray-900">AI Personal Tutor</h3>
                <p className="mt-1 mb-6 max-w-sm text-xs text-gray-500">Stuck on a concept? Ask the AI to explain {week.topic} in simple terms.</p>
                <button type="button" onClick={onAskTutor} disabled={isAskingTutor} className="rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 hover:border-gray-300 disabled:opacity-60 transition">
                  {isAskingTutor ? "Thinking..." : "Explain This Topic"}
                </button>
                {error && (
                  <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200">
                    <p className="text-sm text-red-600">{error}</p>
                    <button onClick={onClearError} className="mt-2 text-xs text-red-500 hover:text-red-700 underline">Dismiss</button>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🤖</span>
                    <p className="font-semibold text-gray-900">
                      {practiceResult ? "Tutor Explanation (Based on Quiz)" : "Tutor Insight"}
                    </p>
                  </div>
                  <button onClick={onAskTutor} disabled={isAskingTutor} className="text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline transition">
                    {isAskingTutor ? "Thinking..." : "Regenerate Answer ↻"}
                  </button>
                </div>
                <TutorExplanation content={tutorResponse.explanation} />
                {tutorResponse.sources?.length ? (
                  <div className="mt-4 rounded-lg bg-gray-50 p-3 text-xs">
                    <p className="mb-2 font-semibold text-gray-500 uppercase tracking-wider text-[10px]">Sources</p>
                    <div className="flex flex-wrap gap-2">
                      {tutorResponse.sources.map((source, index) => (
                        <a key={`${source.title}-${index}`} href={source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 rounded border border-gray-200 bg-white px-2 py-1 text-gray-600 hover:border-indigo-200 hover:text-indigo-600 hover:shadow-sm transition">
                          <span className="truncate max-w-[150px]">{source.title}</span>
                          <span className="text-gray-400">↗</span>
                        </a>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
