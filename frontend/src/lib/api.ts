const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE) {
  console.warn("NEXT_PUBLIC_API_BASE_URL is not set");
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = (await res.json()) as any;
      if (data?.detail) message = data.detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message || "Request failed");
  }

  return (await res.json()) as T;
}
