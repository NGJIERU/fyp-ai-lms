"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";

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
  const { loading: authLoading, authorized } = useRequireRole(["super_admin"]);
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formState, setFormState] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "student",
    is_active: true,
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!authorized) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;

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
  }, [router, authLoading, authorized]);

  const roleCounts = useMemo(() => {
    if (!stats) return [];
    return Object.entries(stats.users_by_role);
  }, [stats]);

  function openCreateModal() {
    setEditingUser(null);
    setFormState({
      full_name: "",
      email: "",
      password: "",
      role: "student",
      is_active: true,
    });
    setCreateModalOpen(true);
  }

  function openEditModal(user: User) {
    setEditingUser(user);
    setFormState({
      full_name: user.full_name ?? "",
      email: user.email,
      password: "",
      role: user.role,
      is_active: user.is_active,
    });
    setCreateModalOpen(true);
  }

  async function handleDelete(user: User) {
    if (!confirm(`Delete ${user.email}? This cannot be undone.`)) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;
    setSubmitting(true);
    try {
      await apiFetch(`/api/v1/admin/users/${user.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
      setStats((prev) => {
        if (!prev) return prev;
        const newTotal = Math.max(prev.total_users - 1, 0);
        const roleKey = user.role;
        const roleCount = Math.max((prev.users_by_role[roleKey] ?? 1) - 1, 0);
        return {
          ...prev,
          total_users: newTotal,
          users_by_role: {
            ...prev.users_by_role,
            [roleKey]: roleCount,
          },
        };
      });
    } catch (err: any) {
      alert(err.message || "Failed to delete user");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const token = localStorage.getItem("access_token");
    if (!token) return;
    setSubmitting(true);
    try {
      if (editingUser) {
        const updated = await apiFetch<User>(`/api/v1/admin/users/${editingUser.id}`, {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            full_name: formState.full_name,
            email: formState.email,
            role: formState.role,
            is_active: formState.is_active,
            password: formState.password || undefined,
          }),
        });
        setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
        setStats((prev) => {
          if (!prev) return prev;
          if (editingUser.role === updated.role) return prev;
          const oldRoleCount = Math.max((prev.users_by_role[editingUser.role] ?? 1) - 1, 0);
          const newRoleCount = (prev.users_by_role[updated.role] ?? 0) + 1;
          return {
            ...prev,
            users_by_role: {
              ...prev.users_by_role,
              [editingUser.role]: oldRoleCount,
              [updated.role]: newRoleCount,
            },
          };
        });
      } else {
        const created = await apiFetch<User>("/api/v1/admin/users", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            full_name: formState.full_name,
            email: formState.email,
            role: formState.role,
            password: formState.password || "password123",
            is_active: formState.is_active,
          }),
        });
        setUsers((prev) => [created, ...prev]);
        setStats((prev) => {
          if (!prev) return prev;
          const roleKey = created.role;
          return {
            ...prev,
            total_users: prev.total_users + 1,
            users_by_role: {
              ...prev.users_by_role,
              [roleKey]: (prev.users_by_role[roleKey] ?? 0) + 1,
            },
          };
        });
      }
      setCreateModalOpen(false);
    } catch (err: any) {
      alert(err.message || "Failed to save user");
    } finally {
      setSubmitting(false);
    }
  }

  if (authLoading || isLoading) {
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
                onClick={openCreateModal}
              >
                Add user
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
                      <td className="px-4 py-3 space-x-3 text-right">
                        <button
                          className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                          onClick={() => openEditModal(user)}
                        >
                          Edit
                        </button>
                        <button
                          className="text-sm font-medium text-rose-600 hover:text-rose-500 disabled:opacity-40"
                          onClick={() => handleDelete(user)}
                          disabled={submitting}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {createModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
            <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingUser ? "Edit user" : "Create user"}
                </h3>
                <button className="text-gray-400 hover:text-gray-600" onClick={() => setCreateModalOpen(false)}>
                  ×
                </button>
              </div>

              <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Full name</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    value={formState.full_name}
                    onChange={(e) => setFormState((prev) => ({ ...prev, full_name: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <input
                    type="email"
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    value={formState.email}
                    onChange={(e) => setFormState((prev) => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Password {editingUser && <span className="text-gray-400">(leave blank to keep current)</span>}
                  </label>
                  <input
                    type="password"
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    value={formState.password}
                    onChange={(e) => setFormState((prev) => ({ ...prev, password: e.target.value }))}
                    required={!editingUser}
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Role</label>
                    <select
                      className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      value={formState.role}
                      onChange={(e) => setFormState((prev) => ({ ...prev, role: e.target.value }))}
                    >
                      <option value="student">Student</option>
                      <option value="lecturer">Lecturer</option>
                      <option value="super_admin">Super admin</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2 pt-6">
                    <input
                      id="is_active"
                      type="checkbox"
                      className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      checked={formState.is_active}
                      onChange={(e) => setFormState((prev) => ({ ...prev, is_active: e.target.checked }))}
                    />
                    <label htmlFor="is_active" className="text-sm text-gray-700">
                      Active
                    </label>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4">
                  <button
                    type="button"
                    className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    onClick={() => setCreateModalOpen(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-60"
                  >
                    {submitting ? "Saving..." : editingUser ? "Save changes" : "Create user"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
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
