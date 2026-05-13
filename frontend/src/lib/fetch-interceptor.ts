import { broadcastSessionExpired } from "./auth-sync";

if (typeof window !== "undefined") {
  const originalFetch = window.fetch;

  window.fetch = async function (...args) {
    const response = await originalFetch.apply(this, args);

    if (response.status === 401) {
      try {
        const sessionRes = await originalFetch("/api/auth/session", { cache: "no-store" });
        if (!sessionRes.ok) {
          broadcastSessionExpired();
        }
      } catch {
        // Ignore network errors
      }
    }

    return response;
  };
}
