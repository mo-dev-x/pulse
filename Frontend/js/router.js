const ROUTES = {
  "": "login.html",
  "#login": "login.html",
  "#register": "register.html",
  "#verify-email": "verify-email.html",
  "#forgot-password": "forgot-password.html",
  "#reset-password": "reset-password.html",
  "#feed": "feed.html",
  "#profile": "profile.html",
  "#zone": "zone.html",
  "#analytics": "analytics.html",
  "#messages": "messages.html",
  "#notifications": "notifications.html",
  "#settings": "settings.html",
  "#search": "search.html",
  "#discover": "discover.html",
};

function redirectFromHash() {
  const hash = window.location.hash || "";
  const target = ROUTES[hash] || "login.html";
  window.location.replace(target);
}

window.addEventListener("DOMContentLoaded", redirectFromHash);
window.addEventListener("hashchange", redirectFromHash);
