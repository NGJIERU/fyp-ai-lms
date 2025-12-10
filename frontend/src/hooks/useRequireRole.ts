"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type MeResponse = {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
};

export function useRequireRole(allowedRoles: string[]) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }

    let cancelled = false;

    async function validate() {
      try {
        const me = await apiFetch<MeResponse>("/api/v1/users/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (cancelled) return;

        if (allowedRoles.includes(me.role)) {
          setAuthorized(true);
        } else {
          router.replace("/");
        }
      } catch (err) {
        if (!cancelled) {
          router.replace("/login");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    validate();

    return () => {
      cancelled = true;
    };
  }, [allowedRoles, router]);

  return { loading, authorized };
}
