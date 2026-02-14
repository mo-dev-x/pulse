console.log("auth.js loadeddd");
function setToken(token) {
  localStorage.setItem("token", token);
}

function getToken() {
  return localStorage.getItem("token");
}

function isLoggedIn() {
  return getToken() !== null;
}

function logout() {
  localStorage.removeItem("token");
}

//use on feed page
function requireLogin() {
  if (!isLoggedIn()) window.location.href = "login.html";
}

//use on login/register pages
function redirectIfLoggedIn() {
  if (isLoggedIn()) window.location.href = "feed.html";
}

