import { apiFetch, getAssetUrl, requireAuth, saveCurrentUser } from "./auth.js";
import { getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls, setLang } from "./i18n.js";
import { applyTheme, initThemeToggle, initOfflineBanner, initUnreadBadges, refreshUnreadBadges } from "./theme.js";

let currentUser = null;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();
  initUnreadBadges();
  setupTabs();
  await loadSettings();
  wireForms();
});

function setupTabs() {
  document.querySelectorAll("[data-settings-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-settings-tab]").forEach((item) => item.classList.toggle("active", item === btn));
      ["profile", "preferences", "security"].forEach((tab) => {
        document.getElementById(`tab-${tab}`).hidden = tab !== btn.dataset.settingsTab;
      });
    });
  });
}

async function loadSettings() {
  const data = await apiFetch("/api/auth/me", { method: "GET" });
  currentUser = data.user;
  saveCurrentUser(currentUser);

  document.getElementById("settingsDisplayName").value = currentUser.display_name || "";
  document.getElementById("settingsBio").value = currentUser.bio || "";
  document.getElementById("settingsLocation").value = currentUser.location || "";
  document.getElementById("settingsWebsite").value = currentUser.website || "";
  document.getElementById("settingsVisibility").value = currentUser.profile_visibility || "public";
  document.getElementById("settingsShowEmail").checked = Boolean(currentUser.show_email);
  document.getElementById("settingsLanguage").value = currentUser.preferred_language || "en";
  document.getElementById("settingsTheme").value = currentUser.theme || "dark";
  document.getElementById("emailNotifications").checked = Boolean(currentUser.email_notifications);
  document.getElementById("pushNotifications").checked = Boolean(currentUser.push_notifications);
  const avatarPreview = document.getElementById("settingsAvatarPreview");
  if (avatarPreview) {
    avatarPreview.src = getUserAvatarUrl(currentUser, getAssetUrl);
  }

  const pseudonymInput = document.getElementById("settingsPseudonym");
  const pseudonymBtn = document.getElementById("savePseudonymBtn");
  const cooldownNote = document.getElementById("pseudonymCooldownNote");
  if (pseudonymInput) {
    pseudonymInput.value = currentUser.pseudonym || "";
    const canChange = currentUser.can_change_pseudonym !== false;
    pseudonymInput.disabled = !canChange;
    if (pseudonymBtn) pseudonymBtn.disabled = !canChange;
    if (cooldownNote) {
      if (!canChange && currentUser.pseudonym_last_changed) {
        const nextDate = new Date(currentUser.pseudonym_last_changed);
        nextDate.setDate(nextDate.getDate() + 90);
        cooldownNote.hidden = false;
        cooldownNote.textContent = `You can change your pseudonym again on ${nextDate.toLocaleDateString()}.`;
      } else {
        cooldownNote.hidden = true;
      }
    }
  }

  await Promise.all([loadSessions(), refreshTwoFactorState()]);
}

