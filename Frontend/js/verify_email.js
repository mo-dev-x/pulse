import { apiFetch, getCurrentUser, isLoggedIn, saveCurrentUser } from "./auth.js";
import { initLanguageControls, t } from "./i18n.js";

const params = new URLSearchParams(window.location.search);
const token = (params.get("token") || "").trim();
const email = params.get("email") || getCurrentUser()?.email || "—";

const pendingEmail = document.getElementById("pendingEmail");
const statusBox = document.getElementById("statusBox");
const resendBtn = document.getElementById("resendVerification");
const continueBtn = document.getElementById("continueToFeed");

function showStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.style.display = "block";
  statusBox.className = isError ? "error" : "msg";
}

async function verifyEmailToken() {
  if (!token) return;

  try {
    const data = await apiFetch(`/api/auth/verify-email/${encodeURIComponent(token)}`, {
      method: "GET",
      skipAuthRedirect: true,
    });
    if (data.user) saveCurrentUser(data.user);
    showStatus(data.message || t("common.success"));
  } catch (error) {
    // If the token is invalid/expired but the user is already verified (e.g. they
    // clicked an old link after already verifying), show a success message instead.
    const cached = getCurrentUser();
    if (cached?.is_verified) {
      showStatus(t("common.success"));
      return;
    }
    // Try a fresh profile fetch to catch cases where localStorage is stale.
    if (isLoggedIn()) {
      try {
        const profile = await apiFetch("/api/auth/me", { skipAuthRedirect: true });
        if (profile?.user?.is_verified || profile?.is_verified) {
          if (profile.user) saveCurrentUser(profile.user);
          showStatus(t("common.success"));
          return;
        }
      } catch (_) { /* ignore */ }
    }
    showStatus(error.message || t("error.network"), true);
  }
}

async function resendVerification() {
  if (!isLoggedIn()) {
    showStatus("Please log in again to resend verification.", true);
    return;
  }

  resendBtn.disabled = true;
  resendBtn.textContent = t("common.loading");

  try {
    const data = await apiFetch("/api/auth/send-verification", { method: "POST" });
    showStatus(data.message || "Verification email sent.");
  } catch (error) {
    showStatus(error.message || t("error.network"), true);
  } finally {
    resendBtn.disabled = false;
    resendBtn.textContent = t("auth.verify.resend");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  initLanguageControls();
  if (pendingEmail) pendingEmail.textContent = email;
  resendBtn?.addEventListener("click", resendVerification);
  continueBtn?.addEventListener("click", () => {
    window.location.href = "feed.html";
  });
  await verifyEmailToken();
});
