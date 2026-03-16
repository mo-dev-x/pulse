import { apiFetch, saveToken, redirectIfLoggedIn } from "./auth.js";

// console.log("login.js loaded");

const form = document.getElementById("loginForm");
const errorEl = document.getElementById("error");
const msgEl = document.getElementById("msg");
const submitBtn = form?.querySelector('button[type="submit"]');

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.style.display = "block";
}

function hideError() {
  errorEl.textContent = "";
  errorEl.style.display = "none";
}

function showMsg(msg) {
  msgEl.textContent = msg;
  msgEl.style.display = "block";
}

function hideMsg() {
  msgEl.textContent = "";
  msgEl.style.display = "none";
}

// if already logged in, go to feed
redirectIfLoggedIn();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  hideMsg();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const rememberMe = document.getElementById("rememberMe")?.checked ?? false;
  submitBtn.disabled = true;
  submitBtn.textContent = "Signing in...";

  try {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });

    const token = data.token || data.access_token;
    if (!token) {
      throw new Error("No token returned by backend");
    }

    saveToken(token, rememberMe);
    showMsg("Login successful. Redirecting...");
    window.location.href = "feed.html";
  } catch (err) {
    console.error("Login failed:", err);
    showError(err.message || "Login failed");
  }finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Login";
  }
});

//show/hide password
const pw = document.getElementById("password");
const toggle = document.getElementById("togglePassword");

toggle?.addEventListener("click", () => {
  if (pw.type === "password") {
    pw.type = "text";
    toggle.classList.add("active");
  } else {
    pw.type = "password";
    toggle.classList.remove("active");
  }
});

