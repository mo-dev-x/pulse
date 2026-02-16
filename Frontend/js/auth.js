console.log("auth.js loadeddd");

export const API = "http://127.0.0.1:5000";
const PERSISTENT_TOKEN_KEY = "pulse_token";
const SESSION_TOKEN_KEY = "pulse_session_token";

export function saveToken(token, rememberMe = true) {
  if (rememberMe) {
    localStorage.setItem(PERSISTENT_TOKEN_KEY, token);
    sessionStorage.removeItem(SESSION_TOKEN_KEY);
    return;
  }
  sessionStorage.setItem(SESSION_TOKEN_KEY, token);
  localStorage.removeItem(PERSISTENT_TOKEN_KEY);
}

export function getToken() {
  return (
    localStorage.getItem(PERSISTENT_TOKEN_KEY) ||
    sessionStorage.getItem(SESSION_TOKEN_KEY)
  );
}

export function isLoggedIn() {
  return getToken() !== null; //true si t existe
}

export function logout() {
  localStorage.removeItem(PERSISTENT_TOKEN_KEY);
  sessionStorage.removeItem(SESSION_TOKEN_KEY);
}
window.logout = logout;

//appel backend

export async function apiFetch(path, options = {}) {
  const url = API + path;
  const headers = {};
  headers["Content-Type"] = "application/json"; //on envoie du JSON
  const token = getToken();
  if (token){
    headers["Authorization"] = "Bearer " + token; //ajouter le token dans les headers ->connected
  }
  if (options.headers){
    for (const key in options.headers){
      headers[key] = options.headers[key]; //fusionner les headers
    }
  }

  const res = await fetch(url,options = {
    method: options.method || "GET",
    body: options.body,
    headers: headers
  });

  const data = await res.json(); //lire la reponse mlbackend
  if (res.ok === false){
    throw new Error(data.message|| data.error || "API error");
  }
  return data;
}


//use on feed page
function requireLogin() {
  if (!isLoggedIn()) window.location.href = "login.html";
}

// //use on login/register pages
export function redirectIfLoggedIn() {
  if (isLoggedIn()) window.location.href = "feed.html";
}
