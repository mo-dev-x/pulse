import { apiFetch, requireAuth, logout, getAssetUrl } from "./auth.js";
import { getPostAvatarUrl, getProfileHref, getUserAvatarUrl } from "./avatar.js";
import { initLanguageControls } from "./i18n.js";
import { initOfflineBanner, initThemeToggle, initUnreadBadges } from "./theme.js";

const els = {
  topbarAvatar: document.getElementById("topbarAvatar"),
  sidebarAvatar: document.getElementById("sidebarAvatar"),
  sidebarName: document.getElementById("sidebarName"),
  sidebarHandle: document.getElementById("sidebarHandle"),

  profileAvatar: document.getElementById("profileAvatar"),
  profileDisplayName: document.getElementById("profileDisplayName"),
  profileHandle: document.getElementById("profileHandle"),
  profileBio: document.getElementById("profileBio"),
  profileCover: document.getElementById("profileCover"),

  statPosts: document.getElementById("statPosts"),
  statFollowers: document.getElementById("statFollowers"),
  statFollowing: document.getElementById("statFollowing"),

  aboutName: document.getElementById("aboutName"),
  aboutHandle: document.getElementById("aboutHandle"),
  aboutLocation: document.getElementById("aboutLocation"),
  aboutWebsite: document.getElementById("aboutWebsite"),
  aboutVisibility: document.getElementById("aboutVisibility"),
  aboutEmailRow: document.getElementById("aboutEmailRow"),
  aboutEmail: document.getElementById("aboutEmail"),
  aboutJoined: document.getElementById("aboutJoined"),

  summaryPublicPosts: document.getElementById("summaryPublicPosts"),
  summaryAnonymousRow: document.getElementById("summaryAnonymousRow"),
  summaryAnonymousPosts: document.getElementById("summaryAnonymousPosts"),
  summaryFollowers: document.getElementById("summaryFollowers"),
  summaryFollowing: document.getElementById("summaryFollowing"),

  sideVisibility: document.getElementById("sideVisibility"),
  sideLocation: document.getElementById("sideLocation"),
  sideWebsite: document.getElementById("sideWebsite"),
  sideJoined: document.getElementById("sideJoined"),

  profilePostsFeed: document.getElementById("profilePostsFeed"),
  profilePostsState: document.getElementById("profilePostsState"),
  mediaGrid: document.getElementById("mediaGrid"),
  mediaState: document.getElementById("mediaState"),

  pinnedPanel: document.getElementById("pinnedPanel"),
  pinnedPostBox: document.getElementById("pinnedPostBox"),
  pinnedState: document.getElementById("pinnedState"),

  userChip: document.getElementById("userChip"),
  btnLogout: document.getElementById("btnLogout"),
  btnViewFeed: document.getElementById("btnViewFeed"),
  btnViewFeedLeft: document.getElementById("btnViewFeedLeft"),
  btnShareProfile: document.getElementById("btnShareProfile"),
  btnFollowers: document.getElementById("btnFollowers"),
  btnFollowing: document.getElementById("btnFollowing"),
  btnFriends: document.getElementById("btnFriends"),
  btnFollowToggle: document.getElementById("btnFollowToggle"),
  btnEditProfile: document.getElementById("btnEditProfile"),
  btnEditProfileMenu: document.getElementById("btnEditProfileMenu"),
  btnEditSide: document.getElementById("btnEditSide"),

  peopleModal: document.getElementById("peopleModal"),
  peopleModalTitle: document.getElementById("peopleModalTitle"),
  peopleList: document.getElementById("peopleList"),
  peopleState: document.getElementById("peopleState"),
  btnClosePeopleModal: document.getElementById("btnClosePeopleModal"),

  editProfileModal: document.getElementById("editProfileModal"),
  editProfileForm: document.getElementById("editProfileForm"),
  editDisplayName: document.getElementById("editDisplayName"),
  editBio: document.getElementById("editBio"),
  editLocation: document.getElementById("editLocation"),
  editWebsite: document.getElementById("editWebsite"),
  editAvatarFile: document.getElementById("editAvatarFile"),
  editHeaderFile: document.getElementById("editHeaderFile"),
  editAvatarPreview: document.getElementById("editAvatarPreview"),
  editHeaderPreview: document.getElementById("editHeaderPreview"),
  editHeaderFocusX: document.getElementById("editHeaderFocusX"),
  editHeaderFocusY: document.getElementById("editHeaderFocusY"),
  editProfileError: document.getElementById("editProfileError"),
  btnCloseEditModal: document.getElementById("btnCloseEditModal"),
  btnCancelEdit: document.getElementById("btnCancelEdit"),
};

