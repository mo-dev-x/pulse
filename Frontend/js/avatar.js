export function getDefaultAvatarUrl() {
  return "assets/default-avatar.svg";
}

export function getUserAvatarUrl(user, getAssetUrl) {
  if (user?.profile_picture) {
    return getAssetUrl(user.profile_picture);
  }
  return getDefaultAvatarUrl();
}

export function getPostAvatarUrl(author, isAnonymous, getAssetUrl) {
  if (!isAnonymous && author?.profile_picture) {
    return getAssetUrl(author.profile_picture);
  }
  return getDefaultAvatarUrl();
}

export function getProfileHref(username) {
  return username ? `profile.html?u=${encodeURIComponent(username)}` : "profile.html";
}
