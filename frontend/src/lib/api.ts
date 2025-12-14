const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE) {
  console.warn("NEXT_PUBLIC_API_BASE_URL is not set");
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  // Auto-include auth token if available
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers ?? {}),
    },
  });

  const contentType = res.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const bodyText = await res.text();

  if (!res.ok) {
    let message = res.statusText;
    if (isJson && bodyText) {
      try {
        const data = JSON.parse(bodyText) as any;
        if (data?.detail) message = data.detail;
      } catch {
        // ignore JSON parse errors
      }
    }
    throw new Error(message || "Request failed");
  }

  if (!bodyText.trim()) {
    return undefined as T;
  }

  if (isJson) {
    try {
      return JSON.parse(bodyText) as T;
    } catch {
      // ignore JSON parse errors
    }
  }

  return undefined as T;
}
