// ===============================
// FIREBASE CONFIG (MODULAR V10)
// ===============================

import { initializeApp } 
    from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";

import { getAnalytics, isSupported } 
    from "https://www.gstatic.com/firebasejs/10.7.1/firebase-analytics.js";

// --- Firebase Credentials ---
export const firebaseConfig = {
    apiKey: "AIzaSyCl-N1WrpxkypbmjKuOpMzjHnPO14XcnL4",
    authDomain: "sortir-buah-naga.firebaseapp.com",
    databaseURL: "https://sortir-buah-naga-default-rtdb.firebaseio.com",
    projectId: "sortir-buah-naga",
    storageBucket: "sortir-buah-naga.firebasestorage.app",
    messagingSenderId: "90569366366",
    appId: "1:90569366366:web:9bb7a9823b1de84c1acdcf",
    measurementId: "G-LT4ZHZBDZS"
};

// --- Init Firebase ---
export const app = initializeApp(firebaseConfig);

// --- Safe Analytics (Tidak crash di localhost) ---
isSupported().then((ok) => {
    if (ok) {
        getAnalytics(app);
    } else {
        console.warn("Analytics tidak didukung di environment ini.");
    }
});
