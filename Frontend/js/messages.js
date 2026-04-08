import { apiFetch, getAssetUrl, requireAuth } from "./auth.js";
import { getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initThemeToggle, initOfflineBanner } from "./theme.js";

let currentConversationId = null;
let currentOtherUser = null;
let pollTimer = null;
let lastKnownMessageId = null;   // used by smooth polling

// Audio recording state
let mediaRecorder = null;
let audioChunks   = [];
let isRecording   = false;
let recStream     = null;   // MediaStream from getUserMedia
let audioBlob     = null;   // blob ready to send (set after stop)
let audioObjUrl   = null;   // object URL for preview playback
let previewAudio  = null;   // Audio element for preview
let recDuration   = 0;      // seconds recorded
let recStartMs    = 0;      // Date.now() at recording start
let recTimerIv    = null;   // setInterval ID for timer
let waveAnimId    = null;   // requestAnimationFrame ID
let audioCtx      = null;   // AudioContext for analyser
let capturedWave  = null;   // Float32Array bar heights captured at stop

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();

  // Start new conversation
  document.getElementById("newConversationUsername")?.addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const username = e.target.value.trim().replace(/^@/, "");
    if (!username) return;
    const data = await apiFetch("/api/messages/conversations", {
      method: "POST",
      body: JSON.stringify({ username }),
    });
    const conversation = data.conversation;
    if (conversation?.id) {
      e.target.value = "";
      await loadConversations(conversation.id);
      showThread();
    }
  });

  const focusSearch = () => document.getElementById("newConversationUsername")?.focus();
  document.getElementById("newMsgBtn")?.addEventListener("click", focusSearch);
  document.getElementById("newMsgBtnEmpty")?.addEventListener("click", focusSearch);

  document.getElementById("messageComposer")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await sendMessage();
  });

  document.getElementById("backBtn")?.addEventListener("click", () => {
    document.getElementById("dmSidebar").classList.remove("dm-sidebar--hidden");
  });

  // Image attach
  document.getElementById("imageAttachBtn")?.addEventListener("click", () => {
    document.getElementById("imageAttachInput")?.click();
  });
  document.getElementById("imageAttachInput")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    await sendMediaMessage(file);
  });

  // Audio record — tap mic to start; recorder bar takes over from there
  document.getElementById("audioRecordBtn")?.addEventListener("click", startAudioRecording);
  document.getElementById("dmRecCancelBtn")?.addEventListener("click", cancelRecording);
  document.getElementById("dmRecDoneBtn")?.addEventListener("click", stopRecording);
  document.getElementById("dmPrevDiscardBtn")?.addEventListener("click", discardPreview);
  document.getElementById("dmPrevPlayBtn")?.addEventListener("click", togglePreviewPlay);
  document.getElementById("dmPrevSendBtn")?.addEventListener("click", sendPreviewedAudio);

  // Reply button click (desktop) + swipe-to-reply (mobile)
  setupReplyGestures();

  // Right-click context menu for messages
  setupContextMenu();

  await loadConversations();
  updateUnreadBadge();
});

// ── Conversation list ──────────────────────────────────────────────────────

async function loadConversations(selectId = null) {
  const list = document.getElementById("conversationList");
  const data = await apiFetch("/api/messages/conversations", { method: "GET" });
  const conversations = data.conversations || [];

  const totalUnread = conversations.reduce((sum, c) => sum + Number(c.unread_count || 0), 0);
  const badge = document.getElementById("messageBadge");
  badge.textContent = String(totalUnread);
  badge.hidden = totalUnread === 0;

  if (!conversations.length) {
    list.innerHTML = `
      <div class="dm-empty-thread" style="padding: 32px 16px;">
        💬 No conversations yet.<br>
        <span style="font-size:13px;opacity:.7">Search for a username above to start chatting.</span>
      </div>`;
    return;
  }

  currentConversationId = selectId || currentConversationId || conversations[0].id;
  list.innerHTML = conversations
    .map((c) => renderConversation(c, c.id === currentConversationId))
    .join("");

  list.querySelectorAll("[data-conversation-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      currentConversationId = Number(btn.dataset.conversationId);
      await loadConversations(currentConversationId);
      showThread();
    });
  });

  await loadThread(currentConversationId);
}

