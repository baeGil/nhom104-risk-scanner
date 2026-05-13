export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
}

export interface ApiError {
  message: string;
  status: number;
  code?: string;
}

const defaultConfig: ApiConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  timeout: 30000,
  retries: 2,
};

async function getAuthToken(): Promise<string | null> {
  try {
    const res = await fetch("/api/auth/session");
    if (!res.ok) return null;
    const session = await res.json();
    return session?.accessToken || null;
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  config: Partial<ApiConfig> = {}
): Promise<T> {
  const { baseUrl, timeout, retries } = { ...defaultConfig, ...config };
  const url = `${baseUrl}${endpoint}`;

  const token = await getAuthToken();
  const authHeaders: Record<string, string> = {};
  if (token) {
    authHeaders["Authorization"] = `Bearer ${token}`;
  }

  let lastError: ApiError | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (response.status === 401) {
        window.location.href = "/login?callbackUrl=" + encodeURIComponent(window.location.pathname);
        throw { message: "Unauthorized", status: 401 } as ApiError;
      }

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        throw {
          message: errorBody?.detail || errorBody?.message || response.statusText,
          status: response.status,
          code: errorBody?.code,
        } as ApiError;
      }

      return await response.json();
    } catch (error) {
      lastError = error as ApiError;
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
      }
    }
  }

  throw lastError || { message: "Unknown error", status: 500 };
}

export async function apiSSE<T>(
  endpoint: string,
  body: Record<string, unknown>,
  onChunk: (data: T) => void,
  config: Partial<ApiConfig> = {}
): Promise<void> {
  const { baseUrl } = { ...defaultConfig, ...config };
  const url = `${baseUrl}${endpoint}`;

  const token = await getAuthToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (response.status === 401) {
    window.location.href = "/login?callbackUrl=" + encodeURIComponent(window.location.pathname);
    throw { message: "Unauthorized", status: 401 } as ApiError;
  }

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw {
      message: error?.detail || error?.message || response.statusText,
      status: response.status,
    } as ApiError;
  }

  const reader = response.body?.getReader();
  if (!reader) throw { message: "No response body", status: 500 };

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") return;
        try {
          onChunk(JSON.parse(data));
        } catch {
          // Skip malformed chunks
        }
      }
    }
  }
}
