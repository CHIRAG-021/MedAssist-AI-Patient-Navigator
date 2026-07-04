/* ============================================================
   MedAssist Patient Care Navigator — Frontend Logic
   ============================================================ */

"use strict";

// --- State ---
let currentLang = "en";  // "en" | "hi"
let isLoading   = false;
let chatHistory = [];
let medications = [];
let appointments = [];

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
  setActivePanel("chat");
  loadMedications();
  loadAppointments();
  loadTips("general");
  initTheme();
  autoResizeTextarea();
  setupEnterKey();
});

// ============================================================
//  NAVIGATION
// ============================================================
function setActivePanel(name) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item-btn").forEach(b => b.classList.remove("active"));

  const panel = document.getElementById(`panel-${name}`);
  const btn   = document.getElementById(`nav-${name}`);
  if (panel) panel.classList.add("active");
  if (btn)   btn.classList.add("active");

  const titles = {
    chat:        "💬 Symptom Chat",
    medications: "💊 Medication Tracker",
    appointments:"📅 Appointments",
    profile:     "🧍 Health Profile & BMI",
    tips:        "🌿 Preventive Health Tips",
    family:      "👨‍👩‍👧 Family Profiles",
  };
  document.getElementById("topbar-title").textContent = titles[name] || "MedAssist";

  // Close mobile sidebar
  document.getElementById("sidebar").classList.remove("open");
}

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
}

