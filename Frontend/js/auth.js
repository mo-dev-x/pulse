function getApiBaseUrl() {
  return localStorage.getItem("useRemoteApi") === "true"
    ? "https://pulse-backend.up.railway.app"
    : "http://127.0.0.1:5000";
}

export const API = getApiBaseUrl();
window.PULSE_API_BASE = API;

const PERSISTENT_TOKEN_KEY = "pulse_token";
const SESSION_TOKEN_KEY = "pulse_session_token";
const USER_KEY = "pulse_user";
const PUBLIC_ROUTES = new Set([
  "/login.html",
  "/register.html",
  "/forgot-password.html",
  "/reset-password.html",
  "/verify-email.html",
  "/index.html",
  "/",
]);

export function buildApiUrl(path = "") {
  if (!path) return API;
  if (/^https?:\/\//i.test(path)) return path;

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API}${normalizedPath}`;
}

export function getAssetUrl(path, fallback = "") {
  if (!path) return fallback;
  if (/^https?:\/\//i.test(path)) return path;

  const clean = String(path).replace(/^\/+/, "");
  if (!clean) return fallback;

  if (clean.startsWith("uploads/")) {
    return `${API}/${clean}`;
  }

  return `${API}/uploads/${clean}`;
}

export function saveToken(token, rememberMe = true) {
  if (!token) return;

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

export function saveCurrentUser(user) {
  if (!user) return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getCurrentUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isLoggedIn() {
  return !!getToken();
}

export function clearToken() {
  localStorage.removeItem(PERSISTENT_TOKEN_KEY);
  sessionStorage.removeItem(SESSION_TOKEN_KEY);
}

export function clearAuthState() {
  clearToken();
  localStorage.removeItem(USER_KEY);
}

function shouldRedirectToLogin() {
  if (typeof window === "undefined") return false;
  return !PUBLIC_ROUTES.has(window.location.pathname);
}

export async function logout({ redirectTo = "login.html" } = {}) {
  const token = getToken();

  try {
    if (token) {
      await fetch(buildApiUrl("/api/auth/logout"), {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Accept-Language": localStorage.getItem("pulse_lang") || "en",
        },
      });
    }
  } catch {
    // Best-effort logout; client-side cleanup remains the source of truth here.
  } finally {
    clearAuthState();
    if (typeof window !== "undefined") {
      window.location.href = redirectTo;
    }
  }
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

function parseResponsePayload(res, contentType) {
  if (contentType.includes("application/json")) {
    return res.json();
  }
  return res.text();
}

function resolveErrorMessage(payload, fallback = "API error") {
  if (typeof payload === "object" && payload) {
    return payload.message || payload.error || fallback;
  }
  return payload || fallback;
}

export async function apiFetch(path, options = {}) {
  const url = buildApiUrl(path);
  const token = getToken();
  const headers = {
    "Accept-Language": localStorage.getItem("pulse_lang") || "en",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const isFormData = options.body instanceof FormData;
  if (!isFormData && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  let res;
  try {
    res = await fetch(url, {
      method: options.method || "GET",
      body: options.body,
      headers,
    });
  } catch (error) {
    const isNetworkLike = error instanceof TypeError || /fetch/i.test(String(error?.message || ""));
    if (isNetworkLike) {
      throw new Error(
        "Unable to reach the API. Check that the backend is running and that its CORS settings allow this frontend origin."
      );
    }
    throw error;
  }

  const contentType = res.headers.get("content-type") || "";
  const payload = await parseResponsePayload(res, contentType);

  if (res.status === 401) {
    clearAuthState();
    if (!options.skipAuthRedirect && shouldRedirectToLogin()) {
      window.location.href = "login.html?reason=session-expired";
    }
  }

  if (!res.ok) {
    throw new Error(resolveErrorMessage(payload));
  }

  return payload;
}
