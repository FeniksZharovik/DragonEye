import { 
    getAuth, 
    signInWithPopup, 
    GithubAuthProvider, 
    signOut, 
    onAuthStateChanged 
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

import { app } from "./firebase-config.js";

const auth = getAuth(app);
const provider = new GithubAuthProvider();

/* LOGIN */
const loginBtn = document.getElementById("loginGitHub");

if (loginBtn) {
    loginBtn.addEventListener("click", () => {
        loginBtn.disabled = true;
        loginBtn.innerText = "Signing in...";

        signInWithPopup(auth, provider)
            .then(() => window.location.href = "dashboard.html")
            .catch((err) => {
                alert("Login failed: " + err.message);
                loginBtn.disabled = false;
                loginBtn.innerText = "Login with GitHub";
            });
    });
}

/* LOGOUT */
const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
        signOut(auth)
            .then(() => window.location.href = "index.html")
            .catch(err => alert("Logout failed: " + err.message));
    });
}

/* AUTO REDIRECT */
onAuthStateChanged(auth, (user) => {
    const path = window.location.pathname;

    if (user && path.includes("index.html")) {
        window.location.href = "dashboard.html";
    }

    if (!user && path.includes("dashboard.html")) {
        window.location.href = "index.html";
    }
});