let currentUser = null;
let profilePayload = null;
let profileUser = null;
let publicPosts = [];
let anonymousPosts = [];
let visiblePosts = [];
let viewingOwnProfile = true;
let currentPinnedPostId = null;
let pendingHeaderObjectUrl = null;

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLanguageControls();
  initThemeToggle();
  initOfflineBanner();
  initUnreadBadges();
  setupMenu();
  setupTabs();
  setupActions();
  setupModals();
  setupGlobalUserSearch();

  try {
    if (els.profilePostsFeed) {
      els.profilePostsFeed.innerHTML = renderSkeletonCards(3);
    }
    if (els.mediaGrid) {
      els.mediaGrid.innerHTML = renderSkeletonCards(2);
    }
    await initProfilePage();
  } catch (err) {
    console.error("Profile page init error:", err);
    if (els.profilePostsState) {
      els.profilePostsState.textContent = err.message || "Could not load profile.";
      els.profilePostsState.style.display = "block";
    }
    if (els.mediaState) {
      els.mediaState.textContent = "Could not load media.";
      els.mediaState.style.display = "block";
    }
    showToast(err.message || "Could not load profile", "error");
  }
});

async function initProfilePage() {
  const meRes = await apiFetch("/api/auth/me", { method: "GET" });
  currentUser = meRes.user;

  const requestedUsername = getRequestedUsername() || currentUser.username;

  const profileRes = await apiFetch(`/api/users/@${encodeURIComponent(requestedUsername)}`, {
    method: "GET",
  });

  profilePayload = profileRes;
  profileUser = profileRes.user || {};
  viewingOwnProfile = profileUser.username === currentUser.username;
  currentPinnedPostId = viewingOwnProfile ? (currentUser.pinned_post_id || null) : null;

  await loadProfilePosts();

  visiblePosts = sortPostsByDate(
    viewingOwnProfile ? [...publicPosts, ...anonymousPosts] : [...publicPosts]
  );

  renderCurrentUserChrome();
  renderViewedProfile();
  renderPinnedPost();
  renderPosts(visiblePosts);
  renderMedia(visiblePosts);

  document.title = `PULSE — ${profileUser.display_name || profileUser.username || "Profile"}`;
}

function getRequestedUsername() {
  const params = new URLSearchParams(window.location.search);
  const raw = (params.get("u") || "").trim();
  if (!raw) return null;
  return raw.replace(/^@/, "");
}

async function loadProfilePosts() {
  if (viewingOwnProfile) {
    const [myPostsRes, myAnonRes] = await Promise.all([
      apiFetch("/api/posts/me", { method: "GET" }),
      apiFetch("/api/posts/me/anonymous", { method: "GET" }),
    ]);

    publicPosts = (myPostsRes.posts || []).map(normalizePost);
    anonymousPosts = (myAnonRes.posts || []).map(normalizePost);
  } else {
    const userPostsRes = await apiFetch(`/api/posts/@${encodeURIComponent(profileUser.username)}`, {
      method: "GET",
    });

    publicPosts = (userPostsRes.posts || []).map(normalizePost);
    anonymousPosts = [];
  }
}

function setupMenu() {
  if (!els.userChip) return;

  const profileLink = document.getElementById("topbarProfileLink");

  els.userChip.addEventListener("click", (e) => {
    if (profileLink && profileLink.contains(e.target)) {
      return;
    }

    e.stopPropagation();
    els.userChip.classList.toggle("open");
  });

  document.addEventListener("click", () => {
    els.userChip.classList.remove("open");
  });
}

function setupTabs() {
  const tabs = document.querySelectorAll(".profile-tab");
  const panels = document.querySelectorAll(".profile-tab-panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const key = tab.dataset.tab;
      document.getElementById(`tab-${key}`).classList.add("active");
    });
  });
}

function setupActions() {
  els.btnLogout?.addEventListener("click", () => logout());

  els.btnViewFeed?.addEventListener("click", () => {
    window.location.href = "feed.html";
  });

  els.btnViewFeedLeft?.addEventListener("click", () => {
    window.location.href = "feed.html";
  });

  els.btnShareProfile?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      showToast("Profile link copied", "success");
    } catch {
      showToast("Could not copy the profile link.", "error");
    }
  });
  els.btnFollowers?.addEventListener("click", async () => {
    await openPeopleModal("followers");
  });

  els.btnFollowing?.addEventListener("click", async () => {
    await openPeopleModal("following");
  });

  els.btnFriends?.addEventListener("click", async () => {
    await openPeopleModal("friends");
  });

  els.btnFollowToggle?.addEventListener("click", async () => {
    await toggleFollowProfile();
  });

  els.btnEditProfile?.addEventListener("click", openEditModal);
  els.btnEditProfileMenu?.addEventListener("click", openEditModal);
  els.btnEditSide?.addEventListener("click", openEditModal);

  els.editAvatarFile?.addEventListener("change", onEditAvatarPreview);
  els.editHeaderFile?.addEventListener("change", onEditHeaderPreview);
  els.editHeaderFocusX?.addEventListener("input", syncHeaderPreviewPosition);
  els.editHeaderFocusY?.addEventListener("input", syncHeaderPreviewPosition);
}