function wireForms() {
  document.getElementById("profileSettingsForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const avatarFile = document.getElementById("settingsAvatarFile")?.files?.[0] || null;
    hideMessage("settingsProfileMessage");

    if (avatarFile) {
      const fd = new FormData();
      fd.append("file", avatarFile);
      await apiFetch("/api/auth/upload-profile-pic", {
        method: "POST",
        body: fd,
      });
    }

    await apiFetch("/api/auth/update-profile", {
      method: "PATCH",
      body: JSON.stringify({
        display_name: document.getElementById("settingsDisplayName").value.trim(),
        bio: document.getElementById("settingsBio").value.trim(),
        location: document.getElementById("settingsLocation").value.trim(),
        website: document.getElementById("settingsWebsite").value.trim(),
      }),
    });

    await apiFetch("/api/auth/privacy-settings", {
      method: "PATCH",
      body: JSON.stringify({
        profile_visibility: document.getElementById("settingsVisibility").value,
        show_email: document.getElementById("settingsShowEmail").checked,
      }),
    });

    await loadSettings();
    showMessage("settingsProfileMessage", "Profile settings saved.");
  });

  document.getElementById("preferencesForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const language = document.getElementById("settingsLanguage").value;
    const theme = document.getElementById("settingsTheme").value;
    setLang(language);
    applyTheme(theme);

    await apiFetch("/api/auth/preferences", {
      method: "PATCH",
      body: JSON.stringify({
        theme,
        email_notifications: document.getElementById("emailNotifications").checked,
        push_notifications: document.getElementById("pushNotifications").checked,
      }),
    });

    showMessage("settingsPreferencesMessage", "Preferences saved.");
    await refreshUnreadBadges();
  });

  document.getElementById("settingsAvatarFile")?.addEventListener("change", () => {
    const file = document.getElementById("settingsAvatarFile")?.files?.[0];
    const preview = document.getElementById("settingsAvatarPreview");
    if (!file || !preview) return;
    preview.src = URL.createObjectURL(file);
  });

  document.getElementById("passwordSettingsForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage("settingsSecurityMessage");
    await apiFetch("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: document.getElementById("currentPassword").value,
        new_password: document.getElementById("newPassword").value,
      }),
    });
    document.getElementById("passwordSettingsForm").reset();
    showMessage("settingsSecurityMessage", "Password updated.");
  });

  document.getElementById("revokeAllSessions")?.addEventListener("click", async () => {
    await apiFetch("/api/auth/sessions/all", { method: "DELETE" });
    await loadSessions();
    showMessage("settingsSecurityMessage", "Other sessions revoked.");
  });

  document.getElementById("enable2fa")?.addEventListener("click", async () => {
    const data = await apiFetch("/api/auth/2fa/enable", { method: "POST" });
    const setup = document.getElementById("twoFactorSetup");
    setup.hidden = false;
    setup.innerHTML = `
      <div><strong>Secret:</strong> ${escapeHtml(data.totp_secret)}</div>
      <div style="margin-top:8px;"><strong>Backup codes:</strong> ${escapeHtml((data.backup_codes || []).join(", "))}</div>
      ${data.qr_code_data_url ? `<div style="margin-top:10px;"><img src="${data.qr_code_data_url}" alt="2FA QR code" style="max-width:180px;border-radius:12px;" /></div>` : ""}
    `;
    await refreshTwoFactorState();
    showMessage("settingsSecurityMessage", "2FA setup started.");
  });

  document.getElementById("verify2fa")?.addEventListener("click", async () => {
    const code = window.prompt("Enter your current 2FA code");
    if (!code) return;
    await apiFetch("/api/auth/2fa/verify", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
    await refreshTwoFactorState();
    showMessage("settingsSecurityMessage", "2FA verification successful.");
  });

  document.getElementById("disable2fa")?.addEventListener("click", async () => {
    const backupCode = window.prompt("Enter a current backup code or TOTP code");
    if (!backupCode) return;
    await apiFetch("/api/auth/2fa/disable", {
      method: "POST",
      body: JSON.stringify({ backup_code: backupCode }),
    });
    await refreshTwoFactorState();
    showMessage("settingsSecurityMessage", "2FA disabled.");
  });

  document.getElementById("regenBackupCodes")?.addEventListener("click", async () => {
    const data = await apiFetch("/api/auth/2fa/backup-codes", { method: "GET" });
    const setup = document.getElementById("twoFactorSetup");
    setup.hidden = false;
    setup.innerHTML = `<div><strong>Backup codes:</strong> ${escapeHtml((data.backup_codes || []).join(", "))}</div>`;
    showMessage("settingsSecurityMessage", "Backup codes regenerated.");
  });

  document.getElementById("pseudonymForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage("pseudonymMessage");
    const newPseudonym = document.getElementById("settingsPseudonym")?.value.trim();
    if (!newPseudonym) return;
    try {
      const data = await apiFetch("/api/auth/update-pseudonym", {
        method: "PATCH",
        body: JSON.stringify({ pseudonym: newPseudonym }),
      });
      await loadSettings();
      showMessage("pseudonymMessage", `Pseudonym updated to "${escapeHtml(data.pseudonym)}".`);
    } catch (err) {
      showMessage("pseudonymMessage", err?.message || "Failed to update pseudonym.");
    }
  });

  document.getElementById("requestPushPermission")?.addEventListener("click", async () => {
    if (!("Notification" in window)) {
      alert("Browser notifications are not supported here.");
      return;
    }

    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      await apiFetch("/api/push/subscribe", {
        method: "POST",
        body: JSON.stringify({
          platform: "web",
          token: `browser-${Date.now()}`,
          device_label: navigator.userAgent.slice(0, 80),
        }),
      });
      showMessage("settingsPreferencesMessage", "Push permission granted and device registered.");
    } else {
      showMessage("settingsPreferencesMessage", `Push permission: ${permission}.`);
    }
  });
}