function renderConversation(conv, active) {
  const avatar = getUserAvatarUrl(conv.other_user, getAssetUrl);
  const name   = conv.other_user?.display_name || "Unknown";
  const preview = conv.last_message
    ? (conv.last_message.content?.startsWith("[audio]") ? "🎤 Voice message" : conv.last_message.content)
    : "No messages yet.";
  const ts     = conv.last_message?.created_at ? formatRelativeTime(conv.last_message.created_at) : "";
  const unread = Number(conv.unread_count || 0) > 0;

  return `
    <button class="dm-conv-row${active ? " dm-conv-row--active" : ""}"
            data-conversation-id="${conv.id}" type="button">
      <div class="dm-conv-avatar-wrap">
        <img class="dm-conv-avatar" src="${escapeAttr(avatar)}" alt="${escapeAttr(name)}" loading="lazy" />
        ${unread ? `<span class="dm-conv-dot"></span>` : ""}
      </div>
      <div class="dm-conv-body">
        <div class="dm-conv-top">
          <span class="dm-conv-name${unread ? " dm-conv-name--bold" : ""}">${escapeHtml(name)}${conv.other_user?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : ''}</span>
          <span class="dm-conv-ts">${escapeHtml(ts)}</span>
        </div>
        <div class="dm-conv-preview${unread ? " dm-conv-preview--bold" : ""}">${escapeHtml(preview)}</div>
      </div>
    </button>`;
}

// ── Thread ─────────────────────────────────────────────────────────────────

async function loadThread(conversationId) {
  document.getElementById("dmEmpty").hidden = true;
  document.getElementById("threadHeader").hidden = false;
  document.getElementById("messagesArea").hidden = false;
  document.getElementById("messageComposer").hidden = false;

  const thread = document.getElementById("messageThread");
  thread.innerHTML = `
    <div class="dm-loading">
      <div class="dm-skel dm-skel-theirs"></div>
      <div class="dm-skel dm-skel-mine"></div>
      <div class="dm-skel dm-skel-theirs" style="width:35%"></div>
    </div>`;

  const data = await apiFetch(
    `/api/messages/conversations/${conversationId}?per_page=100`,
    { method: "GET" }
  );

  currentOtherUser = data.conversation?.other_user || null;
  const titleEl   = document.getElementById("threadTitle");
  const titleName = currentOtherUser?.display_name || "Conversation";
  titleEl.innerHTML = escapeHtml(titleName) + (currentOtherUser?.is_admin ? '<span class="admin-star" title="Admin">⭐</span>' : '');
  document.getElementById("threadAvatar").src = getUserAvatarUrl(currentOtherUser, getAssetUrl);
  const profileLink = document.getElementById("threadProfileLink");
  if (profileLink && currentOtherUser?.username) {
    profileLink.href = `profile.html?u=${encodeURIComponent(currentOtherUser.username)}`;
  }

  const messages = data.messages || [];
  lastKnownMessageId = messages.length ? messages[messages.length - 1].id : null;

  thread.innerHTML = renderMessageGroups(messages);
  fixAudioDurations(thread);

  const area = document.getElementById("messagesArea");
  area.scrollTop = area.scrollHeight;

  await apiFetch(`/api/messages/conversations/${conversationId}/read`, { method: "PATCH" });

  startPolling(conversationId);
}

// ── Smooth poll — only updates DOM when new messages arrive ───────────────

async function pollMessages(conversationId) {
  if (currentConversationId !== conversationId) return;

  try {
    const data = await apiFetch(
      `/api/messages/conversations/${conversationId}?per_page=100`,
      { method: "GET" }
    );
    const messages = data.messages || [];
    if (!messages.length) return;

    const latestId = messages[messages.length - 1].id;
    if (latestId === lastKnownMessageId) return; // Nothing new

    lastKnownMessageId = latestId;

    const thread = document.getElementById("messageThread");
    const area   = document.getElementById("messagesArea");

    // Remember if user was near the bottom before update
    const nearBottom = area.scrollHeight - area.scrollTop - area.clientHeight < 120;

    // Remove optimistic bubbles before re-rendering real messages
    thread.querySelectorAll(".dm-optimistic").forEach((el) => el.remove());

    thread.innerHTML = renderMessageGroups(messages);
    fixAudioDurations(thread);

    if (nearBottom) area.scrollTop = area.scrollHeight;

    await apiFetch(`/api/messages/conversations/${conversationId}/read`, { method: "PATCH" });
    await updateUnreadBadge();
  } catch {
    // Polling errors are silent
  }
}