function setupModals() {
  els.btnClosePeopleModal?.addEventListener("click", closePeopleModal);
  els.btnCloseEditModal?.addEventListener("click", closeEditModal);
  els.btnCancelEdit?.addEventListener("click", closeEditModal);

  els.peopleModal?.addEventListener("click", (e) => {
    if (e.target === els.peopleModal) closePeopleModal();
  });

  els.editProfileModal?.addEventListener("click", (e) => {
    if (e.target === els.editProfileModal) closeEditModal();
  });

  els.editProfileForm?.addEventListener("submit", onEditProfileSubmit);
}

async function toggleFollowProfile() {
  if (viewingOwnProfile || !profileUser?.username) return;

  const isFollowing = Boolean(profileUser?.is_following);
  const username = profileUser.username;

  try {
    if (els.btnFollowToggle) {
      els.btnFollowToggle.disabled = true;
    }

    if (isFollowing) {
      await apiFetch(`/api/unfollow/@${encodeURIComponent(username)}`, {
        method: "DELETE",
      });
      showToast(`Unfollowed @${username}`, "success");
    } else {
      await apiFetch(`/api/follow/@${encodeURIComponent(username)}`, {
        method: "POST",
      });
      showToast(`Now following @${username}`, "success");
    }

    await initProfilePage();
  } catch (err) {
    showToast(err.message || "Follow action failed", "error");
  } finally {
    if (els.btnFollowToggle) {
      els.btnFollowToggle.disabled = false;
    }
  }
}

async function openPeopleModal(type) {
  if (!profileUser?.username || !els.peopleModal || !els.peopleList || !els.peopleState) return;

  els.peopleModal.classList.add("open");
  els.peopleModal.setAttribute("aria-hidden", "false");
  els.peopleList.innerHTML = "";
  els.peopleState.style.display = "block";
  els.peopleState.textContent = "Loading...";

  if (type === "followers") {
    els.peopleModalTitle.textContent = `Followers of @${profileUser.username}`;
  } else if (type === "following") {
    els.peopleModalTitle.textContent = `Following of @${profileUser.username}`;
  } else {
    els.peopleModalTitle.textContent = viewingOwnProfile
      ? "Your friends"
      : `Friends of @${profileUser.username}`;
  }

  try {
    const endpoint = type === "friends"
      ? "/api/users/me/friends"
      : `/api/users/@${encodeURIComponent(profileUser.username)}/${type}`;

    const data = await apiFetch(endpoint, { method: "GET" });

    const people = data[type] || [];

    if (!people.length) {
      els.peopleState.textContent =
        type === "followers"
          ? "No followers yet."
          : type === "following"
            ? "No following yet."
            : "No friends yet.";
      return;
    }

    els.peopleState.style.display = "none";
    renderPeopleList(people, type);
  } catch (err) {
    els.peopleState.textContent = err.message || "Could not load people.";
  }
}

function renderPeopleList(people, type) {
  els.peopleList.innerHTML = people.map((person) => {
    const avatarUrl = getUserAvatarUrl(person, getAssetUrl);

    return `
      <div class="person-row">
        <a class="person-left" href="profile.html?u=${encodeURIComponent(person.username)}">
          <img class="avatar" src="${escapeAttr(avatarUrl)}" alt="User" />
          <div class="person-meta">
            <div class="person-name">${escapeHtml(person.display_name || person.username)}</div>
            <div class="person-handle">@${escapeHtml(person.username)}</div>
          </div>
        </a>

        ${
          viewingOwnProfile && type === "following"
            ? `<button class="btn btn-ghost btn-sm" data-unfollow-user="${escapeAttr(person.username)}">Unfollow</button>`
            : ""
        }
      </div>
    `;
  }).join("");

  els.peopleList.querySelectorAll("[data-unfollow-user]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const username = btn.dataset.unfollowUser;
      await unfollowFromPeopleList(username, btn);
    });
  });
}

async function unfollowFromPeopleList(username, btn) {
  try {
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Removing...";
    }

    await apiFetch(`/api/unfollow/@${encodeURIComponent(username)}`, {
      method: "DELETE",
    });

    showToast(`Unfollowed @${username}`, "success");
    await openPeopleModal("following");
    await initProfilePage();
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Unfollow";
    }
    showToast(err.message || "Unfollow failed", "error");
  }
}

function closePeopleModal() {
  if (!els.peopleModal) return;
  els.peopleModal.classList.remove("open");
  els.peopleModal.setAttribute("aria-hidden", "true");
}

