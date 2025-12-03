// camera.js - simple capture + POST to backend /predict
const API_URL = window.API_URL || "http://127.0.0.1:5000"; // change if your backend runs elsewhere

const video = document.getElementById('camera');
const captureBtn = document.getElementById('captureBtn');
const statusEl = document.getElementById('capture-status');

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 1280 }, audio: false });
    video.srcObject = stream;
  } catch (err) {
    console.error("Camera error:", err);
    statusEl.innerText = "Camera access denied";
  }
}

startCamera();

captureBtn.addEventListener('click', async () => {
  statusEl.innerText = "Capturing...";
  // draw to canvas
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth || 1280;
  canvas.height = video.videoHeight || 1280;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // compress
  canvas.toBlob(async (blob) => {
    try {
      statusEl.innerText = "Uploading...";
      const form = new FormData();
      form.append('file', blob, 'capture.jpg');

      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        body: form
      });

      const j = await res.json();

      if (res.ok && j.result) {
        const r = j.result;
        // update UI
        updateResultUI(r);
        appendLog(r);
        statusEl.innerText = "OK";
      } else {
        console.error("Predict error:", j);
        statusEl.innerText = "Pipeline error";
        alert("Error: " + (j.error || "Unknown"));
      }
    } catch (err) {
      console.error(err);
      statusEl.innerText = "Failed";
      alert("Failed to send image: " + err.message);
    }
  }, 'image/jpeg', 0.92);
});
