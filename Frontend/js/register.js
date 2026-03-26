import {
  apiFetch,
  redirectIfLoggedIn,
  saveCurrentUser,
  saveToken,
} from "./auth.js";
import { initLanguageControls, t } from "./i18n.js";

const form = document.getElementById("registerForm");
const errorEl = document.getElementById("error");
const submitBtn = form?.querySelector('button[type="submit"]');

function showError(message) {
  errorEl.textContent = message;
  errorEl.style.display = "block";
}

function hideError() {
  errorEl.textContent = "";
  errorEl.style.display = "none";
}

function isUlaval(email) {
  return email.toLowerCase().endsWith("@ulaval.ca");
}

function setSubmitting(isSubmitting) {
  if (!submitBtn) return;
  submitBtn.disabled = isSubmitting;
  submitBtn.textContent = isSubmitting ? t("common.loading") : t("auth.register.submit");
}

document.addEventListener("DOMContentLoaded", () => {
  initLanguageControls();
  redirectIfLoggedIn();

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const username = document.getElementById("username").value.trim();

    if (!isUlaval(email)) {
      showError(t("error.invalid_ulaval_email"));
      return;
    }

    if (password.length < 8) {
      showError(t("error.password_short"));
      return;
    }

    if (!username) {
      showError(t("error.username_required"));
      return;
    }

    setSubmitting(true);

    try {
      const data = await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          username,
          display_name: username,
        }),
        skipAuthRedirect: true,
      });

      const token = data.token || data.access_token;
      if (!token) {
        throw new Error("No token returned by backend");
      }

      saveToken(token, true);
      if (data.user) saveCurrentUser(data.user);
      window.location.href = `verify-email.html?email=${encodeURIComponent(email)}&new=1`;
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