/** Group consecutive messages from the same sender, then render. */
function renderMessageGroups(messages) {
  if (!messages.length) {
    return `<div class="dm-empty-thread">No messages yet. Say hello! 👋</div>`;
  }

  const groups = [];
  for (const msg of messages) {
    const last = groups[groups.length - 1];
    if (last && last.is_mine === msg.is_mine) {
      last.msgs.push(msg);
    } else {
      groups.push({ is_mine: msg.is_mine, msgs: [msg] });
    }
  }

  return groups.map(({ is_mine, msgs }) => {
    const side = is_mine ? "mine" : "theirs";
    const n    = msgs.length;

    const bubbles = msgs.map((m, i) => {
      const pos = n === 1 ? "solo" : i === 0 ? "first" : i === n - 1 ? "last" : "mid";

      // ── Resolve reply quote ─────────────────────────────────────────────
      // New messages: reply_preview field (structured).
      // Legacy messages: embedded "↩ preview\ncontent" prefix.
      let replyQuote   = m.reply_preview || null;
      let displayContent = m.content || "";
      if (!replyQuote && displayContent.startsWith("↩ ")) {
        const nl = displayContent.indexOf("\n");
        if (nl > 0) {
          replyQuote     = displayContent.slice(2, nl).trim();
          displayContent = displayContent.slice(nl + 1);
        }
      }
      const quoteHtml = replyQuote
        ? `<div class="dm-bubble-quote"><span class="dm-bubble-quote-bar"></span><span class="dm-bubble-quote-text">${escapeHtml(replyQuote)}</span></div>`
        : "";

      // ── Build short preview for the reply-context bar ───────────────────
      const isAudio = displayContent.startsWith("[audio]");
      const isMedia = isAudio || displayContent.startsWith("[image]") || displayContent.startsWith("[video]");
      const extraClass = isAudio ? " dm-bubble--audio" : isMedia ? " dm-bubble--media" : "";
      const rawLabel   = isMedia ? (isAudio ? "🎤 Voice message" : "📎 Image") : displayContent;
      const labelShort = rawLabel.length > 40 ? rawLabel.slice(0, 40) + "…" : rawLabel;

      return `
        <div class="dm-bubble-wrap dm-bubble-wrap--${side}" data-msg-id="${m.id}">
          <button class="dm-reply-btn" data-reply-id="${m.id}" data-reply-preview="${escapeAttr(labelShort)}" aria-label="Reply" title="Reply">
            <i class="uil uil-corner-up-left"></i>
          </button>
          <div class="dm-bubble${extraClass}" data-pos="${pos}" data-msg-id="${m.id}" data-is-mine="${m.is_mine}">
            ${quoteHtml}${renderBubbleContent(displayContent)}
          </div>
        </div>`;
    }).join("");

    const last      = msgs[n - 1];
    const timeMeta  = formatRelativeTime(last.created_at) +
      (last.is_mine && last.is_read ? " · Seen" : "");

    const avatarHtml = !is_mine
      ? `<img class="dm-group-avatar" src="${escapeAttr(getUserAvatarUrl(currentOtherUser, getAssetUrl))}" alt="" loading="lazy" />`
      : "";

    return `
      <div class="dm-msg-group dm-msg-group--${side}">
        ${avatarHtml}
        <div class="dm-bubbles">
          ${bubbles}
          <span class="dm-msg-time">${escapeHtml(timeMeta)}</span>
        </div>
      </div>`;
  }).join("");
}

/** Render bubble content — handles audio/image/video messages specially. */
function renderBubbleContent(content) {
  if (!content) return "";
  if (content.startsWith("[audio]")) {
    // getAssetUrl resolves "/api/uploads/…" → absolute API URL
    const url = escapeAttr(getAssetUrl(content.slice(7)));
    return `<audio class="dm-audio" controls src="${url}" preload="metadata" data-fix-duration></audio>`;
  }
  if (content.startsWith("[image]")) {
    const url = escapeAttr(getAssetUrl(content.slice(7)));
    return `<img class="dm-media-img" src="${url}" alt="Image" loading="lazy" />`;
  }
  if (content.startsWith("[video]")) {
    const url = escapeAttr(getAssetUrl(content.slice(7)));
    return `<video class="dm-media-video" controls src="${url}" preload="metadata"></video>`;
  }
  return escapeHtml(content);
}

// ── Send text message ──────────────────────────────────────────────────────

