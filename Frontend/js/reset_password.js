import { apiFetch } from "./auth.js";
import { initLanguageControls, t } from "./i18n.js";

const form = document.getElementById("resetPasswordForm");
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

  const params = new URLSearchParams(window.location.search);
  const tokenInput = document.getElementById("token");
  if (tokenInput && params.get("token")) {
    tokenInput.value = params.get("token");
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const token = document.getElementById("token").value.trim();
    const newPassword = document.getElementById("newPassword").value;

    submitBtn.disabled = true;
    submitBtn.textContent = t("common.loading");

    try {
      const data = await apiFetch("/api/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
        skipAuthRedirect: true,
      });
      showMessage(data.message || "Password reset successful.");
      form.reset();
    } catch (error) {
      showError(error.message || t("error.network"));
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = t("auth.reset.submit");
    }
  });
});
