console.log("login.js loadeddd");
redirectIfLoggedIn(); //if already logged ->go feed

const form = document.getElementById("loginForm");
const pw = document.getElementById("password");
const toggle = document.getElementById("togglePw");
const msg = document.getElementById("msg");

// //show/hide password mazelt
// toggle.addEventListener("click", () => {
//   if (pw.type === "password") {
//     pw.type = "text";
//     toggle.textContent = "Hide";
//   } else {
//     pw.type = "password";
//     toggle.textContent = "Show";
//   }
// });

//UI only submit (no backend yet)
form.addEventListener("submit", (e) => {
  e.preventDefault();

  setToken("TEST"); //fake token
  msg.style.color = "green";
  msg.textContent = "Logged in (test mode)";
  
  setTimeout(() => {
    window.location.href = "feed.html";
  }, 400);
});