// ============================================================
//  THEME (Dark / Light)
// ============================================================
function initTheme() {
  const saved = localStorage.getItem("medassist-theme") || "light";
  applyTheme(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(current === "dark" ? "light" : "dark");
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("medassist-theme", theme);
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
}

// ============================================================
//  LANGUAGE TOGGLE
// ============================================================
function toggleLanguage() {
  currentLang = currentLang === "en" ? "hi" : "en";
  const btn = document.getElementById("lang-toggle-btn");
  if (btn) {
    btn.textContent = currentLang === "en" ? "🇮🇳 हिंदी" : "🇬🇧 English";
  }
  const placeholder = document.getElementById("chat-input");
  if (placeholder) {
    placeholder.placeholder = currentLang === "hi"
      ? "अपने लक्षण यहाँ लिखें... (Type in Hindi or English)"
      : "Describe your symptoms or ask a health question...";
  }
  showToast(currentLang === "hi" ? "हिंदी मोड चालू" : "Switched to English mode");
}

// ============================================================
//  CHAT
// ============================================================
function autoResizeTextarea() {
  const ta = document.getElementById("chat-input");
  if (!ta) return;
  ta.addEventListener("input", () => {
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
  });
}

function setupEnterKey() {
  const ta = document.getElementById("chat-input");
  if (!ta) return;
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

function sendQuickQuery(text) {
  const ta = document.getElementById("chat-input");
  if (ta) ta.value = text;
  sendMessage();
}

async function sendMessage() {
  if (isLoading) return;

  const input = document.getElementById("chat-input");
  const text  = input.value.trim();
  if (!text) return;

  // Clear welcome screen
  const welcome = document.getElementById("chat-welcome");
  if (welcome) welcome.style.display = "none";

  // Append user message
  appendMessage("user", text, new Date().toLocaleTimeString("en-IN", {hour:"2-digit", minute:"2-digit"}));
  input.value = "";
  input.style.height = "auto";

  // Show typing indicator
  showTyping();
  isLoading = true;
  setSendBtn(false);

  try {
    const res = await fetch("/api/chat", {
      method:  "POST",
      headers: {"Content-Type": "application/json"},
      body:    JSON.stringify({ message: text }),
    });
    const data = await res.json();
    hideTyping();

    if (data.error) {
      appendMessage("ai", `⚠️ ${data.error}`, data.timestamp, "ROUTINE", false);
    } else {
      if (data.is_urgent) showEmergencyBanner();
      appendMessage("ai", data.response, data.timestamp, data.urgency, true);
      chatHistory.push({ user: text, ai: data.response });
    }
  } catch (err) {
    hideTyping();
    appendMessage("ai",
      "⚠️ Could not connect to MedAssist server. Please check your connection and try again.\n\n⚕️ For medical emergencies, call 108 immediately.",
      new Date().toLocaleTimeString(), "ROUTINE", false
    );
  }

  isLoading = false;
  setSendBtn(true);
}

function appendMessage(role, text, time, urgency = "ROUTINE", showBadges = false) {
  const container = document.getElementById("chat-messages");
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const avatarIcon = role === "user" ? "👤" : "🏥";
  const formattedText = formatMarkdown(text);

  let badgesHtml = "";
  if (showBadges && role === "ai") {
    const urgencyClass = `urgency-${urgency}`;
    const urgencyIcon  = urgency === "URGENT" ? "🚨" : urgency === "MODERATE" ? "⚠️" : "✅";
    badgesHtml = `
      <div class="message-meta">
        <span>${time}</span>
        <span class="urgency-badge ${urgencyClass}">${urgencyIcon} ${urgency}</span>
        <span class="who-badge-msg">🌐 WHO/CDC</span>
      </div>`;
  } else {
    badgesHtml = `<div class="message-meta"><span>${time}</span></div>`;
  }

  row.innerHTML = `
    <div class="message-avatar">${avatarIcon}</div>
    <div>
      <div class="message-bubble">${formattedText}</div>
      ${badgesHtml}
    </div>`;

  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function formatMarkdown(text) {
  // Sanitize first — strip raw HTML
  let safe = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold **text**
  safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  // Italic *text*
  safe = safe.replace(/\*(.*?)\*/g, "<em>$1</em>");
  // Numbered lists
  safe = safe.replace(/^(\d+\.\s.+)$/gm, "<li>$1</li>").replace(/<\/li>\n<li>/g, "</li><li>").replace(/((<li>.*<\/li>)+)/g, "<ol>$1</ol>");
  // Bullet lists
  safe = safe.replace(/^[-•]\s(.+)$/gm, "<li>$1</li>").replace(/<\/li>\n<li>/g, "</li><li>").replace(/((?:<li>(?!<ol>).*?<\/li>)+)/g, "<ul>$1</ul>");
  // Newlines
  safe = safe.replace(/\n/g, "<br>");
  return safe;
}

function showTyping() {
  const container = document.getElementById("chat-messages");
  const row = document.createElement("div");
  row.className = "message-row ai";
  row.id = "typing-row";
  row.innerHTML = `
    <div class="message-avatar">🏥</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById("typing-row");
  if (el) el.remove();
}

function setSendBtn(enabled) {
  const btn = document.getElementById("send-btn");
  if (btn) btn.disabled = !enabled;
}

function showEmergencyBanner() {
  const container = document.getElementById("chat-messages");
  const banner = document.createElement("div");
  banner.className = "emergency-alert";
  banner.innerHTML = `🚨 <strong>EMERGENCY DETECTED — Call 108 Immediately!</strong> &nbsp; Ambulance: 108`;
  container.appendChild(banner);
  container.scrollTop = container.scrollHeight;
}

async function clearChat() {
  await fetch("/api/chat/clear", { method: "POST" });
  const container = document.getElementById("chat-messages");
  container.innerHTML = `
    <div class="chat-welcome" id="chat-welcome">
      <div class="welcome-icon">🏥</div>
      <div class="welcome-title">Welcome to MedAssist</div>
      <div class="welcome-sub">AI-powered health companion — type your symptoms or choose a quick question below.</div>
      <div class="quick-actions">
        <div class="quick-chip" onclick="sendQuickQuery('I have a fever and headache')">🌡️ Fever & Headache</div>
        <div class="quick-chip" onclick="sendQuickQuery('Chest pain and shortness of breath')">💔 Chest Pain</div>
        <div class="quick-chip" onclick="sendQuickQuery('Tips for managing diabetes')">🩸 Diabetes Tips</div>
        <div class="quick-chip" onclick="sendQuickQuery('Home remedies for cold and cough')">🤧 Cold & Cough</div>
        <div class="quick-chip" onclick="sendQuickQuery('I feel very stressed and anxious')">🧠 Mental Health</div>
        <div class="quick-chip" onclick="sendQuickQuery('मुझे पेट में दर्द है')">🇮🇳 Hindi Query</div>
      </div>
    </div>`;
  chatHistory = [];
  showToast("Chat cleared");
}

// ============================================================
//  MEDICATIONS
// ============================================================
async function loadMedications() {
  try {
    const res  = await fetch("/api/medications");
    const data = await res.json();
    medications = data.medications;
    renderMedications(medications, data.adherence);
  } catch (e) { console.warn("Could not load medications:", e); }
}

function renderMedications(meds, adherence) {
  updateAdherenceRing(adherence);
  const list = document.getElementById("med-list");
  if (!list) return;

  if (meds.length === 0) {
    list.innerHTML = `<div class="text-center py-4" style="color:var(--text-muted);font-size:13px">No medications added yet. Add your first medication below.</div>`;
    return;
  }

  list.innerHTML = meds.map(m => `
    <div class="med-item" id="med-${m.id}">
      <div class="med-icon">💊</div>
      <div class="med-info">
        <div class="med-name">${escHtml(m.name)} <small style="color:var(--text-muted)">${escHtml(m.dosage)}</small></div>
        <div class="med-detail">${escHtml(m.frequency)} · ${escHtml(m.time)}</div>
        <div class="med-progress">
          ${m.taken_doses}/${m.total_doses} doses taken
          <div style="height:3px;background:var(--border);border-radius:2px;margin-top:3px">
            <div style="height:3px;background:var(--primary);border-radius:2px;width:${Math.round((m.taken_doses/Math.max(m.total_doses,1))*100)}%"></div>
          </div>
        </div>
      </div>
      <button class="btn-take" onclick="takeMedication(${m.id})">✓ Take</button>
      <button onclick="deleteMedication(${m.id})" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:16px;padding:4px">🗑️</button>
    </div>`).join("");
}

function updateAdherenceRing(adherence) {
  const pct   = Math.min(parseFloat(adherence) || 0, 100);
  const fill  = document.getElementById("ring-fill");
  const label = document.getElementById("ring-percent");
  if (fill)  fill.style.strokeDashoffset = 283 - (283 * pct / 100);
  if (label) label.textContent = pct.toFixed(0) + "%";

  const el = document.getElementById("adherence-label");
  if (el) {
    el.textContent = pct >= 90 ? "Excellent adherence" : pct >= 70 ? "Good adherence" : "Needs improvement";
  }
}

async function takeMedication(id) {
  try {
    const res  = await fetch(`/api/medications/${id}/take`, { method: "POST" });
    const data = await res.json();
    medications = medications.map(m => m.id === id ? data.medication : m);
    renderMedications(medications, data.adherence);
    showToast("✅ Dose marked as taken!");
  } catch (e) { showToast("Failed to update medication"); }
}

async function deleteMedication(id) {
  try {
    const res  = await fetch(`/api/medications/${id}`, { method: "DELETE" });
    const data = await res.json();
    medications = medications.filter(m => m.id !== id);
    renderMedications(medications, data.adherence);
    showToast("Medication removed");
  } catch (e) { showToast("Failed to delete medication"); }
}

function openAddMedModal() {
  document.getElementById("med-modal").classList.add("open");
}

function closeAddMedModal() {
  document.getElementById("med-modal").classList.remove("open");
  document.getElementById("med-form").reset();
}

async function submitMedication(e) {
  e.preventDefault();
  const form = e.target;
  const data = {
    name:        form.med_name.value,
    dosage:      form.med_dosage.value,
    frequency:   form.med_frequency.value,
    time:        form.med_time.value,
    total_doses: parseInt(form.med_total.value) || 30,
    notes:       form.med_notes.value,
  };
  try {
    const res  = await fetch("/api/medications", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data),
    });
    const result = await res.json();
    medications.push(result.medication);
    renderMedications(medications, result.adherence);
    closeAddMedModal();
    showToast("💊 Medication added successfully!");
  } catch (e) { showToast("Failed to add medication"); }
}

// ============================================================
//  APPOINTMENTS
// ============================================================
async function loadAppointments() {
  try {
    const res  = await fetch("/api/appointments");
    const data = await res.json();
    appointments = data.appointments;
    renderAppointments(appointments);
  } catch (e) { console.warn("Could not load appointments:", e); }
}

function renderAppointments(appts) {
  const list = document.getElementById("appt-list");
  if (!list) return;
  if (appts.length === 0) {
    list.innerHTML = `<div class="text-center py-4" style="color:var(--text-muted);font-size:13px">No appointments scheduled. Add your first appointment below.</div>`;
    return;
  }
  list.innerHTML = appts.map(a => {
    const d = a.date ? new Date(a.date + "T00:00:00") : null;
    const month = d ? d.toLocaleString("en-IN", { month: "short" }) : "--";
    const day   = d ? d.getDate() : "--";
    return `
      <div class="appt-item ${a.is_upcoming ? "appt-upcoming" : "appt-past"}">
        <div class="appt-date-badge">
          <span class="appt-month">${month}</span>
          <span class="appt-day">${day}</span>
        </div>
        <div class="appt-info">
          <div class="appt-doctor">${escHtml(a.doctor)} <small style="color:var(--text-muted)">· ${escHtml(a.type)}</small></div>
          <div class="appt-meta">🕐 ${escHtml(a.time)} &nbsp;📍 ${escHtml(a.location)}</div>
          ${a.notes ? `<div class="appt-meta" style="margin-top:3px">📝 ${escHtml(a.notes)}</div>` : ""}
        </div>
        <button onclick="deleteAppointment(${a.id})" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:16px;align-self:flex-start">🗑️</button>
      </div>`;
  }).join("");
}

function openAddApptModal() {
  document.getElementById("appt-modal").classList.add("open");
}
function closeAddApptModal() {
  document.getElementById("appt-modal").classList.remove("open");
  document.getElementById("appt-form").reset();
}

async function submitAppointment(e) {
  e.preventDefault();
  const form = e.target;
  const data = {
    doctor:   form.appt_doctor.value,
    type:     form.appt_type.value,
    date:     form.appt_date.value,
    time:     form.appt_time.value,
    location: form.appt_location.value,
    notes:    form.appt_notes.value,
  };
  try {
    const res  = await fetch("/api/appointments", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data),
    });
    const result = await res.json();
    appointments.push(result.appointment);
    renderAppointments(appointments);
    closeAddApptModal();
    showToast("📅 Appointment added!");
  } catch (e) { showToast("Failed to add appointment"); }
}

async function deleteAppointment(id) {
  try {
    await fetch(`/api/appointments/${id}`, { method: "DELETE" });
    appointments = appointments.filter(a => a.id !== id);
    renderAppointments(appointments);
    showToast("Appointment removed");
  } catch (e) { showToast("Failed to delete appointment"); }
}

// ============================================================
//  BMI / HEALTH PROFILE
// ============================================================
async function calculateBMI(e) {
  e.preventDefault();
  const form = e.target;
  const data = {
    name:       form.profile_name.value,
    age:        form.profile_age.value,
    gender:     form.profile_gender.value,
    height:     parseFloat(form.profile_height.value),
    weight:     parseFloat(form.profile_weight.value),
    conditions: form.profile_conditions.value,
  };

  try {
    const res    = await fetch("/api/bmi", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data),
    });
    const result = await res.json();
    displayBMIResult(result);
  } catch (e) { showToast("Failed to calculate BMI"); }
}

function displayBMIResult(result) {
  const el = document.getElementById("bmi-result");
  if (!el) return;

  const colourMap = { success: "#16a34a", warning: "#d97706", danger: "#dc2626", info: "#0891b2", secondary: "#6b7280" };
  const colour = colourMap[result.color] || "#1a6eb0";

  el.style.display = "block";
  el.innerHTML = `
    <div class="bmi-value" style="color:${colour}">${result.bmi}</div>
    <div class="bmi-category" style="color:${colour}">${result.category}</div>
    <div class="bmi-advice">${result.advice}</div>
    <div style="margin-top:12px;font-size:11px;color:var(--text-muted)">
      📏 Based on ICMR guidelines for South Asian populations
    </div>`;

  showToast(`BMI: ${result.bmi} — ${result.category}`);
  loadFamilyProfiles();
}

async function loadFamilyProfiles() {
  try {
    const res  = await fetch("/api/family");
    const data = await res.json();
    renderFamilyProfiles(data.profiles);
  } catch (e) {}
}

function renderFamilyProfiles(profiles) {
  const list = document.getElementById("family-list");
  if (!list) return;
  if (profiles.length === 0) {
    list.innerHTML = `<div style="color:var(--text-muted);font-size:13px;text-align:center;padding:20px">No family profiles yet. Add one using the Health Profile form.</div>`;
    return;
  }
  list.innerHTML = profiles.map(p => `
    <div class="family-card" onclick="selectFamilyMember('${escHtml(p.name)}')">
      <div class="family-avatar">${(p.name || "?")[0].toUpperCase()}</div>
      <div>
        <div class="family-name">${escHtml(p.name)}</div>
        <div class="family-meta">${p.age} yrs · ${p.gender} · BMI ${p.bmi} (${p.bmi_category})</div>
        ${p.conditions ? `<div class="family-meta">⚕️ ${escHtml(p.conditions)}</div>` : ""}
      </div>
    </div>`).join("");
}

function selectFamilyMember(name) {
  document.querySelectorAll(".family-card").forEach(c => c.classList.remove("active"));
  event.currentTarget.classList.add("active");
  showToast(`Viewing profile: ${name}`);
}

// ============================================================
//  PREVENTIVE TIPS
// ============================================================
async function loadTips(category) {
  document.querySelectorAll(".tip-tab").forEach(t => t.classList.remove("active"));
  const activeTab = document.getElementById(`tip-tab-${category}`);
  if (activeTab) activeTab.classList.add("active");

  try {
    const res  = await fetch("/api/tips");
    const data = await res.json();
    const tips = data[category] || [];
    renderTips(tips);
  } catch (e) { console.warn("Could not load tips:", e); }
}

function renderTips(tips) {
  const list = document.getElementById("tips-list");
  if (!list) return;
  list.innerHTML = tips.map(t => `
    <div class="tip-card">
      <div class="tip-icon-box">${t.icon}</div>
      <div class="tip-text">${escHtml(t.tip)}</div>
    </div>`).join("");
}

// ============================================================
//  UTILITIES
// ============================================================
function showToast(msg, duration = 3000) {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = "toast-msg";
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

function escHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Close modals on backdrop click
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-bg")) {
    e.target.classList.remove("open");
  }
});