async function sendMessage() {
  if (!currentConversationId) return;
  const input   = document.getElementById("messageInput");
  const content = input.value.trim();
  if (!content) return;

  // Capture and clear reply context
  const replyCtx    = document.getElementById("dmReplyContext");
  let replyToId     = null;
  let replyPreview  = null;
  if (replyCtx && !replyCtx.hidden) {
    replyToId    = replyCtx.dataset.replyToId ? Number(replyCtx.dataset.replyToId) : null;
    const previewEl = replyCtx.querySelector(".dm-reply-preview");
    replyPreview = previewEl?.textContent.trim() || null;
    replyCtx.hidden = true;
    replyCtx.dataset.replyToId = "";
  }

  // Optimistic bubble
  input.value = "";
  appendOptimisticBubble(content, replyPreview);

  try {
    await apiFetch(`/api/messages/conversations/${currentConversationId}`, {
      method: "POST",
      body: JSON.stringify({ content, reply_to_id: replyToId, reply_preview: replyPreview }),
    });
    lastKnownMessageId = null;
    await pollMessages(currentConversationId);
  } catch (err) {
    showDmToast(err.message || "Failed to send message.");
  }
}

/** Append a temporary optimistic bubble at the bottom of the thread. */
function appendOptimisticBubble(content, replyPreview = null) {
  const thread = document.getElementById("messageThread");
  const area   = document.getElementById("messagesArea");
  if (!thread) return;

  const quoteHtml = replyPreview
    ? `<div class="dm-bubble-quote"><span class="dm-bubble-quote-bar"></span><span class="dm-bubble-quote-text">${escapeHtml(replyPreview)}</span></div>`
    : "";

  const wrapper = document.createElement("div");
  wrapper.className = "dm-msg-group dm-msg-group--mine dm-optimistic";
  wrapper.innerHTML = `
    <div class="dm-bubbles">
      <div class="dm-bubble" data-pos="solo">${quoteHtml}${escapeHtml(content)}</div>
      <span class="dm-msg-time">Sending…</span>
    </div>`;
  thread.appendChild(wrapper);
  area.scrollTop = area.scrollHeight;
}

function showDmToast(msg) {
  const container = document.getElementById("toastContainer") || document.body;
  const el = document.createElement("div");
  el.className = "toast error";
  el.textContent = msg;
  el.style.cssText = "position:fixed;bottom:80px;right:18px;z-index:200;padding:12px 14px;border-radius:14px;background:var(--surface-toast);border:1px solid var(--accent);color:var(--text);font-size:14px;";
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── Send image message ─────────────────────────────────────────────────────

async function sendMediaMessage(file) {
  if (!currentConversationId) return;

  // Images only — reject videos before uploading
  if (!file.type.startsWith("image/")) {
    showDmToast("Only images can be sent. Video upload is currently disabled.");
    return;
  }

  // Instant preview via an object URL — revoke it once poll replaces the bubble
  const previewUrl = URL.createObjectURL(file);
  appendOptimisticImageBubble(previewUrl);

  const form = new FormData();
  form.append("media", file, file.name);
  try {
    await apiFetch(`/api/messages/conversations/${currentConversationId}/media`, {
      method: "POST",
      body: form,
    });
    lastKnownMessageId = null;
    await pollMessages(currentConversationId);
  } catch (err) {
    showDmToast(err.message || "Failed to send image. Check that the file is ≤ 5 MB.");
  } finally {
    URL.revokeObjectURL(previewUrl);
  }
}

/** Append an optimistic image bubble with a local preview. */
function appendOptimisticImageBubble(objectUrl) {
  const thread = document.getElementById("messageThread");
  const area   = document.getElementById("messagesArea");
  if (!thread) return;

  const wrapper = document.createElement("div");
  wrapper.className = "dm-msg-group dm-msg-group--mine dm-optimistic";
  wrapper.innerHTML = `
    <div class="dm-bubbles">
      <div class="dm-bubble dm-bubble--media" data-pos="solo">
        <img class="dm-media-img dm-optimistic-img" src="${escapeAttr(objectUrl)}" alt="Sending…" />
      </div>
      <span class="dm-msg-time">Sending…</span>
    </div>`;
  thread.appendChild(wrapper);
  area.scrollTop = area.scrollHeight;
}

// ── Audio recording ────────────────────────────────────────────────────────
//
// State machine:  idle → recording (waveform bar) → preview → sent
//
// Root cause fix #1: start(100) with a 100ms timeslice ensures chunks
//   accumulate even on the very first dataavailable event.
// Root cause fix #2: blob size validated before upload; empty blob shows a toast.
// Root cause fix #3: fixAudioDurations() applies the ∞-seek trick on rendered
//   <audio> elements so WebM files (which lack duration headers) show correct time.

const WAVEFORM_BARS = 36;

function getSupportedAudioMime() {
  const types = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/ogg", "audio/mp4"];
  return types.find((t) => MediaRecorder.isTypeSupported?.(t)) ?? "";
}

async function startAudioRecording() {
  if (!navigator.mediaDevices?.getUserMedia) {
    showDmToast("Audio recording is not supported in this browser.");
    return;
  }
  try {
    recStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    showDmToast("Microphone access denied. Please allow it in your browser settings.");
    return;
  }

  audioChunks  = [];
  capturedWave = null;
  audioBlob    = null;

  const mimeType = getSupportedAudioMime();
  mediaRecorder  = mimeType
    ? new MediaRecorder(recStream, { mimeType })
    : new MediaRecorder(recStream);

  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) audioChunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    stopWaveformAnim();
    clearInterval(recTimerIv);
    recTimerIv  = null;
    recDuration = Math.round((Date.now() - recStartMs) / 1000);

    const type = mediaRecorder.mimeType || mimeType || "audio/webm";
    audioBlob   = new Blob(audioChunks, { type });

    // Stop tracks now that we have the blob
    recStream?.getTracks().forEach((t) => t.stop());
    recStream = null;

    showPreviewState();
  };

  // ── Timeslice = 100ms so chunks accumulate reliably ──
  mediaRecorder.start(100);
  isRecording = true;

  showRecordingState();
  startWaveformAnim(recStream);

  // Timer
  recStartMs = Date.now();
  const timerEl = document.getElementById("dmRecTimer");
  if (timerEl) timerEl.textContent = "0:00";
  recTimerIv = setInterval(() => {
    const elapsed = Math.floor((Date.now() - recStartMs) / 1000);
    if (timerEl) timerEl.textContent = formatAudioDuration(elapsed);
  }, 500);
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    isRecording = false;
    mediaRecorder.stop(); // triggers onstop → showPreviewState
  }
}

