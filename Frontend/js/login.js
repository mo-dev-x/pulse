import {
  apiFetch,
  saveCurrentUser,
  saveToken,
  redirectIfLoggedIn,
} from "./auth.js";
import { initLanguageControls, t } from "./i18n.js";

const form = document.getElementById("loginForm");
const errorEl = document.getElementById("error");
const msgEl = document.getElementById("msg");
const submitBtn = form?.querySelector('button[type="submit"]');

function showError(message) {
  errorEl.textContent = message;
  errorEl.style.display = "block";
  msgEl.style.display = "none";
}

function showMsg(message) {
  msgEl.textContent = message;
  msgEl.style.display = "block";
  errorEl.style.display = "none";
}

function setSubmitting(isSubmitting) {
  if (!submitBtn) return;
  submitBtn.disabled = isSubmitting;
  submitBtn.textContent = isSubmitting ? t("common.loading") : t("auth.login.submit");
}

document.addEventListener("DOMContentLoaded", () => {
  initLanguageControls();
  redirectIfLoggedIn();

  const params = new URLSearchParams(window.location.search);
  if (params.get("reason") === "session-expired") {
    showError("Your session expired. Please sign in again.");
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const rememberMe = document.getElementById("rememberMe")?.checked ?? false;

    setSubmitting(true);

    try {
      const data = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
        skipAuthRedirect: true,
      });

      const token = data.token || data.access_token;
      if (!token) {
        throw new Error("No token returned by backend");
      }

      saveToken(token, rememberMe);
      if (data.user) saveCurrentUser(data.user);
      showMsg("Login successful. Redirecting...");
      window.location.href = "feed.html";
    } catch (error) {
      showError(error.message || t("error.network"));
    } finally {
      setSubmitting(false);
    }
  });

  const pw = document.getElementById("password");
  const toggle = document.getElementById("togglePassword");
  toggle?.addEventListener("click", () => {
    const reveal = pw.type === "password";
    pw.type = reveal ? "text" : "password";
    toggle.classList.toggle("active", reveal);
  });
});
