"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { apiFetch } from "@/lib/api";

const HEARTBEAT_INTERVAL = 30000; // 30 seconds

export function useStudyTracker() {
    const pathname = usePathname();
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        // Only track if authenticated user is on student pages
        // (Actual auth check happens via token presence in apiFetch or helper)

        const sendHeartbeat = async () => {
            // Don't track if page is hidden
            if (document.hidden) return;

            const token = localStorage.getItem("access_token");
            if (!token) return;

            // Extract course ID from URL if present
            const courseMatch = pathname.match(/\/student\/course\/(\d+)/);
            const courseId = courseMatch ? parseInt(courseMatch[1]) : null;

            try {
                await apiFetch("/api/v1/analytics/heartbeat", {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` },
                    body: JSON.stringify({
                        course_id: courseId,
                        page_url: pathname
                    })
                });
            } catch (err) {
                // Silently fail for analytics
                console.warn("Heartbeat failed", err);
            }
        };

        // Initial heartbeat
        sendHeartbeat();

        // Start interval
        intervalRef.current = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);

        // Cleanup
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [pathname]);

    // Handle visibility change to pause/resume immediately
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden) {
                if (intervalRef.current) clearInterval(intervalRef.current);
            } else {
                // Resume immediately
                // We could trigger an immediate heartbeat here too
            }
        };

        document.addEventListener("visibilitychange", handleVisibilityChange);
        return () => {
            document.removeEventListener("visibilitychange", handleVisibilityChange);
        };
    }, []);
}
