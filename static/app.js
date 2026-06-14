let isRegisterMode = false;

function toggleAuthMode() {
    isRegisterMode = !isRegisterMode;
    
    document.getElementById("register-fields").classList.toggle("hidden", !isRegisterMode);
    document.getElementById("auth-title").textContent = isRegisterMode ? "Register" : "Login";
    document.getElementById("auth-submit-btn").textContent = isRegisterMode ? "Register" : "Login";
    document.getElementById("auth-toggle-text").textContent = isRegisterMode 
        ? "Already have an account? Login" 
        : "Don't have an account? Register";
    document.getElementById("auth-error").classList.add("hidden");
}

async function handleAuth() {
    const username = document.getElementById("auth-username").value.trim();
    const password = document.getElementById("auth-password").value.trim();
    const errorEl = document.getElementById("auth-error");
    
    if (!username || !password) {
        errorEl.textContent = "Please fill in all fields";
        errorEl.classList.remove("hidden");
        return;
    }
    
    let endpoint = "/login";
    let body = { username, password };
    
    if (isRegisterMode) {
        const email = document.getElementById("reg-email").value.trim();
        if (!email) {
            errorEl.textContent = "Please enter an email";
            errorEl.classList.remove("hidden");
            return;
        }
        endpoint = "/register";
        body = { username, email, password };
    }
    
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.error) {
            errorEl.textContent = data.error;
            errorEl.classList.remove("hidden");
            return;
        }
        
        // Success - hide modal and show app
        document.getElementById("auth-modal").classList.add("hidden");
        document.getElementById("user-bar").classList.remove("hidden");
        document.getElementById("welcome-text").textContent = `👋 Welcome, ${data.username}`;
        
    } catch (err) {
        errorEl.textContent = "Connection error. Please try again.";
        errorEl.classList.remove("hidden");
    }
}

async function logout() {
    await fetch("/logout", { method: "POST" });
    document.getElementById("user-bar").classList.add("hidden");
    document.getElementById("auth-modal").classList.remove("hidden");
    document.getElementById("auth-username").value = "";
    document.getElementById("auth-password").value = "";
}

async function checkLoginStatus() {
    const response = await fetch("/check-session");
    const data = await response.json();
    
    if (data.logged_in) {
        document.getElementById("auth-modal").classList.add("hidden");
        document.getElementById("user-bar").classList.remove("hidden");
        document.getElementById("welcome-text").textContent = `👋 Welcome, ${data.username}`;
    } else {
        document.getElementById("auth-modal").classList.remove("hidden");
        document.getElementById("user-bar").classList.add("hidden");
    }
}

// Run on page load
checkLoginStatus();

let selectedSeverity = "";
let lastResult = null;

function showPage(page) {
    document.getElementById("page-checker").classList.add("hidden");
    document.getElementById("page-history").classList.add("hidden");
    document.getElementById("nav-checker").classList.remove("active");
    document.getElementById("nav-history").classList.remove("active");

    document.getElementById(`page-${page}`).classList.remove("hidden");
    document.getElementById(`nav-${page}`).classList.add("active");
}

function setSeverity(level) {
    selectedSeverity = level;
    document.querySelectorAll(".severity-btn").forEach(btn => btn.classList.remove("selected"));
    document.getElementById(`sev-${level}`).classList.add("selected");
}

