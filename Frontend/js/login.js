import { apiFetch,redirectIfLoggedIn, saveToken } from "./auth.js";

console.log("login.js loadeddd");
redirectIfLoggedIn(); //if already logged ->go feed
// if (isLoggedIn()) window.location.href = "feed.html";

const form = document.getElementById("loginForm");
const errorEl = document.getElementById("error");
const msgEl = document.getElementById("msg"); //ymkn na7eha

function showError(text){
  if (!errorEl) return;
  errorEl.textContent = text;
  errorEl.style.display = "block";
}

function hideError(){
  if (!errorEl) return;
  msgEl.style.display = "";
  errorEl.style.display = "none";
}

function showMsg(text){
  if (!msgEl) return;
  msgEl.textContent = text;
  msgEl.style.display = "block";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();hideError();msgEl.style.display = "none";

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const rememberMe = document.getElementById("rememberMe")?.checked ?? false;

  try {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    const token = data.token || data.access_token; //selon backend
    if (!token) throw new Error("No token returned by backend");

    saveToken(token, rememberMe);
    showMsg("Logged in successfullyyy");
    window.location.href = "feed.html";
  } catch (err) {
    showError(err.message|| "Login failed");
  }

// //show/hide password mazelt
// toggle.addEventListener("click", () => {
//   if (pw.type === "password") {
//     pw.type = "text";
//     toggle.textContent = "Hide";
//   } else {
//     pw.type = "password";
//     toggle.textContent = "Show";
//   }
// });

});
