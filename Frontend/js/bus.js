/**
 * bus — lightweight in-page pub/sub using a shared EventTarget.
 *
 * Usage:
 *   import { bus } from "./bus.js";
 *   bus.on("messages:read", () => refreshUnreadBadges());   // theme.js
 *   bus.emit("messages:read");                               // messages.js
 *
 * Listeners are scoped to the current page's JS runtime — no cross-tab or
 * cross-page communication. Events carry a single `detail` value.
 */

const _target = new EventTarget();

export const bus = {
  /** Subscribe to an event. Returns an unsubscribe function. */
  on(event, handler) {
    const wrapped = (e) => handler(e.detail);
    _target.addEventListener(event, wrapped);
    return () => _target.removeEventListener(event, wrapped);
  },

  /** Publish an event with an optional payload. */
  emit(event, detail) {
    _target.dispatchEvent(new CustomEvent(event, { detail }));
  },
};