function cancelRecording() {
  if (mediaRecorder && isRecording) {
    isRecording = false;
    // Override onstop so we don't enter preview
    mediaRecorder.onstop      = () => {};
    mediaRecorder.ondataavailable = () => {};
    try { mediaRecorder.stop(); } catch { /* ignore */ }
  }
  recStream?.getTracks().forEach((t) => t.stop());
  recStream = null;
  stopWaveformAnim();
  clearInterval(recTimerIv);
  recTimerIv = null;
  audioBlob  = null;
  audioChunks = [];
  hideRecorderUI();
}

function discardPreview() {
  if (previewAudio) {
    previewAudio.pause();
    previewAudio.src = "";
    previewAudio = null;
  }
  if (audioObjUrl) { URL.revokeObjectURL(audioObjUrl); audioObjUrl = null; }
  audioBlob = null;
  hideRecorderUI();
}

function togglePreviewPlay() {
  if (!previewAudio) return;
  const icon = document.getElementById("dmPrevPlayBtn")?.querySelector("i");
  if (previewAudio.paused) {
    previewAudio.play();
    if (icon) icon.className = "uil uil-pause";
  } else {
    previewAudio.pause();
    if (icon) icon.className = "uil uil-play";
  }
}

async function sendPreviewedAudio() {
  if (!audioBlob) return;
  if (audioBlob.size === 0) {
    showDmToast("Recording is empty — please try again.");
    return;
  }
  const btn = document.getElementById("dmPrevSendBtn");
  if (btn) btn.disabled = true;

  // Capture blob reference, then clean up UI before async send
  const blobToSend = audioBlob;
  discardPreview();
  hideRecorderUI();
  await sendAudioMessage(blobToSend);

  if (btn) btn.disabled = false;
}

// ── Recorder UI transitions ────────────────────────────────────────────────

function showRecordingState() {
  document.getElementById("messageComposer").hidden = true;
  document.getElementById("dmAudioRecorder").hidden = false;
  document.getElementById("dmRecState").hidden       = false;
  document.getElementById("dmPrevState").hidden      = true;
}

function showPreviewState() {
  document.getElementById("dmRecState").hidden  = true;
  document.getElementById("dmPrevState").hidden = false;

  const durEl = document.getElementById("dmRecDuration");
  if (durEl) durEl.textContent = formatAudioDuration(recDuration);

  // Reset play button icon
  const playIcon = document.getElementById("dmPrevPlayBtn")?.querySelector("i");
  if (playIcon) playIcon.className = "uil uil-play";

  // Set up preview Audio element for play/pause
  if (audioBlob) {
    audioObjUrl  = URL.createObjectURL(audioBlob);
    previewAudio = new Audio(audioObjUrl);
    previewAudio.addEventListener("ended", () => {
      if (playIcon) playIcon.className = "uil uil-play";
    });
  }

  // Draw static waveform from the last captured frame
  const staticCanvas = document.getElementById("dmStaticCanvas");
  if (staticCanvas && capturedWave) {
    requestAnimationFrame(() => drawStaticWaveform(staticCanvas, capturedWave));
  }
}

