"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

type LoginResponse = {
  access_token: string;
  token_type: string;
  // extend with more fields from backend if needed
};

type MeResponse = {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
};

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username: email,
          password,
        }).toString(),
      });

      if (!res.ok) {
        let message = "Login failed";
        try {
          const data = (await res.json()) as any;
          if (data?.detail) message = data.detail;
        } catch {
          // ignore
        }
        throw new Error(message);
      }

      const data = (await res.json()) as LoginResponse;

      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", data.access_token);
      }
      await redirectByRole();

    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700"
        >
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <div>
        <label
          htmlFor="password"
          className="block text-sm font-medium text-gray-700"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-60"
      >
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>

      <p className="mt-2 text-center text-xs text-gray-500">
        Don&apos;t have an account?{" "}
        <a
          href="/register"
          className="font-medium text-indigo-600 hover:text-indigo-500"
        >
          Register
        </a>
      </p>
    </form>
  );
}

async function redirectByRole() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    window.location.href = "/login";
    return;
  }

  try {
    const me = await apiFetch<MeResponse>("/api/v1/users/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    switch (me.role) {
      case "student":
        window.location.href = "/student/dashboard";
        break;
      case "lecturer":
        window.location.href = "/lecturer/dashboard";
        break;
      case "super_admin":
        window.location.href = "/admin/users";
        break;
      default:
        window.location.href = "/";
    }
  } catch {
    window.location.href = "/";
  }
}
