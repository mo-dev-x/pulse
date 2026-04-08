import { apiFetch } from "./auth.js";
import { initLanguageControls, t } from "./i18n.js";

const form    = document.getElementById("resetPasswordForm");
const errorEl = document.getElementById("error");
const msgEl   = document.getElementById("msg");

function showError(message) {
  errorEl.textContent = message;
  errorEl.style.display = "block";
  msgEl.style.display   = "none";
}

function showMessage(message) {
  msgEl.textContent   = message;
  msgEl.style.display = "block";
  errorEl.style.display = "none";
}

/** Map backend error strings to user-facing messages. */
function friendlyError(raw) {
  const msg = (raw || "").toLowerCase();
  if (msg.includes("expired"))
    return t("auth.reset.error_expired") || "This reset link has expired. Please request a new one.";
  if (msg.includes("invalid") || msg.includes("not found"))
    return t("auth.reset.error_invalid") || "This reset link is invalid. Please request a new one.";
  return raw || t("error.network") || "Something went wrong. Please try again.";
}

document.addEventListener("DOMContentLoaded", () => {
  initLanguageControls();

  const params     = new URLSearchParams(window.location.search);
  const urlToken   = params.get("token") || "";
  const tokenInput = document.getElementById("token");

  // Pre-fill token from URL and hide the token field — user never needs to see it
  if (tokenInput) {
    tokenInput.value = urlToken;
    // Only hide the field when the token came from the link; leave visible when
    // the user navigates directly so they can paste it manually.
    if (urlToken) {
      const tokenLabel = document.querySelector('label[for="token"]');
      if (tokenLabel) tokenLabel.style.display = "none";
      tokenInput.style.display = "none";
    }
  }

  // Warn immediately if no token is present in the URL at all
  if (!urlToken) {
    showError(
      t("auth.reset.error_no_token") ||
      "No reset token found. Please use the link from your email or request a new one."
    );
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitBtn  = form.querySelector('button[type="submit"]');
    const token      = tokenInput?.value.trim() || "";
    const newPassword = document.getElementById("newPassword")?.value || "";

    if (!token) {
      showError(t("auth.reset.error_no_token") || "Reset token is missing.");
      return;
    }

    submitBtn.disabled    = true;
    submitBtn.textContent = t("common.loading") || "Loading…";
    errorEl.style.display = "none";
    msgEl.style.display   = "none";

    try {
      const data = await apiFetch("/api/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password: newPassword }),
        skipAuthRedirect: true,
      });

      showMessage(data.message || t("auth.reset.success") || "Password reset successful!");
      form.reset();
      // Give the user a moment to read the success message, then redirect to login
      setTimeout(() => { window.location.href = "login.html"; }, 2500);
    } catch (err) {
      showError(friendlyError(err.message));
      // On expired/invalid token, offer a quick link to request a new one
      const msg = (err.message || "").toLowerCase();
      if (msg.includes("expired") || msg.includes("invalid")) {
        const link = document.createElement("a");
        link.href      = "forgot-password.html";
        link.className = "link";
        link.textContent = t("auth.reset.request_new") || " Request a new link";
        link.style.display = "block";
        link.style.marginTop = "8px";
        errorEl.appendChild(link);
      }
    } finally {
      submitBtn.disabled    = false;
      submitBtn.textContent = t("auth.reset.submit") || "Reset password";
    }
  });
});