function hideRecorderUI() {
  document.getElementById("dmAudioRecorder").hidden = true;
  document.getElementById("messageComposer").hidden  = false;
}

// ── Waveform via Web Audio API ─────────────────────────────────────────────

function startWaveformAnim(stream) {
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.75;
    audioCtx.createMediaStreamSource(stream).connect(analyser);
    const canvas = document.getElementById("dmWaveformCanvas");
    if (canvas) animateWaveform(canvas, analyser);
  } catch {
    // Waveform is cosmetic — recording still works without it
  }
}

function stopWaveformAnim() {
  if (waveAnimId) { cancelAnimationFrame(waveAnimId); waveAnimId = null; }
  if (audioCtx)  { audioCtx.close().catch(() => {}); audioCtx = null; }
}

function animateWaveform(canvas, analyser) {
  const bufLen = analyser.frequencyBinCount;
  const data   = new Uint8Array(bufLen);
  const step   = Math.max(1, Math.floor(bufLen / WAVEFORM_BARS));

  function draw() {
    waveAnimId = requestAnimationFrame(draw);
    analyser.getByteFrequencyData(data);

    const W = canvas.clientWidth  || 200;
    const H = canvas.clientHeight || 40;
    if (canvas.width !== W) canvas.width = W;
    if (canvas.height !== H) canvas.height = H;

    const ctx2d = canvas.getContext("2d");
    ctx2d.clearRect(0, 0, W, H);

    const barW = Math.max(2, W / WAVEFORM_BARS - 2);
    const gap  = (W - barW * WAVEFORM_BARS) / Math.max(1, WAVEFORM_BARS - 1);
    capturedWave = new Float32Array(WAVEFORM_BARS);

    for (let i = 0; i < WAVEFORM_BARS; i++) {
      const val  = (data[i * step] || 0) / 255;
      capturedWave[i] = val;
      const barH = Math.max(3, val * H);
      const x    = i * (barW + gap);
      const y    = (H - barH) / 2;
      ctx2d.fillStyle = `rgba(255,77,125,${0.35 + val * 0.65})`;
      if (ctx2d.roundRect) {
        ctx2d.beginPath(); ctx2d.roundRect(x, y, barW, barH, 2); ctx2d.fill();
      } else {
        ctx2d.fillRect(x, y, barW, barH);
      }
    }
  }
  draw();
}

function drawStaticWaveform(canvas, bars) {
  const W = canvas.clientWidth  || 200;
  const H = canvas.clientHeight || 40;
  canvas.width  = W;
  canvas.height = H;

  const ctx2d = canvas.getContext("2d");
  ctx2d.clearRect(0, 0, W, H);

  const barW = Math.max(2, W / WAVEFORM_BARS - 2);
  const gap  = (W - barW * WAVEFORM_BARS) / Math.max(1, WAVEFORM_BARS - 1);

  for (let i = 0; i < WAVEFORM_BARS; i++) {
    const val  = bars[i] || 0.15;
    const barH = Math.max(3, val * H);
    const x    = i * (barW + gap);
    const y    = (H - barH) / 2;
    ctx2d.fillStyle = "rgba(255,77,125,0.65)";
    if (ctx2d.roundRect) {
      ctx2d.beginPath(); ctx2d.roundRect(x, y, barW, barH, 2); ctx2d.fill();
    } else {
      ctx2d.fillRect(x, y, barW, barH);
    }
  }
}

function formatAudioDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

// ── Duration fix for rendered <audio> elements ─────────────────────────────
// WebM files recorded by MediaRecorder lack duration metadata, so the browser
// reports 0:00 or Infinity.  Seeking to a huge time forces the browser to scan
// the file and calculate the real duration.

function fixAudioDurations(container) {
  container.querySelectorAll("audio[data-fix-duration]").forEach((audio) => {
    audio.addEventListener("loadedmetadata", function onMeta() {
      audio.removeEventListener("loadedmetadata", onMeta);
      if (!isFinite(audio.duration)) {
        audio.currentTime = 1e101; // beyond end → triggers full duration scan
        audio.addEventListener("timeupdate", function onUpdate() {
          audio.removeEventListener("timeupdate", onUpdate);
          audio.currentTime = 0;
        }, { once: true });
      }
    });
  });
}