async function loadSessions() {
  const root = document.getElementById("sessionsList");
  const data = await apiFetch("/api/auth/sessions", { method: "GET" });
  const sessions = data.sessions || [];
  if (!sessions.length) {
    root.innerHTML = '<div class="state">No active sessions found.</div>';
    return;
  }

  root.className = "session-list";
  root.innerHTML = sessions.map((session, index) => {
    const summary = describeSession(session);
    return `
      <article class="session-card">
        <div class="session-icon" aria-hidden="true">${summary.icon}</div>
        <div>
          <div class="session-title-row">
            <div class="session-title">${escapeHtml(summary.title)}</div>
            ${index === 0 ? '<span class="inline-badge">Current</span>' : ""}
          </div>
          <div class="session-subtitle">${escapeHtml(summary.subtitle)}</div>
          <div class="session-meta">
            <span class="session-pill">${escapeHtml(summary.deviceType)}</span>
            <span class="session-pill">${escapeHtml(summary.ip)}</span>
            <span class="session-pill">Started ${escapeHtml(summary.created)}</span>
            <span class="session-pill">Seen ${escapeHtml(summary.lastSeen)}</span>
          </div>
        </div>
        <div class="notification-actions">
          <button class="iconbtn" data-revoke-session="${session.id}" title="Revoke session">✕</button>
        </div>
      </article>
    `;
  }).join("");

  root.querySelectorAll("[data-revoke-session]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await apiFetch(`/api/auth/sessions/${btn.dataset.revokeSession}`, { method: "DELETE" });
      await loadSessions();
    });
  });
}

function describeSession(session) {
  const ua = String(session.user_agent || "");
  const ip = session.ip_address || "Unknown IP";
  const deviceType = String(session.device_type || "unknown");
  const isMobile = /iphone|android|mobile|ipad/i.test(ua) || deviceType === "mobile";
  const isMac = /mac os|macintosh/i.test(ua);
  const isWindows = /windows/i.test(ua);
  const isLinux = /linux/i.test(ua) && !/android/i.test(ua);
  const isChrome = /chrome|crios/i.test(ua) && !/edg/i.test(ua);
  const isSafari = /safari/i.test(ua) && !/chrome|crios|android/i.test(ua);
  const isFirefox = /firefox/i.test(ua);
  const isEdge = /edg/i.test(ua);

  const os = isMobile
    ? (/iphone|ipad/i.test(ua) ? "iPhone / iPad" : "Android")
    : isMac
      ? "macOS"
      : isWindows
        ? "Windows"
        : isLinux
          ? "Linux"
          : "Unknown OS";

  const browser = isEdge
    ? "Edge"
    : isChrome
      ? "Chrome"
      : isSafari
        ? "Safari"
        : isFirefox
          ? "Firefox"
          : "Browser";

  return {
    icon: isMobile ? "📱" : isMac ? "💻" : isWindows ? "🖥️" : isLinux ? "🧩" : "🌐",
    title: `${os} ${browser}`.trim(),
    subtitle: ua || "Unknown device",
    deviceType: deviceType.charAt(0).toUpperCase() + deviceType.slice(1),
    ip,
    created: formatSessionTime(session.created_at),
    lastSeen: formatSessionTime(session.last_activity),
  };
}

function formatSessionTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "recently";
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

async function refreshTwoFactorState() {
  const state = document.getElementById("twoFactorState");
  const data = await apiFetch("/api/auth/me", { method: "GET" });
  state.textContent = data.user?.totp_enabled ? "2FA is enabled." : "2FA is currently disabled.";
}

function showMessage(id, message) {
  const el = document.getElementById(id);
  if (!el) return;
  el.hidden = false;
  el.textContent = message;
}

function hideMessage(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.hidden = true;
  el.textContent = "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
