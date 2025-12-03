import { getAuth, signInWithPopup, GithubAuthProvider, signOut } 
    from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

const auth = getAuth();
const provider = new GithubAuthProvider();

document.getElementById("loginGitHub").onclick = () => {
    signInWithPopup(auth, provider)
        .then(() => {
            window.location.href = "dashboard.html";
        })
        .catch((error) => {
            alert("Login failed: " + error.message);
        });
};

if (document.getElementById("logoutBtn")) {
    document.getElementById("logoutBtn").onclick = () => {
        signOut(auth).then(() => {
            window.location.href = "index.html";
        });
    };
}
