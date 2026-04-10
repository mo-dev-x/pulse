import { apiFetch } from "./auth.js";
import { bus } from "./bus.js";

const THEME_KEY = "pulse_theme";
let badgeTimer = null;

export function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const systemDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
  const theme = saved || (systemDark ? "dark" : "light");
  applyTheme(theme);
}

export function applyTheme(theme) {
  const next = theme === "light" ? "light" : theme === "auto"
    ? (window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light")
    : "dark";

  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(THEME_KEY, next);

  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.innerHTML = next === "dark"
      ? '<i class="ui-icon ui-icon--action uil uil-sun" aria-hidden="true"></i>'
      : '<i class="ui-icon ui-icon--action uil uil-moon" aria-hidden="true"></i>';
    btn.setAttribute("aria-label", next === "dark" ? "Switch to light mode" : "Switch to dark mode");
  });

  return next;
}

export function initThemeToggle(root = document) {
  initTheme();
  _ensureToastContainer();
  _injectSkipLink();
  root.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  });
}

/** Inject a toast container if the page doesn't already have one. */
function _ensureToastContainer() {
  if (document.getElementById("toastContainer")) return;
  const el = document.createElement("div");
  el.id = "toastContainer";
  el.className = "toast-container";
  el.setAttribute("aria-live", "polite");
  el.setAttribute("aria-atomic", "true");
  document.body.appendChild(el);
}

/** Inject a keyboard-accessible skip-to-content link. */
function _injectSkipLink() {
  if (document.getElementById("skipLink")) return;
  const target = document.querySelector("main, .main, [role='main']");
  if (!target) return;
  if (!target.id) target.id = "main-content";
  const link = document.createElement("a");
  link.id = "skipLink";
  link.href = "#main-content";
  link.className = "skip-link";
  link.textContent = "Skip to main content";
  document.body.insertBefore(link, document.body.firstChild);
}

/**
 * Catch unhandled promise rejections and show them as error toasts.
 * Call once at app startup from each page's JS module.
 */
export function initGlobalErrorHandler() {
  window.addEventListener("unhandledrejection", (event) => {
    if (event.reason?.name === "AbortError") return; // ignore intentional cancels
    const msg = event.reason?.message;
    if (!msg) return;
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "toast error";
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
  });
}

export function initOfflineBanner() {
  const banner = document.getElementById("offlineBanner");
  if (!banner) return;

  const sync = () => {
    const online = navigator.onLine !== false;
    banner.hidden = online;
  };

  window.addEventListener("online", sync);
  window.addEventListener("offline", sync);
  sync();
}

export async function refreshUnreadBadges(root = document) {
  const messageBadges = root.querySelectorAll("[data-message-badge]");
  const notificationBadges = root.querySelectorAll("[data-notification-badge]");

  if (!messageBadges.length && !notificationBadges.length) return;

  try {
    const tasks = [];
    if (messageBadges.length) tasks.push(apiFetch("/api/messages/unread-count", { method: "GET" }));
    else tasks.push(Promise.resolve(null));
    if (notificationBadges.length) tasks.push(apiFetch("/api/notifications?per_page=1", { method: "GET" }));
    else tasks.push(Promise.resolve(null));

    const [messagesData, notificationsData] = await Promise.all(tasks);

    const unreadMessages = Number(messagesData?.unread_messages || 0);
    const unreadNotifications = Number(notificationsData?.unread_count || 0);

    messageBadges.forEach((badge) => {
      badge.hidden = unreadMessages <= 0;
      badge.textContent = String(unreadMessages);
    });

    notificationBadges.forEach((badge) => {
      badge.hidden = unreadNotifications <= 0;
      badge.textContent = String(unreadNotifications);
    });
  } catch {
    // Keep shell resilient when badge endpoints fail.
  }
}

export function initUnreadBadges(root = document) {
  refreshUnreadBadges(root);
  if (badgeTimer) clearInterval(badgeTimer);
  badgeTimer = setInterval(() => {
    refreshUnreadBadges(root);
  }, 60000);

  // Immediately refresh nav badges when messages are marked read on any page.
  // messages.js emits "messages:read" after a successful PATCH — this avoids
  // waiting up to 60s for the interval to catch up.
  bus.on("messages:read", () => refreshUnreadBadges(root));
}

export function initMobileDrawer() {
  const drawer  = document.getElementById("mobileDrawer");
  const overlay = document.getElementById("mobileDrawerOverlay");
  const trigger = document.getElementById("mobileMenuTrigger");
  const closeBtn = document.getElementById("mobileDrawerClose");
  if (!drawer || !overlay) return;

  const open = () => {
    drawer.classList.add("open");
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
  };
  const close = () => {
    drawer.classList.remove("open");
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  };

  trigger?.addEventListener("click", open);
  closeBtn?.addEventListener("click", close);
  overlay.addEventListener("click", close);
}
