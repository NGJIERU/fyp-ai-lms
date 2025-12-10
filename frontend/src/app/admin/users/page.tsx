"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

type User = {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
};

type SystemStats = {
  total_users: number;
  users_by_role: Record<string, number>;
  total_courses: number;
  total_materials: number;
  total_enrollments: number;
  active_sessions_today: number;
};

export default function AdminUsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    const controller = new AbortController();

    async function loadAdminData() {
      try {
        const [usersRes, statsRes] = await Promise.all([
          apiFetch<User[]>("/api/v1/admin/users", {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          }),
          apiFetch<SystemStats>("/api/v1/admin/stats", {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          }),
        ]);

        setUsers(usersRes);
        setStats(statsRes);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err.message ?? "Unable to load admin dashboard");
      } finally {
        setIsLoading(false);
      }
    }

    loadAdminData();
    return () => controller.abort();
  }, [router]);

  const roleCounts = useMemo(() => {
    if (!stats) return [];
    return Object.entries(stats.users_by_role);
  }, [stats]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Loading admin dashboard…</p>
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

  if (!stats) return null;

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header>
          <p className="text-sm uppercase tracking-wide text-indigo-600">Admin Console</p>
          <h1 className="mt-2 text-3xl font-semibold text-gray-900">
            Welcome back, Super Admin
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Review system health, manage users, and monitor overall activity.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          <SummaryCard label="Total users" value={stats.total_users} subtext="Across all roles" />
          <SummaryCard label="Active enrollments" value={stats.total_enrollments} subtext="Students currently enrolled" />
          <SummaryCard label="Courses" value={stats.total_courses} subtext="Managed in the system" />
          <SummaryCard label="Materials" value={stats.total_materials} subtext="Approved resources" />
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Users by role</h2>
            <div className="mt-4 space-y-3">
              {roleCounts.map(([role, count]) => (
                <div key={role} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
                  <span className="text-sm font-medium text-gray-700 capitalize">{role.replace("_", " ")}</span>
                  <span className="text-sm font-semibold text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl bg-white p-6 shadow-sm lg:col-span-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Users</h2>
              <button
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                disabled
              >
                Add user (coming soon)
              </button>
            </div>
            <div className="mt-4 overflow-hidden rounded-xl border border-gray-100">
              <table className="min-w-full divide-y divide-gray-100 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Name</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Email</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Role</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 bg-white">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-4 py-3 text-gray-900">
                        {user.full_name || "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{user.email}</td>
                      <td className="px-4 py-3 text-gray-600 capitalize">{user.role.replace("_", " ")}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${user.is_active ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"}`}
                        >
                          {user.is_active ? "Active" : "Disabled"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  subtext,
}: {
  label: string;
  value: string | number;
  subtext: string;
}) {
  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
      <p className="mt-2 text-xs text-gray-500">{subtext}</p>
    </div>
  );
}
