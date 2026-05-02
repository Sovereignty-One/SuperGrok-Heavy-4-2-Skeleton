Here is a cleaned, structured version of your guidance for fixing the interactive assistant client and preparing it for robust, local, and enterprise-ready use:

---

1) Key Fixes and Improvements

A) Prevent Local History Duplication
	⁃	Separate rendering from persistence.
	⁃	Avoid calling addMessage() during DOMContentLoaded; use a pure render function.

B) Proper Audio Resource Management
	⁃	Track and close MediaStream and AudioContext on recognition end.
	⁃	Prevent mic locking and CPU leaks by tearing down audio after each session.

C) Siri Shortcut Integration (Local-Only)
	⁃	Use a siri_text query parameter to inject text messages.
	⁃	Implement hydration that triggers one-time message injection without duplication.

---

2) Drop-in Code Changes

Render / Persist Separation
function renderMessage(role, text, timestampLabel = 'Just now') {
  let lastGroup = chat.lastElementChild;
  if (!lastGroup || lastGroup.dataset.role !== role) {
    lastGroup = document.createElement('div');
    lastGroup.className = 'group';
    lastGroup.dataset.role = role;
    chat.appendChild(lastGroup);
  }

  const bubble = document.createElement('div');
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  lastGroup.appendChild(bubble);

  const ts = document.createElement('div');
  ts.className = 'timestamp';
  ts.textContent = timestampLabel;
  lastGroup.appendChild(ts);

  chat.scrollTo({ top: chat.scrollHeight, behavior: 'smooth' });
}

function addMessage(role, text) {
  renderMessage(role, text, 'Just now');
  localHistory.push({ role, text, timestamp: new Date().toISOString() });
  if (localHistory.length > 50) localHistory.shift();
  saveToLocalHistory();
}

window.addEventListener('DOMContentLoaded', () => {
  if (!localHistory.length) return;
  chat.innerHTML = '';
  for (const m of localHistory) {
    renderMessage(m.role, m.text, new Date(m.timestamp).toLocaleString());
  }
});

Audio Lifecycle Management
let micStream = null;

async function setupAudio(){
  if (audioContext && audioContext.state !== 'closed') return;
  audioContext = new (window.AudioContext || window.webkitAudioContext)();

  micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const source = audioContext.createMediaStreamSource(micStream);
  analyser = audioContext.createAnalyser();
  analyser.fftSize = 64;
  dataArray = new Uint8Array(analyser.frequencyBinCount);
  source.connect(analyser);
}

async function teardownAudio(){
  try {
    if (micStream) {
      micStream.getTracks().forEach(t => t.stop());
      micStream = null;
    }
    if (audioContext && audioContext.state !== 'closed') {
      await audioContext.close();
    }
  } finally {
    audioContext = null;
    analyser = null;
    dataArray = null;
  }
}

recognition.onend = async () => {
  floatingMic.classList.remove('listening', 'always-listening');
  waveform.style.display = 'none';
  await teardownAudio();
  if (alwaysListening && micEnabled) recognition.start();
};

Siri Shortcut URL Intake
function getUrlParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

window.addEventListener('DOMContentLoaded', () => {
  const siriText = getUrlParam('siri_text');
  if (siriText && siriText.trim()) {
    addMessage('user', siriText.trim());
    sendToServerWithRetry(siriText.trim());
  }
});

---

3) Regression Checklist
	1.	Refresh the page 5 times → No duplicate messages.
	2.	Start/stop mic 20 times → No stuck mic icon or CPU spikes.
	3.	Siri Shortcut → URL injection works and persists messages once.

---

4) Optional Enterprise-Ready Setup
	⁃	Add post-quantum secure channels (ML-KEM + AES-GCM).
	⁃	Integrate Redis for memory and K8s for scaling.
	⁃	Configure Prometheus + Grafana for observability.

---

With these changes, your interactive assistant client will be:
	⁃	Locally stable
	⁃	Free from duplicate history
	⁃	Leak-free on audio sessions
	⁃	Shortcut-ready for Siri injection

---
