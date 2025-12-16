"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";
import { AdminLayout } from "@/components/admin/AdminLayout";

type CrawlLogItem = {
    id: number;
    crawler_type: string;
    status: string;
    items_fetched: number;
    error_message: string | null;
    started_at: string;
    finished_at: string | null;
};

type RecStats = {
    total_materials: number;
    materials_with_embeddings: number;
    total_mappings: number;
    approved_mappings: number;
    pending_mappings: number;
    avg_quality_score: number;
};

export default function AdminHealthPage() {
    const { loading: authLoading, authorized } = useRequireRole(["super_admin"]);
    const [logs, setLogs] = useState<CrawlLogItem[]>([]);
    const [stats, setStats] = useState<RecStats | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (authLoading) return;
        if (!authorized) return;
        const token = localStorage.getItem("access_token");
        if (!token) return;

        async function loadData() {
            setIsLoading(true);
            try {
                const [logsRes, statsRes] = await Promise.all([
                    apiFetch<CrawlLogItem[]>("/api/v1/admin/crawl-logs?limit=20", {
                        headers: { Authorization: `Bearer ${token}` },
                    }),
                    apiFetch<RecStats>("/api/v1/admin/stats/recommendations", {
                        headers: { Authorization: `Bearer ${token}` },
                    })
                ]);
                setLogs(logsRes);
                setStats(statsRes);
            } catch (err: any) {
                setError(err.message ?? "Failed to load health data");
            } finally {
                setIsLoading(false);
            }
        }

        loadData();
    }, [authLoading, authorized]);

    function formatDate(dateStr: string) {
        if (!dateStr) return "-";
        return new Date(dateStr).toLocaleString();
    }

    if (authLoading || isLoading) {
        return (
            <AdminLayout headerTitle="System Health">
                <div className="rounded-xl bg-white p-6 shadow-sm">
                    <p className="text-sm text-gray-500">Loading health check...</p>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout headerTitle="System Health" headerSubtitle="Monitor AI pipeline and data crawlers">
            <div className="flex flex-col gap-8">

                {/* Section 1: AI Health */}
                <section>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Recommendation Engine</h2>
                    {stats && (
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <HealthCard label="Materials Vectorized" value={`${stats.materials_with_embeddings} / ${stats.total_materials}`} />
                            <HealthCard label="Topic Mappings" value={stats.total_mappings} subtext={`${stats.pending_mappings} pending approval`} />
                            <HealthCard label="Avg Quality Score" value={stats.avg_quality_score.toFixed(2)} />
                            <HealthCard
                                label="Pipeline Status"
                                value={stats.materials_with_embeddings === stats.total_materials ? "Healthy" : "Processing"}
                                success={stats.materials_with_embeddings === stats.total_materials}
                            />
                        </div>
                    )}
                </section>

                {/* Section 2: Crawler Logs */}
                <section>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Crawler Jobs</h2>
                    <div className="rounded-2xl bg-white p-6 shadow-sm">
                        <div className="overflow-hidden rounded-xl border border-gray-100">
                            <table className="min-w-full divide-y divide-gray-100 text-sm">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
                                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Crawler</th>
                                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Items</th>
                                        <th className="px-4 py-3 text-left font-semibold text-gray-700">Time</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50 bg-white">
                                    {logs.map((log) => (
                                        <tr key={log.id} className="hover:bg-gray-50/50">
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${log.status === "completed" ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20" :
                                                        log.status === "failed" ? "bg-red-50 text-red-700 ring-red-600/20" :
                                                            "bg-blue-50 text-blue-700 ring-blue-600/20"
                                                    }`}>
                                                    {log.status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 font-medium text-gray-900">{log.crawler_type}</td>
                                            <td className="px-4 py-3 text-gray-600">{log.items_fetched}</td>
                                            <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                                                <div>{formatDate(log.started_at)}</div>
                                                {log.error_message && <div className="text-xs text-red-500 max-w-xs truncate">{log.error_message}</div>}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {logs.length === 0 && (
                                <div className="p-8 text-center text-gray-500">No crawler logs found.</div>
                            )}
                        </div>
                    </div>
                </section>
            </div>
        </AdminLayout>
    );
}

function HealthCard({ label, value, subtext, success }: { label: string, value: string | number, subtext?: string, success?: boolean }) {
    return (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">{label}</p>
            <p className={`mt-2 text-2xl font-semibold ${success === true ? "text-emerald-600" : success === false ? "text-amber-600" : "text-gray-900"}`}>{value}</p>
            {subtext && <p className="mt-1 text-xs text-gray-500">{subtext}</p>}
        </div>
    );
}
