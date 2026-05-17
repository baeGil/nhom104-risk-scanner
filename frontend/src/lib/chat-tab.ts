"use client";

const TAB_ID_KEY = "phaply:legal-qa:tab-id";

function createTabId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `tab_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export function getLegalQaTabId(): string {
  if (typeof window === "undefined") return createTabId();

  const existing = window.sessionStorage.getItem(TAB_ID_KEY);
  if (existing) return existing;

  const tabId = createTabId();
  window.sessionStorage.setItem(TAB_ID_KEY, tabId);
  return tabId;
}

export function resetLegalQaTabId(): string {
  if (typeof window === "undefined") return createTabId();

  const tabId = createTabId();
  window.sessionStorage.setItem(TAB_ID_KEY, tabId);
  return tabId;
}