function openEditModal() {
  if (!viewingOwnProfile || !els.editProfileModal) return;

  if (els.editDisplayName) {
    els.editDisplayName.value = currentUser?.display_name || currentUser?.username || "";
  }

  if (els.editBio) {
    els.editBio.value = currentUser?.bio || "";
  }

  if (els.editLocation) {
    els.editLocation.value = currentUser?.location || "";
  }

  if (els.editWebsite) {
    els.editWebsite.value = currentUser?.website || "";
  }

  if (els.editAvatarPreview) {
    const avatarUrl = getUserAvatarUrl(currentUser, getAssetUrl);
    els.editAvatarPreview.src = avatarUrl;
  }

  resetHeaderPreview();

  hideEditProfileError();
  els.editProfileModal.classList.add("open");
  els.editProfileModal.setAttribute("aria-hidden", "false");
}

function closeEditModal() {
  if (!els.editProfileModal) return;

  els.editProfileModal.classList.remove("open");
  els.editProfileModal.setAttribute("aria-hidden", "true");
  hideEditProfileError();

  if (els.editProfileForm) els.editProfileForm.reset();

  if (els.editAvatarPreview) {
    const avatarUrl = getUserAvatarUrl(currentUser, getAssetUrl);
    els.editAvatarPreview.src = avatarUrl;
  }

  if (pendingHeaderObjectUrl) {
    URL.revokeObjectURL(pendingHeaderObjectUrl);
    pendingHeaderObjectUrl = null;
  }

  resetHeaderPreview();
}

function onEditAvatarPreview() {
  const file = els.editAvatarFile?.files?.[0];
  if (!file || !els.editAvatarPreview) return;

  const objectUrl = URL.createObjectURL(file);
  els.editAvatarPreview.src = objectUrl;
}

function onEditHeaderPreview() {
  const file = els.editHeaderFile?.files?.[0];
  if (!file || !els.editHeaderPreview) return;

  if (pendingHeaderObjectUrl) {
    URL.revokeObjectURL(pendingHeaderObjectUrl);
  }

  pendingHeaderObjectUrl = URL.createObjectURL(file);
  els.editHeaderPreview.style.backgroundImage = `
    linear-gradient(rgba(10,10,20,0.22), rgba(10,10,20,0.4)),
    url("${pendingHeaderObjectUrl}")
  `;
  syncHeaderPreviewPosition();
}

function getHeaderFocusKey(username) {
  return `pulse_header_focus_${username || "me"}`;
}

function getSavedHeaderFocus(username) {
  try {
    const raw = localStorage.getItem(getHeaderFocusKey(username));
    if (!raw) return { x: 50, y: 50 };
    const parsed = JSON.parse(raw);
    return {
      x: Number.isFinite(parsed?.x) ? parsed.x : 50,
      y: Number.isFinite(parsed?.y) ? parsed.y : 50,
    };
  } catch {
    return { x: 50, y: 50 };
  }
}

function saveHeaderFocus(username, x, y) {
  localStorage.setItem(getHeaderFocusKey(username), JSON.stringify({ x, y }));
}

function resetHeaderPreview() {
  if (!els.editHeaderPreview) return;

  const username = currentUser?.username || "me";
  const focus = getSavedHeaderFocus(username);
  if (els.editHeaderFocusX) els.editHeaderFocusX.value = String(focus.x);
  if (els.editHeaderFocusY) els.editHeaderFocusY.value = String(focus.y);

  const headerImage = currentUser?.header_image ? getAssetUrl(currentUser.header_image) : "";
  els.editHeaderPreview.style.backgroundImage = headerImage
    ? `linear-gradient(rgba(10,10,20,0.22), rgba(10,10,20,0.4)), url("${headerImage}")`
    : "";
  syncHeaderPreviewPosition();
}

function syncHeaderPreviewPosition() {
  const x = Number(els.editHeaderFocusX?.value || 50);
  const y = Number(els.editHeaderFocusY?.value || 50);
  if (els.editHeaderPreview) {
    els.editHeaderPreview.style.backgroundPosition = `${x}% ${y}%`;
  }
}

