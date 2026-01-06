"use client";

export const dynamic = "force-dynamic";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";

type LecturerDashboardResponse = {
  courses: {
    course_id: number;
    course_code: string;
    course_name: string;
    pending_approvals: number;
  }[];
};

type CourseOption = {
  id: number;
  code: string;
  name: string;
};

type PendingMaterial = {
  mapping_id: number;
  material_id: number;
  course_id: number;
  week_number: number;
  relevance_score: number;
  material?: {
    id: number;
    title: string;
    url: string;
    source: string;
    type: string;
    quality_score: number;
  } | null;
};

function MaterialsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { loading: authLoading, authorized } = useRequireRole(["lecturer", "super_admin"]);

  const initialCourseId = useMemo(() => {
    const value = Number(searchParams?.get("course"));
    return Number.isFinite(value) ? value : null;
  }, [searchParams]);
  const initialWeek = useMemo(() => searchParams?.get("week") ?? "", [searchParams]);

  const [courses, setCourses] = useState<CourseOption[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<number | null>(initialCourseId);
  const [weekFilter, setWeekFilter] = useState<string>(initialWeek);
  const [pending, setPending] = useState<PendingMaterial[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingPending, setLoadingPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isApproving, setIsApproving] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [bulkLoading, setBulkLoading] = useState<"approve" | "reject" | null>(null);

  const PAGE_SIZE = 10;

  useEffect(() => {
    if (authLoading || !authorized) return;

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    async function fetchCourses() {
      setLoadingCourses(true);
      try {
        const dashboard = await apiFetch<LecturerDashboardResponse>("/api/v1/dashboard/lecturer", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const options = dashboard.courses.map((c) => ({
          id: c.course_id,
          code: c.course_code,
          name: c.course_name,
        }));
        setCourses(options);
        // Always set first course if no course selected
        if (options.length > 0) {
          setSelectedCourse((prev) => prev || initialCourseId || options[0].id);
        }
        setError(null);
      } catch (err: any) {
        setError(err.message ?? "Unable to load courses");
      } finally {
        setLoadingCourses(false);
      }
    }

    fetchCourses();
  }, [authLoading, authorized, initialCourseId, router]);

  useEffect(() => {
    if (!selectedCourse || !authorized) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const controller = new AbortController();
    async function fetchPending() {
      setLoadingPending(true);
      try {
        const params = new URLSearchParams({ course_id: String(selectedCourse) });
        if (weekFilter) params.append("week_number", weekFilter);
        const data = await apiFetch<PendingMaterial[]>(`/api/v1/recommendations/pending?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        setPending(data);
        setSelectedIds(new Set());
        setPage(1);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err.message ?? "Failed to load pending materials");
      } finally {
        setLoadingPending(false);
      }
    }

    fetchPending();
    return () => controller.abort();
  }, [authorized, selectedCourse, weekFilter]);

  const selectedCourseLabel = useMemo(() => {
    const course = courses.find((c) => c.id === selectedCourse);
    return course ? `${course.code} · ${course.name}` : "Select a course";
  }, [courses, selectedCourse]);

  async function submitMappingAction(mappingId: number, approve: boolean, token: string, relevanceOverride?: number) {
    await apiFetch(`/api/v1/recommendations/approve/${mappingId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ approved: approve, relevance_score: relevanceOverride }),
    });
  }

  async function handleApproval(mappingId: number, approve: boolean, relevanceOverride?: number) {
    if (!authorized) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;

    setIsApproving(mappingId);
    setActionMessage(null);
    try {
      await submitMappingAction(mappingId, approve, token, relevanceOverride);
      setPending((prev) => prev.filter((item) => item.mapping_id !== mappingId));
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(mappingId);
        return next;
      });
      setActionMessage(approve ? "Material approved" : "Mapping rejected");
    } catch (err: any) {
      setError(err.message ?? "Action failed");
    } finally {
      setIsApproving(null);
    }
  }

  async function handleBulkAction(approve: boolean) {
    if (!authorized || selectedIds.size === 0) return;
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    const ids = Array.from(selectedIds);
    setBulkLoading(approve ? "approve" : "reject");
    setActionMessage(null);
    try {
      await Promise.all(ids.map((id) => submitMappingAction(id, approve, token)));
      const idSet = new Set(ids);
      setPending((prev) => prev.filter((item) => !idSet.has(item.mapping_id)));
      setSelectedIds(new Set());
      setActionMessage(approve ? "Selected materials approved" : "Selected mappings rejected");
    } catch (err: any) {
      setError(err.message ?? "Bulk action failed");
    } finally {
      setBulkLoading(null);
    }
  }

  function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setWeekFilter(formData.get("week")?.toString().trim() ?? "");
  }

  const sourceOptions = useMemo(() => {
    const set = new Set<string>();
    pending.forEach((item) => {
      const source = item.material?.source || "Unknown";
      set.add(source);
    });
    return Array.from(set).sort();
  }, [pending]);

  const typeOptions = useMemo(() => {
    const set = new Set<string>();
    pending.forEach((item) => {
      const type = item.material?.type || "Unknown";
      set.add(type);
    });
    return Array.from(set).sort();
  }, [pending]);

  const filteredPending = useMemo(() => {
    return pending.filter((item) => {
      const source = item.material?.source || "Unknown";
      const type = item.material?.type || "Unknown";
      const sourceMatches = sourceFilter === "all" || source === sourceFilter;
      const typeMatches = typeFilter === "all" || type === typeFilter;
      return sourceMatches && typeMatches;
    });
  }, [pending, sourceFilter, typeFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredPending.length / PAGE_SIZE));

  useEffect(() => {
    setPage(1);
  }, [sourceFilter, typeFilter, weekFilter, selectedCourse]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const paginatedPending = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredPending.slice(start, start + PAGE_SIZE);
  }, [filteredPending, page]);

  const allPageSelected = paginatedPending.every((item) => selectedIds.has(item.mapping_id)) && paginatedPending.length > 0;

  function toggleSelect(mappingId: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(mappingId)) {
        next.delete(mappingId);
      } else {
        next.add(mappingId);
      }
      return next;
    });
  }

  function toggleSelectPage(value: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      paginatedPending.forEach((item) => {
        if (value) {
          next.add(item.mapping_id);
        } else {
          next.delete(item.mapping_id);
        }
      });
      return next;
    });
  }

  if (authLoading || loadingCourses) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Loading courses…</p>
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

  if (courses.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">No courses available to review materials.</p>
          </div>
        </div>
      </div>
    );
  }
  
  // Show loading while auto-selecting first course
  if (!selectedCourse) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Loading materials...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header>
          <p className="text-sm uppercase tracking-wide text-indigo-600">Materials approval</p>
          <h1 className="mt-2 text-3xl font-semibold text-gray-900">Review pending recommendations</h1>
          <p className="mt-1 text-sm text-gray-500">Approve or reject AI-suggested content before students see it.</p>
        </header>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <form className="flex flex-wrap gap-4" onSubmit={handleFilterSubmit}>
            <div className="flex flex-col">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Course</label>
              <select
                className="mt-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm"
                value={selectedCourse ?? ""}
                onChange={(e) => setSelectedCourse(Number(e.target.value))}
              >
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.code} · {course.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Week filter</label>
              <input
                type="number"
                name="week"
                min={1}
                max={14}
                placeholder="Any week"
                className="mt-1 w-32 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm"
                defaultValue={weekFilter}
              />
            </div>
            <div className="flex flex-col">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Source</label>
              <select
                className="mt-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm"
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
              >
                <option value="all">All sources</option>
                {sourceOptions.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Type</label>
              <select
                className="mt-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="all">All types</option>
                {typeOptions.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
              >
                Apply filters
              </button>
            </div>
            {actionMessage && (
              <div className="flex items-end text-sm text-emerald-600">{actionMessage}</div>
            )}
          </form>
        </section>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Pending items</h2>
              <p className="text-sm text-gray-500">{selectedCourseLabel}</p>
              <p className="text-xs text-gray-400">
                Showing {paginatedPending.length} of {filteredPending.length} items (page {page}/{totalPages})
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={page === 1}
              >
                Previous
              </button>
              <button
                type="button"
                className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={page === totalPages}
              >
                Next
              </button>
              {loadingPending && <p className="text-xs text-gray-400">Refreshing…</p>}
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                checked={allPageSelected}
                onChange={(e) => toggleSelectPage(e.target.checked)}
              />
              Select page ({selectedIds.size} selected)
            </label>
            <button
              type="button"
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 disabled:opacity-40"
              disabled={selectedIds.size === 0 || bulkLoading !== null}
              onClick={() => handleBulkAction(true)}
            >
              {bulkLoading === "approve" ? "Approving…" : "Approve selected"}
            </button>
            <button
              type="button"
              className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40"
              disabled={selectedIds.size === 0 || bulkLoading !== null}
              onClick={() => handleBulkAction(false)}
            >
              {bulkLoading === "reject" ? "Processing…" : "Reject selected"}
            </button>
          </div>

          <div className="mt-6 space-y-4">
            {!loadingPending && filteredPending.length === 0 && (
              <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">No materials match your filters.</p>
            )}

            {paginatedPending.map((item) => {
              const sourceLabel = item.material?.source || "Unknown";
              const typeLabel = item.material?.type || "Unknown";
              const isSelected = selectedIds.has(item.mapping_id);
              return (
                <div key={item.mapping_id} className="rounded-xl border border-gray-100 p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        checked={isSelected}
                        onChange={() => toggleSelect(item.mapping_id)}
                      />
                      <div>
                        <p className="text-sm font-semibold text-gray-900">
                          Week {item.week_number}: {item.material?.title ?? "Untitled resource"}
                        </p>
                        <p className="text-xs text-gray-500">
                          Source {sourceLabel} · Type {typeLabel}
                        </p>
                        <p className="text-xs text-gray-400">Relevance score {(item.relevance_score * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                    <a
                      href={item.material?.url ?? "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                    >
                      Open resource ↗
                    </a>
                  </div>

                  <div className="mt-4 flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      disabled={isApproving === item.mapping_id}
                      className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 disabled:opacity-60"
                      onClick={() => handleApproval(item.mapping_id, true)}
                    >
                      {isApproving === item.mapping_id ? "Approving…" : "Approve"}
                    </button>
                    <button
                      type="button"
                      disabled={isApproving === item.mapping_id}
                      className="rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
                      onClick={() => handleApproval(item.mapping_id, false)}
                    >
                      {isApproving === item.mapping_id ? "Processing…" : "Reject"}
                    </button>
                    <span className="text-xs text-gray-400">Material #{item.material_id} · Mapping #{item.mapping_id}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}

export default function MaterialsApprovalPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 px-4 py-10">
          <div className="mx-auto max-w-6xl">
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">Loading page...</p>
            </div>
          </div>
        </div>
      }
    >
      <MaterialsContent />
    </Suspense>
  );
}
