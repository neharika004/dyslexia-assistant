<div align="center">

# 📖 DysRead
### Adaptive Dyslexia-Aware Reading Assistant Using Online Learning

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension%20MV3-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white)](https://developer.chrome.com/docs/extensions/)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2-FF6B35?style=for-the-badge)](https://ollama.com)
[![spaCy](https://img.shields.io/badge/spaCy-3.7+-09A3D5?style=for-the-badge)](https://spacy.io)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> **A browser-based intelligent reading assistant that automatically detects cognitively difficult text, adapts fonts and spacing in real time, simplifies hard sentences using a local LLM, and learns which settings work best for each individual user — all privately, on your own machine.**

<br/>


</div>

---



## 📋 Table of Contents

- [What is DysRead?](#-what-is-dysread)
- [How It Works](#-how-it-works)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Running the Project](#-running-the-project)
- [Loading the Chrome Extension](#-loading-the-chrome-extension)
- [Using the System](#-using-the-system)
- [Evaluation Dashboard](#-evaluation-dashboard)
- [API Reference](#-api-reference)
- [ML Model Details](#-ml-model-details)
- [NLP Pipeline](#-nlp-pipeline)
- [Team Contributions](#-team-contributions)
- [Troubleshooting](#-troubleshooting)

---

## 🧠 What is DysRead?

Dyslexia affects approximately **15–20% of the global population**. Existing accessibility tools apply the same fixed font and spacing to every user, on every piece of text, forever. They don't ask whether the text is actually difficult. They don't learn what works for you.

**DysRead solves all three problems:**

| Problem | Our Solution |
|---|---|
| Static formatting for all users | LinUCB bandit learns your personal optimal config |
| No text difficulty awareness | 9-feature NLP pipeline scores every sentence |
| Hard sentences left unchanged | Llama 3.2 selectively simplifies only what's needed |

The result is a Chrome extension that **transforms any webpage** — Wikipedia, news, textbooks, anything — into a personalised dyslexia-friendly reading experience that gets better every time you use it.

---

## ⚙️ How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         CHROME EXTENSION                        │
│                                                                 │
│  User opens any webpage                                         │
│        ↓                                                        │
│  Readability.js extracts clean article text                     │
│  Scroll listener tracks: reading speed (WPM) + regressions     │
│        ↓  POST /analyze                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                        PYTHON BACKEND (FastAPI)                 │
│                                                                 │
│  NLP Pipeline                                                   │
│    → spaCy segments text into sentences                         │
│    → 9 features extracted per sentence:                         │
│       syllables, tree depth, crowding, WM load,                 │
│       TTR, word familiarity, sentence length...                 │
│    → Cognitive load score (0–1) per sentence                   │
│        ↓                                                        │
│  Context Vector (7D)                                            │
│    → [difficulty, speed, regressions, duration,                 │
│       feedback_history, session_num, para_length]               │
│        ↓                                                        │
│  LinUCB Bandit                                                  │
│    → Selects 1 of 10 reading configurations                     │
│    → Balances exploration vs exploitation (α = 1.2)             │
│        ↓                                                        │
│  Llama 3.2 (via Ollama) — sentences with difficulty > 0.55     │
│    → Rewrites in simpler language, same meaning                 │
│        ↓  returns config + simplified text                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                         CHROME EXTENSION                        │
│                                                                 │
│  Injects CSS → changes font, spacing, colour, line-height       │
│  Replaces hard sentences with simplified versions in DOM        │
│        ↓                                                        │
│  User reads adapted page                                        │
│  Rates comfort 1–5 in popup                                     │
│        ↓  POST /feedback                                        │
│  Reward = 0.45×feedback + 0.35×speed_gain + 0.20×less_rereads  │
│  LinUCB matrices updated → saved to disk                        │
│  Model remembers. Gets better next session.                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- **🔍 Intelligent Text Analysis** — NLP pipeline extracts 9 dyslexia-specific readability features per sentence, going far beyond traditional Flesch-Kincaid metrics
- **🤖 Personalised ML Adaptation** — LinUCB contextual bandit learns your optimal reading config over ~40–50 sessions, independently for each user
- **✏️ Selective LLM Simplification** — Llama 3.2 rewrites only sentences above difficulty threshold 0.55, preserving easy text unchanged
- **🎨 Live CSS Rendering** — Font, letter spacing, line height, word spacing, and background colour applied instantly to any webpage
- **📊 Evaluation Dashboard** — Real-time Chart.js dashboard showing learning curves, action distributions, and per-user reward improvement
- **🔒 100% Private** — Everything runs locally. No text or behaviour data ever leaves your machine
- **💰 Zero Cost** — No API keys, no subscriptions. Ollama + Llama 3.2 are completely free

---

## 🛠 Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 | Core language |
| FastAPI | 0.110+ | REST API framework |
| spaCy | 3.7+ | NLP: tokenisation, POS tagging, dependency parsing |
| pyphen | 0.14+ | Syllable counting |
| NLTK | 3.8+ | Stopwords, WordNet |
| NumPy | 1.26+ | LinUCB matrix operations |
| SQLite + SQLAlchemy | 3.x / 2.0+ | Session & profile storage |
| Ollama + Llama 3.2 | latest | Local LLM for text simplification |

### Frontend (Chrome Extension)
| Technology | Purpose |
|---|---|
| JavaScript ES2020 | Extension logic |
| Chrome Extensions Manifest V3 | Extension framework |
| Mozilla Readability.js | Article extraction |
| CSS Custom Properties | Dynamic typography injection |
| Chart.js 4.4 | Dashboard visualisations |

### Machine Learning
| Model | Details |
|---|---|
| LinUCB Contextual Bandit | Disjoint variant, 10 actions, 7D context, α=1.2, online updates |
| Llama 3.2 (3B) | Zero-shot instruction-tuned local LLM via Ollama |
| Weighted Linear Scorer | 9-feature weighted combination for difficulty score |

---

## 📁 Project Structure

```
dyslexia-assistant/
│
├── backend/                        # Python backend
│   ├── main.py                     # FastAPI app factory + startup
│   ├── config.py                   # Environment variables
│   ├── .env                        # Local config (not committed)
│   ├── common_words.txt            # 5000 most common English words
│   │
│   ├── nlp/
│   │   ├── features.py             # 9-feature extractor per sentence
│   │   └── segmenter.py            # Sentence splitting + scoring
│   │
│   ├── ml/
│   │   ├── bandit.py               # LinUCB implementation + action space
│   │   ├── simplifier.py           # Ollama/Llama 3.2 client
│   │   └── bandit_state/           # Per-user saved model state (JSON)
│   │
│   └── api/
│       ├── routes.py               # FastAPI endpoints
│       └── database.py             # SQLite schema + queries
│
├── extension/                      # Chrome Extension (Manifest V3)
│   ├── manifest.json               # Extension config + permissions
│   ├── popup.html                  # Extension popup UI
│   ├── src/
│   │   ├── background.js           # Service worker + API calls
│   │   ├── content.js              # Page injection + tracking
│   │   ├── popup.js                # Popup UI logic
│   │   └── readability.js          # Mozilla Readability (downloaded)
│   ├── styles/
│   │   ├── injected.css            # Floating button + toast styles
│   │   └── OpenDyslexic-Regular.otf  # Dyslexia font (downloaded)
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
├── evaluation/
│   ├── simulate.py                 # Generates synthetic session data
│   └── dashboard.py                # Evaluation results web app (port 8001)
│
├── docs/                           # Project report + diagrams
├── venv/                           # Python virtual environment
└── README.md
```

---

## 📦 Prerequisites

Before installing, make sure you have:

| Requirement | How to check | Install link |
|---|---|---|
| Python 3.12 | `python --version` | [python.org](https://python.org) |
| VS Code | — | [code.visualstudio.com](https://code.visualstudio.com) |
| Google Chrome | — | [chrome.google.com](https://google.com/chrome) |
| Ollama | `ollama --version` | [ollama.com/download](https://ollama.com/download) |
| Git (optional) | `git --version` | [git-scm.com](https://git-scm.com) |

> **Windows users:** All commands below are for **Command Prompt (CMD)** or the **VS Code integrated terminal**.

---

## 🚀 Installation

### Step 1 — Clone or download the project

```cmd
cd C:\Users\%USERNAME%\Desktop
git clone https://github.com/your-repo/dyslexia-assistant.git
cd dyslexia-assistant
```

Or if you don't have Git, just place the project folder on your Desktop.

### Step 2 — Create Python virtual environment

```cmd
cd C:\Users\%USERNAME%\Desktop\dyslexia-assistant
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal line.

### Step 3 — Install Python dependencies

```cmd
pip install fastapi uvicorn spacy pyphen nltk numpy scikit-learn sqlalchemy requests python-dotenv gtts pydantic
```

### Step 4 — Download spaCy language model

```cmd
python -m spacy download en_core_web_sm
```

### Step 5 — Download NLTK data

```cmd
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### Step 6 — Download the common words list

```cmd
python -c "
import urllib.request
url = 'https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt'
urllib.request.urlretrieve(url, 'backend/common_words.txt')
print('Downloaded common_words.txt')
"
```

### Step 7 — Download Readability.js for the extension

```cmd
python -c "
import urllib.request
url = 'https://raw.githubusercontent.com/mozilla/readability/main/Readability.js'
urllib.request.urlretrieve(url, 'extension/src/readability.js')
print('Downloaded Readability.js')
"
```

### Step 8 — Download OpenDyslexic font

Visit **https://opendyslexic.org/get-the-font** and download `OpenDyslexic-Regular.otf`.

Place it at: `extension/styles/OpenDyslexic-Regular.otf`

### Step 9 — Install and set up Ollama

1. Download from **https://ollama.com/download** and install
2. Open a new CMD window and run:
```cmd
ollama pull llama3.2
```
3. Ollama starts automatically on Windows. Verify at: `http://localhost:11434`

---

## ▶️ Running the Project

You need **two terminal windows** running simultaneously.

### Terminal 1 — Main Backend (port 8000)

```cmd
cd C:\Users\%USERNAME%\Desktop\dyslexia-assistant\backend
venv\Scripts\activate
python main.py
```

Expected output:
```
Database initialized.
Server running at http://127.0.0.1:8000
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Verify: open **http://127.0.0.1:8000/health** in your browser → should return `{"status":"ok"}`

### Terminal 2 — Evaluation Dashboard (port 8001)

```cmd
cd C:\Users\%USERNAME%\Desktop\dyslexia-assistant\backend
venv\Scripts\activate
python ..\evaluation\simulate.py    # Generate demo data first (run once)
python ..\evaluation\dashboard.py
```

Dashboard available at: **http://127.0.0.1:8001**

---

## 🧩 Loading the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the folder: `C:\Users\YourName\Desktop\dyslexia-assistant\extension`
5. The DysRead extension appears with a purple circle icon

> **After any code changes to the extension**, click the refresh icon on the DysRead card at `chrome://extensions` and hard-refresh the tab with `Ctrl + Shift + R`.

---

## 📖 Using the System

1. **Open any article** in Chrome — Wikipedia, BBC News, any text-heavy webpage
2. **Click the DysRead icon** in the Chrome toolbar
3. The popup shows:
   - 🟢 Server connected (green = backend running)
   - Text difficulty percentage
   - Active configuration (font, spacing, colours)
   - Reading speed and re-read count
4. **The page automatically transforms** within 1–2 seconds:
   - Font changes to OpenDyslexic or the bandit's selected font
   - Letter spacing and line height increase
   - Background tints to cream or blue
   - Hard sentences are rewritten in simpler language
5. **Rate your reading experience** using the emoji buttons (😣 to 😊)
6. **Click Submit Feedback** — the model updates immediately and remembers for next time

> The system improves over approximately **40–50 reading sessions** as the bandit converges to your personal optimal configuration.

---

## 📊 Evaluation Dashboard

Navigate to **http://127.0.0.1:8001** after starting the dashboard server.

The dashboard shows four real-time visualisations:

| Chart | What it shows |
|---|---|
| Learning Curve | Moving-average reward over sessions — should increase and stabilise |
| Reading Speed | WPM trend over sessions per user profile |
| Action Distribution | Which of the 10 configurations the bandit selects most |
| Cumulative Reward | Per-user average reward showing personalisation convergence |

To populate the dashboard with demo data:
```cmd
cd backend
python ..\evaluation\simulate.py
```

This simulates 4 user profiles × 60 sessions each and saves results to the database.

---

## 🔌 API Reference

Base URL: `http://127.0.0.1:8000`

Interactive docs: **http://127.0.0.1:8000/docs**

### `GET /health`
```json
{ "status": "ok", "message": "DysRead backend is running" }
```

### `POST /analyze`
```json
// Request
{
  "text": "Article text here...",
  "user_id": "user_abc123",
  "reading_speed_wpm": 150,
  "regression_count": 2,
  "session_duration_s": 60,
  "article_url": "https://example.com/article"
}

// Response
{
  "action_id": 0,
  "config": {
    "font": "OpenDyslexic",
    "letter_spacing": "2px",
    "line_height": "2.0",
    "bg_color": "#FFFDF0",
    "word_spacing": "4px",
    "simplify": "high"
  },
  "context_vector": [0.41, 0.50, 0.10, 0.20, 0.50, 0.02, 0.30],
  "sentences": [
    {
      "original": "The aforementioned complications...",
      "display": "The mentioned problems...",
      "difficulty": 0.71,
      "simplified": true
    }
  ],
  "avg_difficulty": 0.41,
  "session_number": 5
}
```

### `POST /feedback`
```json
// Request
{
  "user_id": "user_abc123",
  "action_id": 0,
  "context_vector": [0.41, 0.50, 0.10, 0.20, 0.50, 0.02, 0.30],
  "explicit_feedback": 4,
  "reading_speed_wpm": 180,
  "baseline_speed": 150,
  "regression_count": 1,
  "baseline_regressions": 5
}

// Response
{ "reward": 0.672, "message": "Model updated successfully" }
```

### `GET /stats/{user_id}`
```json
{
  "user_id": "user_abc123",
  "session_count": 12,
  "total_updates": 12,
  "avg_reward": 0.543,
  "action_counts": [4, 1, 2, 0, 1, 2, 0, 1, 1, 0],
  "most_used_config": { "font": "OpenDyslexic", ... }
}
```

---


## 📄 License

MIT License — free to use, modify, and distribute with attribution.

---

<div align="center">



</div>
