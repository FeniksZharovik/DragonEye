// -------------------------------
// Update Result UI
// -------------------------------
function updateResultUI(r) {
    document.getElementById('res-grade').innerText = r.grade || '-';
    document.getElementById('res-score').innerText = (r.score !== undefined) ? (r.score.toFixed(1) + "%") : '-';
    document.getElementById('res-length').innerText = r.length ?? '-';
    document.getElementById('res-diameter').innerText = r.diameter ?? '-';
    document.getElementById('res-est-weight').innerText = r.weight ?? '-';
    document.getElementById('res-actual-weight').innerText = r.actual_weight ?? '-';
    document.getElementById('res-ratio').innerText = r.ratio ?? '-';

    // Badge animation & color
    const badge = document.getElementById('grade-badge');
    badge.textContent = r.grade || '-';

    badge.classList.remove('A', 'B', 'C');
    if (r.grade) badge.classList.add(r.grade);

    badge.style.transform = "scale(1.15)";
    setTimeout(() => badge.style.transform = "scale(1)", 300);
}

// -------------------------------
// Append Log Entry
// -------------------------------
function appendLog(r) {
    const tbody = document.querySelector('#log-table tbody');
    const tr = document.createElement('tr');
    const time = new Date().toLocaleString();

    tr.innerHTML = `
        <td>${time}</td>
        <td>${r.grade || '-'}</td>
        <td>${r.score ? r.score.toFixed(1) : '-'}</td>
        <td>${r.length || '-'}</td>
        <td>${r.diameter || '-'}</td>
        <td>${r.weight || '-'}</td>
        <td>${r.actual_weight || '-'}</td>
    `;

    tbody.prepend(tr);
}

// -------------------------------
// Logout Button
// -------------------------------
document.getElementById('logoutBtn').addEventListener('click', () => {
    // Jika pakai Firebase Auth
    if (firebase.auth) {
        firebase.auth().signOut().then(() => {
            window.location.href = "login.html";
        });
    } else {
        // Fallback jika tidak pakai Firebase Auth
        window.location.href = "login.html";
    }
});
