/**
 * PULSE Service Worker
 * Strategy:
 *   - API calls (/api/*): network-first, fall back to cached response
 *   - Static assets (CSS/JS/HTML/images): cache-first, fall back to network
 *   - Offline fallback: serve /offline.html when navigation fails completely
 */

const CACHE_VERSION = "pulse-v1";

const STATIC_ASSETS = [
  "/feed.html",
  "/discover.html",
  "/zone.html",
  "/analytics.html",
  "/profile.html",
  "/notifications.html",
  "/messages.html",
  "/search.html",
  "/settings.html",
  "/login.html",
  "/register.html",
  "/offline.html",
  "/manifest.json",
  "/css/variables.css",
  "/css/base.css",
  "/css/components.css",
  "/css/feed.css",
  "/css/analytics.css",
  "/css/login.css",
  "/css/profile.css",
  "/css/messages.css",
  "/css/notifications.css",
  "/js/auth.js",
  "/js/theme.js",
  "/js/avatar.js",
  "/js/i18n.js",
  "/js/feed.js",
  "/js/discover.js",
  "/js/zone.js",
  "/js/analytics.js",
  "/js/profile.js",
  "/js/notifications.js",
  "/js/messages.js",
  "/js/search.js",
  "/js/settings.js",
  "/js/login.js",
  "/js/register.js",
  "/js/api.js",
  "/js/router.js",
  "/js/zone_autocomplete.js",
  "/assets/default-avatar.svg",
  "/assets/icon-192.svg",
  "/assets/icon-512.svg",
];

// ── Install: pre-cache all static assets ─────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ── Activate: remove stale caches ────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: routing logic ──────────────────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin or the configured API origin
  if (url.origin !== self.location.origin && !url.pathname.startsWith("/api/")) return;

  // API calls: network-first (fresh data when online, stale when offline)
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Navigation requests (HTML pages): network-first so updates land immediately
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() =>
        caches.match(request).then((cached) => cached || caches.match("/offline.html"))
      )
    );
    return;
  }

  // Everything else (CSS, JS, images): cache-first
  event.respondWith(cacheFirst(request));
});

// ── Push Notifications ────────────────────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;
  let payload = {};
  try { payload = event.data.json(); } catch { payload = { title: 'PULSE', body: event.data.text() }; }

  const title = payload.title || 'PULSE';
  const options = {
    body: payload.body || '',
    icon: '/assets/icon-192.svg',
    badge: '/assets/icon-192.svg',
    data: payload.data || {},
    vibrate: [200, 100, 200],
    tag: payload.data?.notification_type || 'pulse-notification',
    renotify: true,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/feed.html';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      const existing = clientList.find((c) => 'focus' in c);
      if (existing) {
        existing.navigate(url);
        return existing.focus();
      }
      return clients.openWindow(url);
    })
  );
});

async function networkFirst(request) {
  const cache = await caches.open(CACHE_VERSION);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await cache.match(request);
    return cached || new Response(JSON.stringify({ error: "Offline" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_VERSION);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response("Offline", { status: 503 });
  }
}