async function analyze() {
    const symptoms = document.getElementById("symptoms").value.trim();
    const duration = document.getElementById("duration").value.trim();

    if (!symptoms || !duration || !selectedSeverity) {
        alert("Please fill in all fields and select a severity level.");
        return;
    }

    const btn = document.getElementById("analyze-btn");
    btn.disabled = true;
    btn.textContent = "🔍 Analyzing...";

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symptoms, duration, severity: selectedSeverity })
        });

        const data = await response.json();

        const resultCard = document.getElementById("result-card");
        const casualDiv = document.getElementById("casual-message");
        const diagnosisDiv = document.getElementById("diagnosis");

        resultCard.classList.remove("hidden");

        if (data.casual) {
            casualDiv.classList.remove("hidden");
            diagnosisDiv.classList.add("hidden");
            document.getElementById("casual-text").textContent = data.message;
        } else if (data.error) {
            alert("Error: " + data.error);
        } else {
            casualDiv.classList.add("hidden");
            diagnosisDiv.classList.remove("hidden");

            document.getElementById("ai-response").textContent = data.ai_response;
            document.getElementById("score-text").textContent = `Severity Score: ${data.score}/100`;
            document.getElementById("assessment-text").textContent = data.assessment;

            // Score bar color
            const bar = document.getElementById("score-bar");
            bar.style.width = data.score + "%";
            if (data.score >= 70) bar.style.background = "#e74c3c";
            else if (data.score >= 40) bar.style.background = "#f39c12";
            else bar.style.background = "#27ae60";

            // Flags
            const flagsSection = document.getElementById("flags-section");
            flagsSection.innerHTML = "";
            if (data.flags && data.flags.length > 0) {
                data.flags.forEach(flag => {
                    const div = document.createElement("div");
                    div.className = "flag";
                    div.textContent = flag;
                    flagsSection.appendChild(div);
                });
            }

            lastResult = {
                symptoms, duration,
                severity: selectedSeverity,
                ai_response: data.ai_response,
                score: data.score,
                assessment: data.assessment,
                flags: data.flags
            };
        }

    } catch (err) {
        alert("Connection error. Please try again.");
    }

    btn.disabled = false;
    btn.textContent = "🔍 Analyze Symptoms";
}

async function exportPDF() {
    if (!lastResult) return;
    const response = await fetch("/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lastResult)
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "medicheck_report.pdf";
    a.click();
}

async function loadHistory() {
    const response = await fetch("/history");
    const data = await response.json();
    renderHistory(data);
}

async function searchHistory() {
    const keyword = document.getElementById("search-input").value.trim();
    if (!keyword) return loadHistory();
    const response = await fetch(`/search?keyword=${keyword}`);
    const data = await response.json();
    renderHistory(data);
}

function renderHistory(data) {
    const list = document.getElementById("history-list");
    list.innerHTML = "";

    if (data.length === 0) {
        list.innerHTML = "<p style='color:#aaa'>No sessions found.</p>";
        return;
    }

    data.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.innerHTML = `
            <button class="delete-btn" onclick="deleteSession(${item.id}, event)">🗑️</button>
            <h4>${item.symptoms}</h4>
            <p>${item.date} · Score: ${item.score}/100</p>
            <p>${item.assessment}</p>
        `;
        div.onclick = () => viewFullReport(item.id);
        list.appendChild(div);
    });
}

async function viewFullReport(id) {
    const response = await fetch(`/history/${id}`);
    const data = await response.json();

    document.getElementById("symptoms").value = data.symptoms;
    document.getElementById("duration").value = data.duration;
    setSeverity(data.severity);

    const resultCard = document.getElementById("result-card");
    const diagnosisDiv = document.getElementById("diagnosis");
    const casualDiv = document.getElementById("casual-message");

    resultCard.classList.remove("hidden");
    diagnosisDiv.classList.remove("hidden");
    casualDiv.classList.add("hidden");

    document.getElementById("ai-response").textContent = data.ai_response;
    document.getElementById("score-text").textContent = `Severity Score: ${data.score}/100`;
    document.getElementById("assessment-text").textContent = data.assessment;

    const bar = document.getElementById("score-bar");
    bar.style.width = data.score + "%";
    if (data.score >= 70) bar.style.background = "#e74c3c";
    else if (data.score >= 40) bar.style.background = "#f39c12";
    else bar.style.background = "#27ae60";

    lastResult = data;
    showPage("checker");
}

async function deleteSession(id, event) {
    event.stopPropagation();
    if (!confirm("Delete this session?")) return;
    await fetch(`/history/${id}/delete`, { method: "DELETE" });
    loadHistory();
}

async function deleteAll() {
    if (!confirm("Delete ALL history? This cannot be undone.")) return;
    await fetch("/history/delete-all", { method: "DELETE" });
    loadHistory();
}