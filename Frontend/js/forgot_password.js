import { apiFetch } from "./auth.js";
import { initLanguageControls, t } from "./i18n.js";

const form = document.getElementById("forgotPasswordForm");
const errorEl = document.getElementById("error");
const msgEl = document.getElementById("msg");

function showError(message) {
  errorEl.textContent = message;
  errorEl.style.display = "block";
  msgEl.style.display = "none";
}

function showMessage(message) {
  msgEl.textContent = message;
  msgEl.style.display = "block";
  errorEl.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
  initLanguageControls();

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const email = document.getElementById("email").value.trim();

    submitBtn.disabled = true;
    submitBtn.textContent = t("common.loading");

    try {
      const data = await apiFetch("/api/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
        skipAuthRedirect: true,
      });
      showMessage(data.message || "Reset link sent.");
    } catch (error) {
      showError(error.message || t("error.network"));
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = t("auth.forgot.submit");
    }
  });
});
