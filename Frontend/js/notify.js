/**
 * runAsyncUI({ fn, onLoad, onSuccess, isEmpty, onEmpty, onError, onFinally })
 *
 * Orchestrates the loading → success → empty → error lifecycle for an async
 * data-fetch operation. All phase callbacks are optional and awaited, so they
 * may be sync or async interchangeably.
 *
 * @param {object}                  options
 * @param {()         => Promise}   options.fn        - Async function to run (typically an apiCall)
 * @param {()         => void}      [options.onLoad]  - Called first; set loading state here
 * @param {(result)   => void}      [options.onSuccess] - Called when fn resolves and isEmpty is falsy
 * @param {(result)   => boolean}   [options.isEmpty] - Predicate; routes to onEmpty when truthy
 * @param {(result)   => void}      [options.onEmpty]   - Called when isEmpty returns true
 * @param {(Error)    => void}      [options.onError]   - Called when fn rejects
 * @param {()         => void}      [options.onFinally] - Always called last (equivalent to finally)
 */
export async function runAsyncUI({
  fn,
  onLoad,
  onSuccess,
  isEmpty,
  onEmpty,
  onError,
  onFinally,
} = {}) {
  await onLoad?.();
  try {
    const result = await fn();
    if (typeof isEmpty === "function" && isEmpty(result)) {
      await onEmpty?.(result);
    } else {
      await onSuccess?.(result);
    }
  } catch (err) {
    await onError?.(err);
  } finally {
    await onFinally?.();
  }
}

/**
 * notify(message, type, duration)
 *
 * Appends a toast to #toastContainer (created by theme.js initThemeToggle).
 * Falls back to console.warn if no container is present.
 *
 * @param {string} message
 * @param {"info"|"success"|"error"} [type="info"]
 * @param {number} [duration=2600]
 */
export function notify(message, type = "info", duration = 2600) {
  const container = document.getElementById("toastContainer");
  if (!container) {
    console.warn(`[notify:${type}]`, message);
    return;
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}
