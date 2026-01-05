
import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300; // 5 minutes

export async function POST(req: NextRequest) {
    // Use backend URL directly - NEXT_PUBLIC_API_BASE_URL is for frontend routing
    const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
    const url = `${BACKEND_URL}/api/v1/tutor/generate-questions${req.nextUrl.search}`;

    try {
        const body = await req.json();
        const token = req.headers.get("authorization");

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 seconds timeout

        const res = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: token } : {}),
            },
            body: JSON.stringify(body),
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error: any) {
        console.error("Proxy error:", error);
        if (error.name === "AbortError") {
            return NextResponse.json({ error: "Request timed out" }, { status: 504 });
        }
        return NextResponse.json({ error: error.message || "Internal Server Error" }, { status: 500 });
    }
}
