let selectedRating = 0;
let currentStats = {};
let isEnabled = true;

// ── On load ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadStorageData();
  checkServerHealth();
  fetchPageStats();
  setupEventListeners();
});

function loadStorageData() {
  chrome.storage.local.get(
    ["enabled", "sessionCount", "userId", "currentConfig",
     "lastAnalysis", "currentActionId"],
    (data) => {
      isEnabled = data.enabled !== false;
      updateToggleUI(isEnabled);

      const count = data.sessionCount || 0;
      document.getElementById("sessionCount").textContent = count;

      if (data.userId) {
        document.getElementById("userIdDisplay").textContent =
          "ID: " + data.userId.substring(0, 12);
      }

      if (data.lastAnalysis) {
        renderConfig(data.lastAnalysis.config);
        renderDifficulty(data.lastAnalysis.avg_difficulty);
        document.getElementById("pageDot").className = "status-dot";
        document.getElementById("pageStatus").textContent =
          "Adapted — difficulty " +
          Math.round(data.lastAnalysis.avg_difficulty * 100) + "%";
      }
    }
  );
}

function checkServerHealth() {
  chrome.runtime.sendMessage({ type: "GET_HEALTH" }, (response) => {
    const dot = document.getElementById("serverDot");
    const text = document.getElementById("serverStatus");
    if (response && response.ok) {
      dot.className = "status-dot";
      text.textContent = "Server connected";
    } else {
      dot.className = "status-dot red";
      text.textContent = "Server offline — start backend";
    }
  });
}

function fetchPageStats() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return;
    chrome.tabs.sendMessage(
      tabs[0].id,
      { type: "GET_STATS" },
      (response) => {
        if (chrome.runtime.lastError || !response) return;
        currentStats = response;
        document.getElementById("speedVal").textContent =
          response.readingSpeedWpm || "—";
        document.getElementById("regressVal").textContent =
          response.regressionCount || "0";
      }
    );
  });
}

function renderConfig(config) {
  if (!config) return;
  const body = document.getElementById("configBody");
  const items = [
    ["Font", config.font],
    ["Letter spacing", config.letter_spacing],
    ["Line height", config.line_height],
    ["Background", config.bg_color],
    ["Simplification", config.simplify],
  ];
  body.innerHTML = items.map(([k, v]) => `
    <div class="config-item">
      <span class="config-key">${k}</span>
      <span class="config-val">${v}</span>
    </div>
  `).join("");
}

function renderDifficulty(score) {
  const pct = Math.round(score * 100);
  document.getElementById("difficultyVal").textContent = pct + "%";
  document.getElementById("difficultyBar").style.width = pct + "%";
}

function updateToggleUI(on) {
  const toggle = document.getElementById("mainToggle");
  const label = document.getElementById("toggleLabel");
  if (on) {
    toggle.classList.add("on");
    label.textContent = "ON";
  } else {
    toggle.classList.remove("on");
    label.textContent = "OFF";
  }
}

function setupEventListeners() {
  // Main toggle
  document.getElementById("mainToggle").addEventListener("click", () => {
    isEnabled = !isEnabled;
    updateToggleUI(isEnabled);
    chrome.storage.local.set({ enabled: isEnabled });
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;
      chrome.tabs.sendMessage(tabs[0].id, {
        type: "TOGGLE_EXTENSION", enabled: isEnabled,
      });
    });
  });

  // Star ratings
  document.querySelectorAll(".star").forEach((star) => {
    star.addEventListener("click", () => {
      selectedRating = parseInt(star.dataset.val);
      document.querySelectorAll(".star").forEach((s, i) => {
        s.classList.toggle("active", i < selectedRating);
      });
    });
  });

  // Submit feedback
  document.getElementById("submitFeedback").addEventListener("click", () => {
    if (selectedRating === 0) {
      alert("Please select a rating first (the emoji faces).");
      return;
    }
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(
        tabs[0].id, { type: "GET_STATS" }, (stats) => {
          chrome.runtime.sendMessage({
            type: "SEND_FEEDBACK",
            payload: {
              rating: selectedRating,
              readingSpeedWpm: (stats && stats.readingSpeedWpm) || 150,
              regressionCount: (stats && stats.regressionCount) || 0,
              url: tabs[0].url,
            },
          }, (response) => {
            if (response && response.ok) {
              const btn = document.getElementById("submitFeedback");
              btn.textContent = "✓ Feedback saved!";
              btn.style.background = "#22c55e";
              setTimeout(() => {
                btn.textContent = "Submit Feedback";
                btn.style.background = "";
              }, 2000);
              loadStorageData();
            }
          });
        }
      );
    });
  });

  // Re-analyze
  document.getElementById("analyzeNow").addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;
      chrome.tabs.sendMessage(tabs[0].id, { type: "RUN_NOW" }, () => {
        document.getElementById("pageStatus").textContent = "Re-analyzing...";
        setTimeout(() => {
          loadStorageData();
          fetchPageStats();
        }, 3000);
      });
    });
  });
}