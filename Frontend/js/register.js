const form = document.getElementById("registerForm");
const errorEl = document.getElementById("error");

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.style.display = "block";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.style.display = "none";

  const username = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  // ✅ validation ULaval
  if (!email.endsWith("@ulaval.ca")) {
    showError("Email must end with @ulaval.ca");
    return;
  }

  try {
    const data = await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });

    // ✅ souvent register renvoie aussi un token
    if (data.token) {
      saveToken(data.token);
      window.location.href = "feed.html";
    } else {
      // sinon -> aller login
      window.location.href = "login.html";
    }
  } catch (err) {
    showError(err.message);
  }
});
