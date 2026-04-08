/**
 * PWA helpers — install prompt + Web Push subscription.
 * Import and call initInstallPrompt() and initPushNotifications()
 * from authenticated pages (e.g. feed.js).
 */

import { apiFetch } from './auth.js';

// ── Install Prompt ────────────────────────────────────────────────────────────

let deferredInstallPrompt = null;

export function initInstallPrompt() {
  // Respect the user's choice to dismiss permanently
  if (localStorage.getItem('pwa-install-dismissed')) return;
  // Already installed as a standalone app — no banner needed
  if (window.matchMedia('(display-mode: standalone)').matches) return;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    // Short delay so the page has settled before showing the banner
    setTimeout(showInstallBanner, 2000);
  });
}

function showInstallBanner() {
  if (document.getElementById('pwaInstallBanner')) return;

  const banner = document.createElement('div');
  banner.id = 'pwaInstallBanner';
  banner.className = 'pwa-install-banner';
  banner.setAttribute('role', 'complementary');
  banner.setAttribute('aria-label', 'Install PULSE app');
  banner.innerHTML = `
    <img src="assets/icon-192.svg" class="pwa-banner-icon" alt="" aria-hidden="true" />
    <div class="pwa-banner-text">
      <strong>Install PULSE</strong>
      <span>Add to your home screen for the best experience</span>
    </div>
    <button class="btn pwa-install-btn" id="pwaInstallBtn">Install</button>
    <button class="iconbtn pwa-dismiss-btn" id="pwaDismissBtn" aria-label="Dismiss install prompt">✕</button>
  `;
  document.body.appendChild(banner);

  document.getElementById('pwaInstallBtn').addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    banner.remove();
    deferredInstallPrompt = null;
  });

  document.getElementById('pwaDismissBtn').addEventListener('click', () => {
    banner.remove();
    localStorage.setItem('pwa-install-dismissed', '1');
  });
}

// ── Web Push Notifications ────────────────────────────────────────────────────

export async function initPushNotifications() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
  if (!('Notification' in window)) return;
  if (Notification.permission === 'denied') return;

  try {
    const registration = await navigator.serviceWorker.ready;

    // If already subscribed, keep the backend in sync and exit
    const existingSub = await registration.pushManager.getSubscription();
    if (existingSub) {
      await _syncSubscription(existingSub);
      return;
    }

    // Fetch VAPID public key — if the backend hasn't configured it, bail silently
    let vapidPublicKey;
    try {
      const resp = await apiFetch('/api/push/vapid-public-key');
      vapidPublicKey = resp.public_key;
    } catch {
      return;
    }
    if (!vapidPublicKey) return;

    // Only ask for permission when the user hasn't been asked before
    if (Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') return;
    }

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: _urlBase64ToUint8Array(vapidPublicKey),
    });

    await _syncSubscription(subscription);
  } catch (err) {
    console.warn('[PWA] Push subscription error:', err);
  }
}

async function _syncSubscription(subscription) {
  try {
    await apiFetch('/api/push/subscribe', {
      method: 'POST',
      body: JSON.stringify({
        platform: 'web',
        token: JSON.stringify(subscription.toJSON()),
      }),
    });
  } catch {
    // Silent — don't interrupt the app if the sync fails
  }
}

function _urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}
