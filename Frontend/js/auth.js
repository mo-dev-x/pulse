console.log("auth.js loaded");

export const API = "http://127.0.0.1:5000";

const PERSISTENT_TOKEN_KEY = "pulse_token";
const SESSION_TOKEN_KEY = "pulse_session_token";

export function saveToken(token, rememberMe = true) {
  if (rememberMe) {
    localStorage.setItem(PERSISTENT_TOKEN_KEY, token);
    sessionStorage.removeItem(SESSION_TOKEN_KEY);
  } else {
    sessionStorage.setItem(SESSION_TOKEN_KEY, token);
    localStorage.removeItem(PERSISTENT_TOKEN_KEY);
  }
}

export function getToken() {
  return (
    localStorage.getItem(PERSISTENT_TOKEN_KEY) ||
    sessionStorage.getItem(SESSION_TOKEN_KEY)
  );
}

export function isLoggedIn() {
  return getToken() !== null;
}

export function logout() {
  localStorage.removeItem(PERSISTENT_TOKEN_KEY);
  sessionStorage.removeItem(SESSION_TOKEN_KEY);
  window.location.href = "login.html";
}

export function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "login.html";
  }
}

export function redirectIfLoggedIn() {
  if (isLoggedIn()) {
    window.location.href = "feed.html";
  }
}

export async function apiFetch(path, options = {}) {
  const url = API + path;

  const headers = { ...(options.headers || {}) };
  const token = getToken();

  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }

  const isFormData = options.body instanceof FormData;

  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, {
    method: options.method || "GET",
    body: options.body,
    headers
  });

  let data = {};
  const contentType = res.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (!res.ok) {
    if (typeof data === "object") {
      throw new Error(data.message || data.error || "API error");
    }
    throw new Error(data || "API error");
  }

  return data;
}