async function onEditProfileSubmit(e) {
  e.preventDefault();

  if (!viewingOwnProfile) return;

  const name = (els.editDisplayName?.value || "").trim();
  const bio = (els.editBio?.value || "").trim();
  const location = (els.editLocation?.value || "").trim();
  const website = (els.editWebsite?.value || "").trim();
  const avatarFile = els.editAvatarFile?.files?.[0] || null;
  const headerFile = els.editHeaderFile?.files?.[0] || null;
  const submitBtn = els.editProfileForm?.querySelector('button[type="submit"]');

  if (!name) {
    showEditProfileError("Display name cannot be empty.");
    return;
  }

  if (name.length > 100) {
    showEditProfileError("Display name must be 100 characters or less.");
    return;
  }

  if (bio.length > 500) {
    showEditProfileError("Bio must be 500 characters or less.");
    return;
  }

  if (location.length > 100) {
    showEditProfileError("Location must be 100 characters or less.");
    return;
  }

  if (website.length > 255) {
    showEditProfileError("Website must be 255 characters or less.");
    return;
  }

  try {
    hideEditProfileError();

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Saving...";
    }

    if (avatarFile) {
      const fd = new FormData();
      fd.append("file", avatarFile);

      await apiFetch("/api/auth/upload-profile-pic", {
        method: "POST",
        body: fd,
      });
    }

    if (headerFile) {
      const fd = new FormData();
      fd.append("file", headerFile);

      await apiFetch("/api/auth/upload-header", {
        method: "POST",
        body: fd,
      });
    }

    await apiFetch("/api/auth/update-profile", {
      method: "PATCH",
      body: JSON.stringify({
        display_name: name,
        bio,
        location,
        website,
      }),
    });

    saveHeaderFocus(
      currentUser?.username,
      Number(els.editHeaderFocusX?.value || 50),
      Number(els.editHeaderFocusY?.value || 50),
    );

    showToast("Profile updated", "success");
    closeEditModal();
    await initProfilePage();
  } catch (err) {
    showEditProfileError(err.message || "Profile update failed");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Save";
    }
  }
}

function showEditProfileError(message) {
  if (!els.editProfileError) return;
  els.editProfileError.textContent = message;
  els.editProfileError.style.display = "block";
}

function hideEditProfileError() {
  if (!els.editProfileError) return;
  els.editProfileError.textContent = "";
  els.editProfileError.style.display = "none";
}

function renderCurrentUserChrome() {
  const displayName = currentUser?.display_name || currentUser?.username || "Pulse User";
  const username = currentUser?.username || "user";

  const avatarUrl = getUserAvatarUrl(currentUser, getAssetUrl);

  if (els.topbarAvatar) els.topbarAvatar.src = avatarUrl;
  if (els.sidebarAvatar) els.sidebarAvatar.src = avatarUrl;
  if (els.sidebarName) els.sidebarName.textContent = displayName;
  if (els.sidebarHandle) els.sidebarHandle.textContent = `@${username}`;
}

function renderViewedProfile() {
  const displayName = profileUser?.display_name || profileUser?.username || "Pulse User";
  const username = profileUser?.username || "user";
  const bio = profileUser?.bio || "No bio yet.";
  const location = profileUser?.location || "—";
  const website = profileUser?.website || "—";
  const visibility = humanizeVisibility(profileUser?.profile_visibility);
  const joined = formatJoined(profileUser?.created_at);
  const email = profileUser?.email || null;

  const avatarUrl = getUserAvatarUrl(profileUser, getAssetUrl);

  if (els.profileAvatar) els.profileAvatar.src = avatarUrl;
  if (els.profileDisplayName) els.profileDisplayName.textContent = displayName;
  if (els.profileHandle) els.profileHandle.textContent = `@${username}`;
  if (els.profileBio) els.profileBio.textContent = bio;

  if (els.profileCover) {
    const headerImage = viewingOwnProfile ? currentUser?.header_image : profileUser?.header_image;
    const focus = getSavedHeaderFocus(profileUser?.username);

    if (headerImage) {
      els.profileCover.classList.add("has-image");
      els.profileCover.style.backgroundImage = `
        linear-gradient(rgba(10,10,20,0.28), rgba(10,10,20,0.38)),
        url("${getAssetUrl(headerImage)}")
      `;
      els.profileCover.style.backgroundPosition = `${focus.x}% ${focus.y}%`;
    } else {
      els.profileCover.classList.remove("has-image");
      els.profileCover.style.backgroundImage = "";
      els.profileCover.style.backgroundPosition = "";
    }
  }

  const totalVisiblePosts = visiblePosts.length;
  const followerCount = Number(profileUser?.follower_count ?? 0);
  const followingCount = Number(profileUser?.following_count ?? 0);

  if (els.statPosts) els.statPosts.textContent = String(totalVisiblePosts);
  if (els.statFollowers) els.statFollowers.textContent = String(followerCount);
  if (els.statFollowing) els.statFollowing.textContent = String(followingCount);

  if (els.btnFollowers) {
    els.btnFollowers.innerHTML = `<i class="uil uil-users-alt"></i> Followers (${followerCount})`;
  }

  if (els.btnFollowing) {
    els.btnFollowing.innerHTML = `<i class="uil uil-user-plus"></i> Following (${followingCount})`;
  }

  if (els.btnFriends) {
    els.btnFriends.innerHTML = `<i class="uil uil-heart"></i> Friends`;
  }

  if (els.aboutName) els.aboutName.textContent = displayName;
  if (els.aboutHandle) els.aboutHandle.textContent = `@${username}`;
  if (els.aboutLocation) els.aboutLocation.textContent = location;
  if (els.aboutWebsite) els.aboutWebsite.textContent = website;
  if (els.aboutVisibility) els.aboutVisibility.textContent = visibility;
  if (els.aboutJoined) els.aboutJoined.textContent = joined;

  if (els.aboutEmailRow) {
    setHidden(els.aboutEmailRow, !email);
  }
  if (els.aboutEmail) {
    els.aboutEmail.textContent = email || "—";
  }

  if (els.summaryPublicPosts) {
    els.summaryPublicPosts.textContent = `${publicPosts.length} public post${publicPosts.length !== 1 ? "s" : ""}`;
  }

  if (els.summaryAnonymousRow) {
    setHidden(els.summaryAnonymousRow, !viewingOwnProfile);
  }

  if (els.summaryAnonymousPosts) {
    els.summaryAnonymousPosts.textContent = `${anonymousPosts.length} anonymous post${anonymousPosts.length !== 1 ? "s" : ""}`;
  }

  if (els.summaryFollowers) {
    els.summaryFollowers.textContent = `${followerCount} follower${followerCount !== 1 ? "s" : ""}`;
  }

  if (els.summaryFollowing) {
    els.summaryFollowing.textContent = `${followingCount} following`;
  }

  if (els.sideVisibility) els.sideVisibility.textContent = visibility;
  if (els.sideLocation) els.sideLocation.textContent = location;
  if (els.sideWebsite) els.sideWebsite.textContent = website;
  if (els.sideJoined) els.sideJoined.textContent = joined;

  updateProfileActions();
}

