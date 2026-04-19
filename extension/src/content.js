(function () {
  if (window.__dysreadInjected) return;
  window.__dysreadInjected = true;

  // ── State ──────────────────────────────────────────────────────────────────
  let enabled = true;
  let startTime = Date.now();
  let wordCount = 0;
  let regressionCount = 0;
  let lastScrollY = window.scrollY;
  let scrollHistory = [];
  let readingSpeedWpm = 150;
  let analysisData = null;
  let originalContent = null;
  let overlayActive = false;

  // ── Scroll tracking ────────────────────────────────────────────────────────
  window.addEventListener("scroll", () => {
    const currentY = window.scrollY;
    const delta = currentY - lastScrollY;

    if (delta < -80) {
      regressionCount++;
    }

    scrollHistory.push({ y: currentY, time: Date.now() });
    if (scrollHistory.length > 30) scrollHistory.shift();

    if (scrollHistory.length >= 2) {
      const oldest = scrollHistory[0];
      const newest = scrollHistory[scrollHistory.length - 1];
      const timeDiff = (newest.time - oldest.time) / 1000 / 60;
      const pixelsMoved = Math.abs(newest.y - oldest.y);
      const wordsEstimate = pixelsMoved / 25;
      if (timeDiff > 0) {
        readingSpeedWpm = Math.round(wordsEstimate / timeDiff);
        readingSpeedWpm = Math.max(30, Math.min(readingSpeedWpm, 600));
      }
    }
    lastScrollY = currentY;
  });

  // ── Extract article text ───────────────────────────────────────────────────
  function extractText() {
    try {
      const docClone = document.cloneNode(true);
      const reader = new Readability(docClone);
      const article = reader.parse();
      if (article && article.textContent && article.textContent.length > 200) {
        wordCount = article.textContent.split(/\s+/).length;
        return article.textContent.substring(0, 6000);
      }
    } catch (e) {}

    const selectors = ["article", "main", ".post-content",
      ".article-body", ".entry-content", "#content", ".content"];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText.length > 200) {
        wordCount = el.innerText.split(/\s+/).length;
        return el.innerText.substring(0, 6000);
      }
    }
    return document.body.innerText.substring(0, 4000);
  }

  // ── Apply config to page ───────────────────────────────────────────────────
  function applyConfig(config) {
    const fontUrl = chrome.runtime.getURL("styles/OpenDyslexic-Regular.otf");

    let styleEl = document.getElementById("__dysread_style");
    if (!styleEl) {
      styleEl = document.createElement("style");
      styleEl.id = "__dysread_style";
      document.head.appendChild(styleEl);
    }

    styleEl.textContent = `
      @font-face {
        font-family: 'OpenDyslexic';
        src: url('${fontUrl}') format('opentype');
      }
      body, p, div, article, section, li, td, span, h1, h2, h3, h4, h5, h6 {
        font-family: '${config.font}', sans-serif !important;
        letter-spacing: ${config.letter_spacing} !important;
        line-height: ${config.line_height} !important;
        word-spacing: ${config.word_spacing} !important;
      }
      body {
        background-color: ${config.bg_color} !important;
      }
      p, li, td {
        max-width: 75ch !important;
      }
    `;
    overlayActive = true;
  }

  function removeConfig() {
    const styleEl = document.getElementById("__dysread_style");
    if (styleEl) styleEl.remove();
    overlayActive = false;
  }

  // ── Replace simplified sentences ──────────────────────────────────────────
  function applySimplifications(sentences) {
    const simplified = sentences.filter(
      (s) => s.simplified && s.display !== s.original
    );
    if (simplified.length === 0) return;

    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null
    );

    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue.trim().length > 20) {
        textNodes.push(node);
      }
    }

    for (const s of simplified) {
      const original = s.original.trim();
      for (const textNode of textNodes) {
        if (textNode.nodeValue.includes(original)) {
          textNode.nodeValue = textNode.nodeValue.replace(
            original,
            s.display
          );
          break;
        }
      }
    }
  }

  // ── Difficulty highlight overlay ──────────────────────────────────────────
  function showDifficultyHints(sentences) {
    const hard = sentences.filter((s) => s.difficulty >= 0.65);
    if (hard.length === 0) return;

    for (const s of hard) {
      const original = s.original.trim().substring(0, 60);
      const walker = document.createTreeWalker(
        document.body, NodeFilter.SHOW_TEXT, null
      );
      let node;
      while ((node = walker.nextNode())) {
        if (node.nodeValue.includes(original)) {
          try {
            const span = document.createElement("mark");
            span.style.cssText =
              "background: rgba(255,200,0,0.25) !important;" +
              "border-radius: 3px !important;" +
              "padding: 0 2px !important;";
            const range = document.createRange();
            const idx = node.nodeValue.indexOf(original);
            range.setStart(node, idx);
            range.setEnd(node, idx + original.length);
            range.surroundContents(span);
          } catch (e) {}
          break;
        }
      }
    }
  }

  // ── Main trigger ──────────────────────────────────────────────────────────
  function runAnalysis() {
    const text = extractText();
    if (!text || text.length < 100) return;

    const sessionDuration = (Date.now() - startTime) / 1000;

    chrome.runtime.sendMessage(
      {
        type: "ANALYZE_TEXT",
        payload: {
          text,
          readingSpeedWpm,
          regressionCount,
          sessionDuration,
          url: window.location.href,
        },
      },
      (response) => {
        if (!response || !response.ok) return;
        analysisData = response.data;
        applyConfig(response.data.config);
        applySimplifications(response.data.sentences);
        showDifficultyHints(response.data.sentences);

        chrome.runtime.sendMessage({
          type: "PAGE_ANALYZED",
          payload: {
            difficulty: response.data.avg_difficulty,
            config: response.data.config,
            sessionNumber: response.data.session_number,
          },
        });
      }
    );
  }

  // ── Listen for messages from popup ───────────────────────────────────────
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "TOGGLE_EXTENSION") {
      enabled = message.enabled;
      if (enabled) {
        runAnalysis();
      } else {
        removeConfig();
      }
      sendResponse({ ok: true });
    }

    if (message.type === "GET_STATS") {
      sendResponse({
        readingSpeedWpm,
        regressionCount,
        sessionDuration: Math.round((Date.now() - startTime) / 1000),
        wordCount,
        overlayActive,
      });
    }

    if (message.type === "RUN_NOW") {
      runAnalysis();
      sendResponse({ ok: true });
    }
    return true;
  });

  // ── Auto-run after page loads ─────────────────────────────────────────────
  chrome.storage.local.get(["enabled"], (result) => {
    enabled = result.enabled !== false;
    if (enabled) {
      setTimeout(runAnalysis, 1500);
    }
  });
})();