async function sendAudioMessage(blob) {
  if (!currentConversationId) return;
  appendOptimisticBubble("🎤 Sending voice message…");
  const ext  = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "mp4" : "webm";
  const form = new FormData();
  form.append("audio", blob, `voice.${ext}`);
  try {
    await apiFetch(`/api/messages/conversations/${currentConversationId}/audio`, {
      method: "POST",
      body: form,
    });
    lastKnownMessageId = null;
    await pollMessages(currentConversationId);
  } catch (err) {
    showDmToast(err.message || "Could not send voice message. Please try again.");
  }
}

// ── Right-click context menu ───────────────────────────────────────────────

// ── Reply gestures: button click (desktop) + swipe right (mobile) ─────────

function triggerReply(btn) {
  const preview = btn.dataset.replyPreview || "";
  const ctx     = document.getElementById("dmReplyContext");
  if (!ctx) return;
  ctx.dataset.replyToId = btn.dataset.replyId;
  const previewEl = ctx.querySelector(".dm-reply-preview");
  if (previewEl) previewEl.textContent = preview;
  ctx.hidden = false;
  document.getElementById("messageInput")?.focus();
}

function setupReplyGestures() {
  const thread = document.getElementById("messageThread");
  if (!thread) return;

  // ── Desktop: click the reply button ──────────────────────────────────────
  thread.addEventListener("click", (e) => {
    const btn = e.target.closest(".dm-reply-btn");
    if (!btn) return;
    e.stopPropagation();
    triggerReply(btn);
  });

  // ── Cancel reply ──────────────────────────────────────────────────────────
  document.getElementById("dmReplyCancelBtn")?.addEventListener("click", () => {
    const ctx = document.getElementById("dmReplyContext");
    if (ctx) { ctx.hidden = true; ctx.dataset.replyToId = ""; }
  });

  // ── Mobile: swipe right on any bubble-wrap to reply ───────────────────────
  // Works identically to Instagram — swipe right on your own or the other
  // person's message, the bubble slides right, releasing past the threshold
  // triggers reply and snaps back.
  let swipeWrap    = null;   // currently tracked bubble-wrap
  let swipeStartX  = 0;
  let swipeStartY  = 0;
  let swipeTriggered = false;
  const SWIPE_THRESHOLD = 56;  // px right to trigger
  const SWIPE_MAX       = 72;  // max visual drag distance

  thread.addEventListener("touchstart", (e) => {
    const wrap = e.target.closest(".dm-bubble-wrap");
    if (!wrap) return;
    // Don't interfere with the context-menu long-press
    swipeWrap      = wrap;
    swipeStartX    = e.touches[0].clientX;
    swipeStartY    = e.touches[0].clientY;
    swipeTriggered = false;
    swipeWrap.style.transition = "none";
  }, { passive: true });

  thread.addEventListener("touchmove", (e) => {
    if (!swipeWrap) return;
    const dx = e.touches[0].clientX - swipeStartX;
    const dy = e.touches[0].clientY - swipeStartY;

    // Abort if it looks like vertical scrolling
    if (Math.abs(dy) > Math.abs(dx) * 1.2) {
      swipeWrap.style.transform = "";
      swipeWrap = null;
      return;
    }

    // Only right-swipe
    if (dx <= 0) return;

    const clamped = Math.min(dx, SWIPE_MAX);
    swipeWrap.style.transform = `translateX(${clamped}px)`;

    if (clamped >= SWIPE_THRESHOLD && !swipeTriggered) {
      swipeTriggered = true;
      navigator.vibrate?.(12);
    }
  }, { passive: true });

  thread.addEventListener("touchend", () => {
    if (!swipeWrap) return;
    // Spring back
    swipeWrap.style.transition = "transform 0.22s cubic-bezier(.25,.8,.25,1)";
    swipeWrap.style.transform  = "";

    if (swipeTriggered) {
      const btn = swipeWrap.querySelector(".dm-reply-btn");
      if (btn) triggerReply(btn);
    }

    swipeWrap = null;
  }, { passive: true });

  thread.addEventListener("touchcancel", () => {
    if (!swipeWrap) return;
    swipeWrap.style.transition = "transform 0.22s cubic-bezier(.25,.8,.25,1)";
    swipeWrap.style.transform  = "";
    swipeWrap = null;
  }, { passive: true });
}