function updateProfileActions() {
  const isFollowing = Boolean(profileUser?.is_following);

  setHidden(els.btnFollowToggle, viewingOwnProfile);
  setHidden(els.btnEditProfile, !viewingOwnProfile);
  setHidden(els.btnEditProfileMenu, !viewingOwnProfile);
  setHidden(els.btnEditSide, !viewingOwnProfile);
  setHidden(els.btnFriends, !viewingOwnProfile);

  if (els.btnFollowToggle && !viewingOwnProfile) {
    els.btnFollowToggle.innerHTML = isFollowing
      ? `<i class="uil uil-check"></i> Following`
      : `<i class="uil uil-user-plus"></i> Follow`;

    els.btnFollowToggle.classList.toggle("btn-accent", !isFollowing);
    els.btnFollowToggle.classList.toggle("btn-ghost", isFollowing);
  }
}

function renderPinnedPost() {
  if (!els.pinnedPostBox || !els.pinnedState) return;

  els.pinnedPostBox.innerHTML = "";

  const pinnedPost = getPinnedPost();

  if (!pinnedPost) {
    els.pinnedState.textContent = viewingOwnProfile
      ? "No pinned post yet."
      : "This profile has no pinned post.";
    els.pinnedState.style.display = "block";
    return;
  }

  els.pinnedState.style.display = "none";
  els.pinnedPostBox.appendChild(createPostCard(pinnedPost));
}

function getPinnedPost() {
  if (viewingOwnProfile && currentPinnedPostId) {
    return publicPosts.find((post) => post.id === currentPinnedPostId) || null;
  }

  if (profilePayload?.pinned_post) {
    return normalizePost(profilePayload.pinned_post);
  }

  return null;
}

function renderPosts(posts) {
  if (!els.profilePostsFeed || !els.profilePostsState) return;

  els.profilePostsFeed.innerHTML = "";

  if (!posts.length) {
    els.profilePostsState.textContent = viewingOwnProfile
      ? "You don’t have posts yet."
      : "No public posts yet.";
    els.profilePostsState.style.display = "block";
    return;
  }

  els.profilePostsState.style.display = "none";

  posts.forEach((post) => {
    els.profilePostsFeed.appendChild(createPostCard(post));
  });
}

function renderMedia(posts) {
  if (!els.mediaGrid || !els.mediaState) return;

  els.mediaGrid.innerHTML = "";

  const mediaPosts = posts.filter((post) => post.imagePath);

  if (!mediaPosts.length) {
    els.mediaState.textContent = "No media yet.";
    els.mediaState.style.display = "block";
    return;
  }

  els.mediaState.style.display = "none";

  mediaPosts.forEach((post) => {
    const item = document.createElement("div");
    item.className = "media-item";
    item.innerHTML = `
  <img
    src="${escapeAttr(getAssetUrl(post.imagePath))}"
    alt="Post media"
    onerror="this.closest('.media-item').innerHTML='<div style=&quot;padding:14px;color:rgba(229,231,235,.65)&quot;>Media unavailable ❌</div>';"
  />`;
    els.mediaGrid.appendChild(item);
  });
}

