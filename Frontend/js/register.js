import { apiFetch, saveToken, isLoggedIn } from "./auth.js";
console.log("Register page loadeddd");

const form = document.getElementById("registerForm");
const errorEl = document.getElementById("error");

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.style.display = "block";
}

function hideError() {
  errorEl.textContent = "";
  errorEl.style.display = "none";
}

// si déjà connectée -> feed
if (isLoggedIn()) window.location.href = "feed.html";

function isUlaval(email) {
  return email.toLowerCase().endsWith("@ulaval.ca");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  console.log("submit firedddd");
  hideError();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const username = document.getElementById("username").value.trim();
  // const display_name = document.getElementById("display_name").value.trim();

  const display_name = username;


  // validation frontend
  if (!isUlaval(email)) {
    showError("Email must end with @ulaval.ca");
    return;
  }

  try {
    const data = await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, username, display_name }),
    });

    const token = data.token || data.access_token;
    if (!token) throw new Error("No token returned by backend");

    saveToken(token);
    window.location.href = "feed.html";
  } catch (err) {
    showError(err.message || "Register failed");
  }
});
