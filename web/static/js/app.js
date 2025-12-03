// ===============================
// FIREBASE DATABASE LISTENER
// ===============================

import { app } from "./firebase-config.js";
import {
    getDatabase,
    ref,
    query,
    limitToLast,
    onValue
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

const db = getDatabase(app);

// Baca 1 data terbaru dari "predictions"
const latestPredRef = query(ref(db, "predictions"), limitToLast(1));

onValue(latestPredRef, (snap) => {
    if (!snap.exists()) return;

    snap.forEach(item => {
        const data = item.val();
        console.log("DATA MASUK:", data);

        // Update Tabel
        addToTable(data);

        // Update Gauge kalau ada actual
        if (data.actual !== undefined) {
            setGauge(data.actual);
        }
    });
});

// ===============================
// GAUGE FUNCTIONS
// ===============================
function resizeGauge() {
    const box = document.getElementById("gaugeBox");
    const svg = document.getElementById("gaugeSVG");

    let size = box.clientWidth;
    svg.setAttribute("width", size);
    svg.setAttribute("height", size);

    const r = (size / 2) - 20;
    const bg = document.getElementById("gBg");
    const fill = document.getElementById("gFill");

    bg.setAttribute("cx", size / 2);
    bg.setAttribute("cy", size / 2);
    bg.setAttribute("r", r);

    fill.setAttribute("cx", size / 2);
    fill.setAttribute("cy", size / 2);
    fill.setAttribute("r", r);

    const c = 2 * Math.PI * r;
    fill.style.strokeDasharray = c;
    fill.style.strokeDashoffset = c;
}

window.addEventListener("load", resizeGauge);
window.addEventListener("resize", resizeGauge);

// ===============================
// UPDATE GAUGE
// ===============================
function setGauge(value) {
    const fill = document.getElementById("gFill");
    const val = document.getElementById("gValue");

    value = Math.max(0, Math.min(100, value));

    const r = fill.getAttribute("r");
    const c = 2 * Math.PI * r;

    const offset = c - (value / 100) * c;
    fill.style.strokeDashoffset = offset;
    val.textContent = value;
}

// ===============================
// TAMBAH KE TABEL
// ===============================
function addToTable(data) {
    const table = document.querySelector("#logTable tbody");
    const now = new Date().toLocaleTimeString();

    const row = document.createElement("tr");

    row.innerHTML = `
        <td>${now}</td>
        <td>${data.grade ?? "-"}</td>
        <td>${data.length ?? "-"}</td>
        <td>${data.diameter ?? "-"}</td>
        <td>${data.weight ?? "-"}</td>
        <td>${data.actual ?? "-"}</td>
    `;

    table.prepend(row);
}