function normalizePost(p) {
  const media = Array.isArray(p.media) ? p.media : [];
  const firstImage = media.find((m) => m.file_type === "image");
  const isAnonymous = Boolean(p.is_anonymous);
  const author = p.author || {};
  const zone = p.zone || null;

  const authorName = isAnonymous
    ? (author.pseudonym || "Anonymous")
    : (author.display_name || author.username || "User");

  const handle = isAnonymous
    ? "@anonymous"
    : (author.username ? `@${author.username}` : "@user");

  const avatarUrl = getPostAvatarUrl(author, isAnonymous, getAssetUrl);

  return {
    id: p.id,
    text: p.content || "",
    isAnonymous,
    authorName,
    handle,
    avatarUrl,
    profileHref: !isAnonymous && author.username ? getProfileHref(author.username) : "",
    zoneId: zone?.id || null,
    zoneName: zone?.name || "Campus",
    timeRaw: p.created_at || "",
    timeLabel: formatRelativeTime(p.created_at),
    sentiment: p.sentiment || "neutral",
    emotionLabel: p.emotion_label || "",
    emotionDisplay: p.emotion_display || "",
    imagePath: firstImage?.file_path || "",
    reactions: {
      love: p.reactions?.["❤️"] ?? 0,
      fire: p.reactions?.["🔥"] ?? 0,
      sad: p.reactions?.["😢"] ?? 0,
    },
  }
}
  function createPostCard(post) {
    const card = document.createElement("article");
    card.className = "panel post";

    const badge = sentimentBadge(post.sentiment, post.emotionDisplay, post.emotionLabel);
    const canPin = viewingOwnProfile && !post.isAnonymous;
    const isPinned = canPin && currentPinnedPostId === post.id;

    card.innerHTML = `
    <div class="post-head">
      <div class="post-user">
        ${post.profileHref ? `
          <a class="post-user-link" href="${escapeAttr(post.profileHref)}" aria-label="View ${escapeAttr(post.authorName)}'s profile">
            <img class="avatar" src="${escapeAttr(post.avatarUrl)}" alt="${escapeAttr(post.authorName)}" />
            <div class="post-meta">
              <div class="u">
                ${escapeHtml(post.authorName)}
                <span class="badge ${badge.cls}">${badge.label}</span>
              </div>
              <div class="m">${escapeHtml(post.handle)}</div>
            </div>
          </a>
        ` : `
          <img class="avatar" src="${escapeAttr(post.avatarUrl)}" alt="User" />
          <div class="post-meta">
            <div class="u">
              ${escapeHtml(post.authorName)}
              <span class="badge ${badge.cls}">${badge.label}</span>
            </div>
            <div class="m">${escapeHtml(post.handle)}</div>
          </div>
        `}
        <div class="post-meta post-meta-secondary">
          <div class="m">
            <button class="zone-pill" data-zone-name="${escapeAttr(post.zoneName)}">${escapeHtml(post.zoneName)}</button> •
            ${escapeHtml(post.timeLabel)}
          </div>
        </div>
      </div>
      <div class="post-menu">
        ${canPin
        ? `<button class="iconbtn" data-pin-action="${isPinned ? "unpin" : "pin"}" title="${isPinned ? "Unpin post" : "Pin post"}">
                ${isPinned ? "📌" : "📍"}
              </button>`
        : ""
      }
      </div>
    </div>

    ${post.text ? `<div class="post-text">${escapeHtml(post.text)}</div>` : ""}

    ${post.imagePath
        ? `
      <div class="post-media">
        <img
          src="${escapeAttr(getAssetUrl(post.imagePath))}"
          alt="Post media"
          onerror="this.closest('.post-media').innerHTML='<div style=&quot;padding:14px;color:rgba(229,231,235,.65)&quot;>Media unavailable ❌</div>';"
        />
      </div>
    `
        : ""
      }

    <div class="post-actions">
      <div class="actions-left">
        <div class="reaction">
          <button class="react-btn" disabled>❤️ <span>${post.reactions.love ?? 0}</span></button>
          <button class="react-btn" disabled>🔥 <span>${post.reactions.fire ?? 0}</span></button>
          <button class="react-btn" disabled>😢 <span>${post.reactions.sad ?? 0}</span></button>
        </div>
      </div>
    </div>
  `;

    const pinBtn = card.querySelector("[data-pin-action]");
    if (pinBtn) {
      pinBtn.addEventListener("click", async () => {
        await onPinToggle(post);
      });
    }

    const zoneBtn = card.querySelector("[data-zone-name]");
    if (zoneBtn && post.zoneId) {
      zoneBtn.addEventListener("click", () => {
        window.location.href = `zone.html?id=${encodeURIComponent(post.zoneId)}`;
      });
    }
    return card;
  }