// ── Right-click context menu ───────────────────────────────────────────────

let ctxTargetMsgId = null;
let ctxTargetConvId = null;

function setupContextMenu() {
  const menu = document.getElementById("dmCtxMenu");
  const unsendBtn = document.getElementById("dmCtxUnsend");

  function showMenuAt(msgId, convId, x, y) {
    ctxTargetMsgId = msgId;
    ctxTargetConvId = convId;
    menu.hidden = false;
    menu.style.left = `${Math.max(8, Math.min(x, window.innerWidth - 160))}px`;
    menu.style.top  = `${Math.max(8, Math.min(y, window.innerHeight - 80))}px`;
  }

  const threadEl = document.getElementById("messageThread");

  // Desktop: right-click
  threadEl?.addEventListener("contextmenu", (e) => {
    const bubble = e.target.closest(".dm-bubble[data-is-mine='true']");
    if (!bubble) return;
    e.preventDefault();
    showMenuAt(Number(bubble.dataset.msgId), currentConversationId, e.clientX, e.clientY);
  });

  // Mobile: long-press (touch-and-hold)
  let longPressTimer = null;
  threadEl?.addEventListener("touchstart", (e) => {
    const bubble = e.target.closest(".dm-bubble[data-is-mine='true']");
    if (!bubble) return;
    longPressTimer = setTimeout(() => {
      const touch = e.touches[0];
      showMenuAt(Number(bubble.dataset.msgId), currentConversationId, touch.clientX, touch.clientY - 60);
      navigator.vibrate?.(30);
    }, 500);
  }, { passive: true });
  threadEl?.addEventListener("touchend",  () => clearTimeout(longPressTimer), { passive: true });
  threadEl?.addEventListener("touchmove", () => clearTimeout(longPressTimer), { passive: true });

  // Dismiss menu on outside click / touch
  document.addEventListener("click", () => { menu.hidden = true; });
  document.addEventListener("touchstart", (e) => {
    if (!e.target.closest(".dm-bubble") && !e.target.closest(".dm-ctx-menu")) menu.hidden = true;
  }, { passive: true });
  document.addEventListener("contextmenu", (e) => {
    if (!e.target.closest(".dm-bubble[data-is-mine='true']")) menu.hidden = true;
  });

  unsendBtn?.addEventListener("click", async () => {
    menu.hidden = true;
    if (!ctxTargetMsgId || !ctxTargetConvId) return;
    try {
      await apiFetch(
        `/api/messages/conversations/${ctxTargetConvId}/messages/${ctxTargetMsgId}`,
        { method: "DELETE" }
      );
      // Remove the bubble-wrap (and its group if now empty)
      const bubble = document.querySelector(`.dm-bubble[data-msg-id="${ctxTargetMsgId}"]`);
      if (bubble) {
        const bubbleWrap = bubble.closest(".dm-bubble-wrap") || bubble;
        const bubblesWrap = bubble.closest(".dm-bubbles");
        bubbleWrap.remove();
        if (bubblesWrap && !bubblesWrap.querySelector(".dm-bubble")) {
          bubblesWrap.closest(".dm-msg-group")?.remove();
        }
      }
      lastKnownMessageId = null; // force re-sync on next poll
    } catch {
      // silent
    }
  });
}

// ── Polling ────────────────────────────────────────────────────────────────

function startPolling(conversationId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(() => pollMessages(conversationId), 5000);
}

async function updateUnreadBadge() {
  try {
    const data = await apiFetch("/api/messages/unread-count", { method: "GET" });
    const badge = document.getElementById("messageBadge");
    const count = Number(data.unread_messages || 0);
    badge.textContent = String(count);
    badge.hidden = count === 0;
  } catch {
    // Keep polling resilient
  }
}

// ── Mobile helpers ─────────────────────────────────────────────────────────

function showThread() {
  document.getElementById("dmSidebar").classList.add("dm-sidebar--hidden");
  document.getElementById("dmEmpty").hidden = true;
  document.getElementById("threadHeader").hidden = false;
  document.getElementById("messagesArea").hidden = false;
  document.getElementById("messageComposer").hidden = false;
}

// ── Utilities ──────────────────────────────────────────────────────────────

function formatRelativeTime(dateLike) {
  const diffSec = Math.floor((Date.now() - new Date(dateLike).getTime()) / 1000);
  if (diffSec < 60) return "Just now";
  const m = Math.floor(diffSec / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) { return escapeHtml(value); }
