import { apiFetch, saveToken, redirectIfLoggedIn } from "./auth.js";

// console.log("register.js loaded");

const form = document.getElementById("registerForm");
const errorEl = document.getElementById("error");
const submitBtn = form?.querySelector('button[type="submit"]');

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.style.display = "block";
}

function hideError() {
  errorEl.textContent = "";
  errorEl.style.display = "none";
}

redirectIfLoggedIn();

function isUlaval(email) {
  return email.toLowerCase().endsWith("@ulaval.ca");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const username = document.getElementById("username").value.trim();
  submitBtn.disabled = true;
  submitBtn.textContent = "Creating account...";

  const display_name = username;

  if (!isUlaval(email)) {
    showError("Email must end with @ulaval.ca");
    return;
  }

  if (password.length < 6) {
    showError("Password must be at least 6 characters");
    return;
  }

  if (!username) {
    showError("Username is required");
    return;
  }

  try {
    const data = await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, username, display_name }),
    });

    const token = data.token || data.access_token; //depend on email verification
    if (!token) {
      throw new Error("No token returned by backend");
    }

    saveToken(token, true);
    window.location.href = "feed.html";
  } catch (err) {
    showError(err.message || "Register failed");
  }finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Create Account";
  }
});

const pw = document.getElementById("password");
const toggle = document.getElementById("togglePassword");
toggle?.addEventListener("click", () => {
  if (pw.type === "password") {
    pw.type = "text";
    toggle.classList.add("active");
  } else {
    pw.type = "password";
    toggle.classList.remove("active");
  }
});