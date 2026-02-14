// import { API_BASE } from "./config.js";
// import { getToken, logout } from "./auth.js";

// export async function apiFetch(path, { method="GET", body=null, isForm=false } = {}) {
//   const token = getToken();

//   const headers = {};
//   if (!isForm) headers["Content-Type"] = "application/json";
//   if (token) headers["Authorization"] = `Bearer ${token}`;

//   const res = await fetch(`${API_BASE}${path}`, {
//     method,
//     headers,
//     body: body ? (isForm ? body : JSON.stringify(body)) : null
//   });

//   if (res.status === 401) {
//     logout();
//     window.location.href = "login.html";
//     return;
//   }

//   const text = await res.text();
//   let data = null;
//   try { data = text ? JSON.parse(text) : null; } catch { data = text; }

//   if (!res.ok) throw new Error(data?.message || `HTTP ${res.status}`);

//   return data;
// }

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    ...(options.headers || {}),
  };

  // ✅ Si on envoie du JSON
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // ✅ Ajouter JWT si dispo
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // ✅ Lire JSON si possible
  let data = null;
  try {
    data = await res.json();
  } catch {
    // pas json
  }

  if (!res.ok) {
    const msg = data?.error || data?.message || "Erreur serveur";
    throw new Error(msg);
  }

  return data;
}
