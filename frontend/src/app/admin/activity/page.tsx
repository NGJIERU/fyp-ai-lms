"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";
import { AdminLayout } from "@/components/admin/AdminLayout";

type ActivityLogItem = {
    id: number;
    user_id: number;
    user_email: string | null;
    action: string;
    resource_type: string | null;
    resource_id: number | null;
    created_at: string;
};

export default function AdminActivityPage() {
    const { loading: authLoading, authorized } = useRequireRole(["super_admin"]);
    const [logs, setLogs] = useState<ActivityLogItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [page, setPage] = useState(1);
    const LIMIT = 50;

    useEffect(() => {
        if (authLoading) return;
        if (!authorized) return;
        const token = localStorage.getItem("access_token");
        if (!token) return;

        async function loadData() {
            setIsLoading(true);
            try {
                const queryParams = new URLSearchParams({
                    skip: ((page - 1) * LIMIT).toString(),
                    limit: LIMIT.toString(),
                    days: "30" // Fetch last 30 days by default
                });

                const res = await apiFetch<ActivityLogItem[]>(`/api/v1/admin/activity-logs?${queryParams.toString()}`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                setLogs(res);
            } catch (err: any) {
                setError(err.message ?? "Failed to load activity logs");
            } finally {
                setIsLoading(false);
            }
        }

        loadData();
    }, [authLoading, authorized, page]);

    function formatDate(dateStr: string) {
        if (!dateStr) return "-";
        return new Date(dateStr).toLocaleString(undefined, {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    }

    if (authLoading || isLoading) {
        return (
            <AdminLayout headerTitle="System Activity">
                <div className="rounded-xl bg-white p-6 shadow-sm">
                    <p className="text-sm text-gray-500">Loading logs...</p>
                </div>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout headerTitle="System Activity" headerSubtitle="Monitor user actions and system events (Last 30 days)">
            <div className="rounded-2xl bg-white p-6 shadow-sm">
                {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

                {/* Pagination Controls */}
                <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
                    <span className="text-sm text-gray-500">
                        Page {page}
                    </span>
                    <div className="space-x-2">
                        <button
                            className="rounded px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                        >
                            Previous
                        </button>
                        <button
                            className="rounded px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                            onClick={() => setPage(p => p + 1)}
                            disabled={logs.length < LIMIT}
                        >
                            Next
                        </button>
                    </div>
                </div>

                <div className="overflow-hidden rounded-xl border border-gray-100">
                    <table className="min-w-full divide-y divide-gray-100 text-sm">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">Time</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">User</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">Action</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-700">Resource</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50 bg-white">
                            {logs.map((log) => (
                                <tr key={log.id} className="hover:bg-gray-50/50">
                                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{formatDate(log.created_at)}</td>
                                    <td className="px-4 py-3 font-medium text-gray-900">
                                        <div>{log.user_email || "Unknown"}</div>
                                        <div className="text-xs text-gray-400">ID: {log.user_id}</div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">
                                            {log.action}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-gray-600">
                                        {log.resource_type && log.resource_id
                                            ? `${log.resource_type} #${log.resource_id}`
                                            : log.resource_type === 'system'
                                                ? '-'
                                                : log.resource_type
                                                    ? log.resource_type
                                                    : '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {logs.length === 0 && (
                        <div className="p-8 text-center text-gray-500">No activity found in this period.</div>
                    )}
                </div>
            </div>
        </AdminLayout>
    );
}
