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
const resendEl = document.getElementById("resend-verification");
const resendLink = document.getElementById("resend-link");
const submitBtn = form?.querySelector('button[type="submit"]');
const credentialsStep = document.getElementById("credentials-step");
const twoFaStep = document.getElementById("2fa-step");
const totpSection = document.getElementById("totp-section");
const backupSection = document.getElementById("backup-section");
const toggleBackupLink = document.getElementById("toggle-backup");
const backToLoginLink = document.getElementById("back-to-login");
const registerLinkRow = document.getElementById("register-link-row");

// Stored while waiting for 2FA
let pendingCredentials = null;
let usingBackupCode = false;

function showError(message, showResend = false) {
  errorEl.textContent = message;
  errorEl.style.display = "block";
  msgEl.style.display = "none";
  resendEl.style.display = showResend ? "block" : "none";
}

function clearError() {
  errorEl.style.display = "none";
  errorEl.textContent = "";
  resendEl.style.display = "none";
}

function showMsg(message) {
  msgEl.textContent = message;
  msgEl.style.display = "block";
  errorEl.style.display = "none";
  resendEl.style.display = "none";
}

function setSubmitting(isSubmitting) {
  if (!submitBtn) return;
  submitBtn.disabled = isSubmitting;
  const label = pendingCredentials
    ? t("auth.login.2fa_submit")
    : t("auth.login.submit");
  submitBtn.textContent = isSubmitting ? t("common.loading") : label;
}

function show2FA() {
  credentialsStep.style.display = "none";
  twoFaStep.style.display = "block";
  registerLinkRow.style.display = "none";
  submitBtn.setAttribute("data-i18n", "auth.login.2fa_submit");
  submitBtn.textContent = t("auth.login.2fa_submit");
  clearError();
  document.getElementById("totp-code").focus();
}

function reset2FA() {
  pendingCredentials = null;
  usingBackupCode = false;
  credentialsStep.style.display = "block";
  twoFaStep.style.display = "none";
  registerLinkRow.style.display = "";
  totpSection.style.display = "block";
  backupSection.style.display = "none";
  toggleBackupLink.setAttribute("data-i18n", "auth.login.2fa_use_backup");
  toggleBackupLink.textContent = t("auth.login.2fa_use_backup");
  submitBtn.setAttribute("data-i18n", "auth.login.submit");
  submitBtn.textContent = t("auth.login.submit");
  document.getElementById("totp-code").value = "";
  document.getElementById("backup-code").value = "";
  clearError();
}

document.addEventListener("DOMContentLoaded", () => {
  initLanguageControls();
  redirectIfLoggedIn();

  const params = new URLSearchParams(window.location.search);
  if (params.get("reason") === "session-expired") {
    showError(t("auth.login.session_expired"));
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      let body;

      if (pendingCredentials) {
        // 2FA step
        const totpCode = document.getElementById("totp-code").value.trim();
        const backupCode = document.getElementById("backup-code").value.trim();
        body = {
          email: pendingCredentials.email,
          password: pendingCredentials.password,
          ...(usingBackupCode ? { backup_code: backupCode } : { totp_code: totpCode }),
        };
      } else {
        // Credentials step
        body = {
          email: document.getElementById("email").value.trim(),
          password: document.getElementById("password").value,
        };
      }

      const rememberMe = document.getElementById("rememberMe")?.checked ?? false;

      const data = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
        skipAuthRedirect: true,
      });

      const token = data.token || data.access_token;
      if (!token) throw new Error("No token returned by backend");

      saveToken(token, rememberMe);
      if (data.user) saveCurrentUser(data.user);
      showMsg(t("auth.login.success"));
      window.location.href = "feed.html";
    } catch (error) {
      if (error.payload?.requires_2fa && !pendingCredentials) {
        pendingCredentials = {
          email: document.getElementById("email").value.trim(),
          password: document.getElementById("password").value,
        };
        show2FA();
      } else {
        const needsVerification = error.payload?.needs_verification === true;
        showError(error.message || t("error.network"), needsVerification);
        if (needsVerification) {
          resendLink.dataset.email = document.getElementById("email").value.trim();
        }
      }
    } finally {
      setSubmitting(false);
    }
  });

  toggleBackupLink?.addEventListener("click", (event) => {
    event.preventDefault();
    usingBackupCode = !usingBackupCode;
    totpSection.style.display = usingBackupCode ? "none" : "block";
    backupSection.style.display = usingBackupCode ? "block" : "none";
    toggleBackupLink.setAttribute(
      "data-i18n",
      usingBackupCode ? "auth.login.2fa_use_totp" : "auth.login.2fa_use_backup"
    );
    toggleBackupLink.textContent = t(
      usingBackupCode ? "auth.login.2fa_use_totp" : "auth.login.2fa_use_backup"
    );
    clearError();
  });

  backToLoginLink?.addEventListener("click", (event) => {
    event.preventDefault();
    reset2FA();
  });

  resendLink?.addEventListener("click", async (event) => {
    event.preventDefault();
    const email = resendLink.dataset.email;
    if (!email) return;

    resendLink.textContent = t("common.loading");
    try {
      await apiFetch("/api/auth/resend-verification", {
        method: "POST",
        body: JSON.stringify({ email }),
        skipAuthRedirect: true,
      });
      showMsg(t("auth.login.resend_success"));
    } catch {
      showError(t("auth.login.resend_error"));
    } finally {
      resendLink.textContent = t("auth.login.resend_verification");
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
