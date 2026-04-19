const API_BASE = "http://127.0.0.1:8000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    enabled: true,
    userId: "user_" + Math.random().toString(36).substr(2, 9),
    baselineSpeed: 150,
    baselineRegressions: 5,
    sessionCount: 0,
    currentConfig: null,
    currentActionId: null,
    currentContextVector: null,
  });
  console.log("DysRead installed and ready.");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "ANALYZE_TEXT") {
    handleAnalyze(message.payload).then(sendResponse);
    return true;
  }
  if (message.type === "SEND_FEEDBACK") {
    handleFeedback(message.payload).then(sendResponse);
    return true;
  }
  if (message.type === "GET_HEALTH") {
    fetch(`${API_BASE}/health`)
      .then((r) => r.json())
      .then((data) => sendResponse({ ok: true, data }))
      .catch(() => sendResponse({ ok: false }));
    return true;
  }
});

async function handleAnalyze(payload) {
  try {
    const storage = await chrome.storage.local.get([
      "userId", "baselineSpeed", "baselineRegressions", "sessionCount"
    ]);

    const response = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: payload.text,
        user_id: storage.userId,
        reading_speed_wpm: payload.readingSpeedWpm || storage.baselineSpeed,
        regression_count: payload.regressionCount || 0,
        session_duration_s: payload.sessionDuration || 60,
        article_url: payload.url || "",
      }),
    });

    if (!response.ok) throw new Error("API error " + response.status);
    const data = await response.json();

    await chrome.storage.local.set({
      currentActionId: data.action_id,
      currentConfig: data.config,
      currentContextVector: data.context_vector,
      lastAnalysis: data,
    });

    return { ok: true, data };
  } catch (err) {
    console.error("Analyze error:", err);
    return { ok: false, error: err.message };
  }
}

async function handleFeedback(payload) {
  try {
    const storage = await chrome.storage.local.get([
      "userId", "currentActionId", "currentContextVector",
      "baselineSpeed", "baselineRegressions",
    ]);

    const response = await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: storage.userId,
        action_id: storage.currentActionId,
        context_vector: storage.currentContextVector,
        explicit_feedback: payload.rating,
        reading_speed_wpm: payload.readingSpeedWpm || storage.baselineSpeed,
        baseline_speed: storage.baselineSpeed,
        regression_count: payload.regressionCount || 0,
        baseline_regressions: storage.baselineRegressions,
        article_url: payload.url || "",
      }),
    });

    if (!response.ok) throw new Error("Feedback API error");
    const data = await response.json();

    const count = (await chrome.storage.local.get("sessionCount")).sessionCount || 0;
    await chrome.storage.local.set({ sessionCount: count + 1 });

    return { ok: true, data };
  } catch (err) {
    console.error("Feedback error:", err);
    return { ok: false, error: err.message };
  }
}