async function onPinToggle(post) {
  if (!viewingOwnProfile || post.isAnonymous) return;

  try {
    if (currentPinnedPostId === post.id) {
      await apiFetch("/api/posts/pin", {
        method: "DELETE",
      });
      showToast("Pinned post removed", "success");
    } else {
      await apiFetch(`/api/posts/${post.id}/pin`, {
        method: "PATCH",
      });
      showToast("Post pinned to profile", "success");
    }

    await initProfilePage();
  } catch (err) {
    showToast(err.message || "Pin action failed", "error");
  }
}

  function sentimentBadge(sentiment, emotionDisplay = "", emotionLabel = "") {
    const raw = String(emotionDisplay || emotionLabel || sentiment || "neutral").trim();
    const value = raw.toLowerCase();
    if (/(joy|love|excited|hope|positive|calm|grateful|happy)/i.test(value)) return { cls: "green", label: `🟢 ${raw}` };
    if (/(anger|sad|fear|stress|anx|negative|frustr|overwhelm|disgust)/i.test(value)) return { cls: "red", label: `🔴 ${raw}` };
    return { cls: "yellow", label: `🟡 ${raw}` };
  }

function humanizeVisibility(value) {
  const normalized = String(value || "public").toLowerCase();

  if (normalized === "followers") return "Followers only";
  if (normalized === "private") return "Private";
  return "Public";
}

function sortPostsByDate(posts) {
  return [...posts].sort((a, b) => {
    return new Date(b.timeRaw).getTime() - new Date(a.timeRaw).getTime();
  });
}

function formatRelativeTime(dateLike) {
  const d = new Date(dateLike);
  if (Number.isNaN(d.getTime())) return "Recently";

  const diffMs = Date.now() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return "Just now";

  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;

  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;

  return d.toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

  function formatJoined(dateLike) {
    const d = new Date(dateLike);
    if (Number.isNaN(d.getTime())) return "Recently joined";

    return d.toLocaleDateString([], {
      month: "long",
      year: "numeric",
    });
  }

function setHidden(el, hidden) {
  if (!el) return;
  el.classList.toggle("hidden", Boolean(hidden));
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 2600);
}

function setupGlobalUserSearch() {
  const input = document.getElementById("globalSearch");
  const resultsEl = document.getElementById("searchResults");

  if (!input || !resultsEl) return;

  let debounceTimer = null;

  input.addEventListener("input", () => {
    const query = input.value.trim();
    clearTimeout(debounceTimer);

    if (query.length < 2) {
      hideSearchResults();
      return;
    }

    debounceTimer = setTimeout(async () => {
      await searchUsers(query);
    }, 250);
  });

  input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const query = input.value.trim();
    if (query.length < 2) return;
    event.preventDefault();
    window.location.href = `search.html?q=${encodeURIComponent(query)}`;
  });

  document.addEventListener("click", (e) => {
    const insideSearch = input.contains(e.target) || resultsEl.contains(e.target);
    if (!insideSearch) hideSearchResults();
  });
}

async function searchUsers(query) {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  try {
    const data = await apiFetch(`/api/search/users?q=${encodeURIComponent(query)}`, {
      method: "GET",
    });

    renderSearchResults(data.users || []);
  } catch (err) {
    resultsEl.style.display = "block";
    resultsEl.innerHTML = `<div class="search-empty">${escapeHtml(err.message || "Search failed")}</div>`;
  }
}

function renderSearchResults(users) {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  const filteredUsers = users.filter((user) => user.username !== currentUser?.username);

  if (!filteredUsers.length) {
    resultsEl.style.display = "block";
    resultsEl.innerHTML = `<div class="search-empty">No users found</div>`;
    return;
  }

  resultsEl.style.display = "block";
  resultsEl.innerHTML = filteredUsers.map((user) => {
    const avatarUrl = getUserAvatarUrl(user, getAssetUrl);

    return `
      <div class="search-result-item">
        <a class="search-result-left search-result-link" href="profile.html?u=${encodeURIComponent(user.username)}">
          <img class="avatar" src="${escapeAttr(avatarUrl)}" alt="User" />
          <div>
            <div class="search-result-name">${escapeHtml(user.display_name || user.username)}</div>
            <div class="search-result-handle">@${escapeHtml(user.username)}</div>
          </div>
        </a>
      </div>
    `;
  }).join("");
}

function hideSearchResults() {
  const resultsEl = document.getElementById("searchResults");
  if (!resultsEl) return;

  resultsEl.style.display = "none";
  resultsEl.innerHTML = "";
}

function renderSkeletonCards(count) {
  return Array.from({ length: count }, () => `
    <article class="skeleton-card">
      <div class="skeleton-line short"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line medium"></div>
    </article>
  `).join("");
}

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
  }
