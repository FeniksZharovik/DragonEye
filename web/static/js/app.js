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

// Ambil data terbaru dari "predictions"
const latestPredRef = query(ref(db, "predictions"), limitToLast(1));

onValue(latestPredRef, (snap) => {
    if (!snap.exists()) return;

    snap.forEach(item => {
        const data = item.val();
        console.log("DATA MASUK:", data);

        // Update tabel
        addToTable(data);

        // Update Gauge pakai grade
        if (data.grade !== undefined) {
            setGauge(data.grade);
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
// UPDATE GAUGE (Grade Only)
// ===============================
function setGauge(grade) {
    const fill = document.getElementById("gFill");
    const val = document.getElementById("gValue");

    // Tampilkan huruf
    val.textContent = grade;

    // Warna gauge
    if (grade === "A") {
        fill.style.stroke = "#00c853";  // hijau
    } else if (grade === "B") {
        fill.style.stroke = "#ffab00";  // kuning
    } else if (grade === "C") {
        fill.style.stroke = "#d50000";  // merah
    } else {
        // fallback warna jika undefined
        fill.style.stroke = "#9e9e9e";
    }

    // Full circle (100%)
    fill.style.strokeDashoffset = 0;
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

// ===============================
// MQTT SEND CAPTURE TRIGGER
// ===============================

// Inisialisasi MQTT WebSocket client
const mqttClient = mqtt.connect("ws://10.204.14.89:8083/mqtt"); 
// Pastikan broker ESP32 atau Mosquitto aktif WS port 8083

mqttClient.on("connect", () => {
    console.log("✓ MQTT Web Connected");
});

// Event tombol capture
document.getElementById("captureBtn").addEventListener("click", () => {
    console.log("Mengirim trigger capture...");

    mqttClient.publish("iot/camera/capture", "capture");

    // Optional feedback UI
    const btn = document.getElementById("captureBtn");
    btn.textContent = "Processing...";
    btn.disabled = true;

    setTimeout(() => {
        btn.textContent = "Capture";
        btn.disabled = false;
    }, 2000);
});

