const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

if (!API_BASE) {
  console.warn("NEXT_PUBLIC_API_BASE_URL is not set");
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  // Auto-include auth token if available
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const isFormData = options?.body instanceof FormData;
  const headers: HeadersInit = {
    ...(!isFormData && { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers ?? {}),
  };

  // Handle double-slash issues or double-prefixing
  // If API_BASE is /api/v1 and path starts with /api/v1, strip one
  let url = `${API_BASE}${path}`;
  if (API_BASE && path.startsWith(API_BASE)) {
    url = path; // Path already includes base
  }

  const res = await fetch(url, {
    ...options,
    headers,
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
