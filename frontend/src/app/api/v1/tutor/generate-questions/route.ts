
import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300; // 5 minutes

export async function POST(req: NextRequest) {
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
    const url = `${API_BASE}/tutor/generate-questions${req.nextUrl.search}`;

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
