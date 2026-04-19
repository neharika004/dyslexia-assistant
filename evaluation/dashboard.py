import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from api.database import DB_FULL_PATH, init_db
from ml.bandit import ACTION_SPACE

app = FastAPI(title="DysRead Evaluation Dashboard")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


def get_all_data():
    if not os.path.exists(DB_FULL_PATH):
        return [], []
    conn = sqlite3.connect(DB_FULL_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sessions  = [dict(r) for r in c.execute(
        "SELECT * FROM sessions ORDER BY timestamp").fetchall()]
    profiles  = [dict(r) for r in c.execute(
        "SELECT * FROM user_profiles").fetchall()]
    conn.close()
    return sessions, profiles


@app.get("/api/data")
def get_data():
    sessions, profiles = get_all_data()
    users = {}
    for s in sessions:
        uid = s["user_id"]
        if uid not in users:
            users[uid] = {"rewards": [], "speeds": [],
                          "actions": [], "timestamps": []}
        users[uid]["rewards"].append(round(s["reward"] or 0, 3))
        users[uid]["speeds"].append(round(s["reading_speed_wpm"] or 150, 1))
        users[uid]["actions"].append(s["action_id"])
        users[uid]["timestamps"].append(s["timestamp"][:10])

    action_usage = [0] * len(ACTION_SPACE)
    for s in sessions:
        if s["action_id"] is not None:
            action_usage[s["action_id"]] += 1

    return {
        "users": users,
        "profiles": profiles,
        "action_usage": action_usage,
        "action_labels": [f"{a['font'][:6]}+{a['letter_spacing']}"
                          for a in ACTION_SPACE],
        "total_sessions": len(sessions),
        "total_users": len(profiles),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>DysRead — Evaluation Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Segoe UI',sans-serif;background:#0a0a0f;color:#e0e0f0;min-height:100vh;}
  .topbar{background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:20px 32px;
    display:flex;align-items:center;justify-content:space-between;}
  .topbar h1{font-size:22px;color:#fff;font-weight:700;}
  .topbar span{font-size:13px;color:rgba(255,255,255,0.75);}
  .stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:24px 32px;}
  .stat{background:#13131f;border:1px solid rgba(255,255,255,0.08);border-radius:14px;
    padding:20px 24px;}
  .stat-num{font-size:32px;font-weight:700;color:#a5b4fc;}
  .stat-label{font-size:12px;color:#6b6b8a;margin-top:4px;}
  .charts{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:0 32px 24px;}
  .chart-card{background:#13131f;border:1px solid rgba(255,255,255,0.08);
    border-radius:14px;padding:20px 24px;}
  .chart-card.full{grid-column:1/-1;}
  .chart-title{font-size:13px;font-weight:600;color:#a5b4fc;margin-bottom:16px;
    text-transform:uppercase;letter-spacing:0.6px;}
  canvas{max-height:260px;}
  .table-section{padding:0 32px 32px;}
  table{width:100%;border-collapse:collapse;font-size:13px;}
  th{text-align:left;padding:10px 14px;color:#6b6b8a;
    border-bottom:1px solid rgba(255,255,255,0.06);font-weight:500;}
  td{padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.04);color:#c0c0d8;}
  tr:hover td{background:rgba(255,255,255,0.03);}
  .badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;
    font-weight:600;}
  .badge-good{background:rgba(34,197,94,0.15);color:#4ade80;}
  .badge-mid {background:rgba(251,191,36,0.15);color:#fbbf24;}
  .badge-low {background:rgba(239,68,68,0.15);color:#f87171;}
  .section-title{font-size:16px;font-weight:600;color:#e0e0f0;
    padding:0 32px 12px;margin-top:8px;}
  .loading{text-align:center;padding:60px;color:#4a4a6a;font-size:14px;}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <h1>📊 DysRead — Evaluation Dashboard</h1>
    <span>Adaptive Dyslexia-Aware Reading Assistant — Project Results</span>
  </div>
  <div style="text-align:right">
    <div style="font-size:13px;color:rgba(255,255,255,0.9)" id="lastUpdate">Loading...</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:2px;">
      VIT — Final Year Project 2025</div>
  </div>
</div>

<div class="stats-row">
  <div class="stat">
    <div class="stat-num" id="totalSessions">—</div>
    <div class="stat-label">Total sessions</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="totalUsers">—</div>
    <div class="stat-label">User profiles</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="avgReward">—</div>
    <div class="stat-label">Avg reward score</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="topConfig">—</div>
    <div class="stat-label">Most selected config</div>
  </div>
</div>

<div class="charts">
  <div class="chart-card full">
    <div class="chart-title">Bandit Learning Curve — Reward Over Sessions (all users)</div>
    <canvas id="learningChart"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title">Reading Speed Improvement Over Sessions</div>
    <canvas id="speedChart"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title">Action Selection Distribution (Bandit Choices)</div>
    <canvas id="actionChart"></canvas>
  </div>
  <div class="chart-card full">
    <div class="chart-title">Per-User Cumulative Reward (shows personalization)</div>
    <canvas id="userChart"></canvas>
  </div>
</div>

<div class="section-title">User Profile Summary</div>
<div class="table-section">
  <table>
    <thead>
      <tr>
        <th>User ID</th>
        <th>Sessions</th>
        <th>Avg Reward</th>
        <th>Performance</th>
        <th>Last Action ID</th>
      </tr>
    </thead>
    <tbody id="profileTable"></tbody>
  </table>
</div>

<script>
const COLORS = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b',
                '#ef4444','#ec4899','#84cc16'];

async function loadData() {
  const res  = await fetch('/api/data');
  const data = await res.json();

  document.getElementById('totalSessions').textContent = data.total_sessions;
  document.getElementById('totalUsers').textContent    = data.total_users;
  document.getElementById('lastUpdate').textContent    =
    'Updated: ' + new Date().toLocaleTimeString();

  const topIdx = data.action_usage.indexOf(Math.max(...data.action_usage));
  document.getElementById('topConfig').textContent =
    data.action_labels[topIdx] || '—';

  // Compute global avg reward
  let allRewards = [];
  Object.values(data.users).forEach(u => allRewards = allRewards.concat(u.rewards));
  const avgR = allRewards.length
    ? (allRewards.reduce((a,b)=>a+b,0)/allRewards.length).toFixed(3) : '—';
  document.getElementById('avgReward').textContent = avgR;

  buildLearningChart(data.users);
  buildSpeedChart(data.users);
  buildActionChart(data.action_usage, data.action_labels);
  buildUserChart(data.users);
  buildTable(data.profiles);
}

function movingAvg(arr, win=5) {
  return arr.map((_,i) => {
    const slice = arr.slice(Math.max(0,i-win+1), i+1);
    return parseFloat((slice.reduce((a,b)=>a+b,0)/slice.length).toFixed(3));
  });
}

function buildLearningChart(users) {
  const ctx = document.getElementById('learningChart').getContext('2d');
  const datasets = Object.entries(users).map(([uid, u], i) => ({
    label: uid.length > 16 ? uid.substring(0,16)+'…' : uid,
    data: movingAvg(u.rewards, 5),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: 'transparent',
    borderWidth: 2,
    pointRadius: 0,
    tension: 0.4,
  }));
  new Chart(ctx, {
    type: 'line',
    data: { labels: datasets[0]?.data.map((_,i)=>'S'+(i+1)) || [], datasets },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color:'#a0a0c0', font:{size:11} } } },
      scales: {
        x: { ticks:{color:'#5a5a7a'}, grid:{color:'rgba(255,255,255,0.04)'} },
        y: { ticks:{color:'#5a5a7a'}, grid:{color:'rgba(255,255,255,0.04)'},
             min:0, max:1, title:{display:true,text:'Reward',color:'#6b6b8a'} },
      },
    },
  });
}

function buildSpeedChart(users) {
  const ctx = document.getElementById('speedChart').getContext('2d');
  const datasets = Object.entries(users).map(([uid, u], i) => ({
    label: uid.length > 16 ? uid.substring(0,16)+'…' : uid,
    data: movingAvg(u.speeds, 5),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: 'transparent',
    borderWidth: 2, pointRadius: 0, tension: 0.4,
  }));
  new Chart(ctx, {
    type: 'line',
    data: { labels: datasets[0]?.data.map((_,i)=>'S'+(i+1)) || [], datasets },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color:'#a0a0c0', font:{size:11} } } },
      scales: {
        x: { ticks:{color:'#5a5a7a'}, grid:{color:'rgba(255,255,255,0.04)'} },
        y: { ticks:{color:'#5a5a7a'}, grid:{color:'rgba(255,255,255,0.04)'},
             title:{display:true,text:'WPM',color:'#6b6b8a'} },
      },
    },
  });
}

function buildActionChart(usage, labels) {
  const ctx = document.getElementById('actionChart').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Times selected',
        data: usage,
        backgroundColor: COLORS.map(c => c + '99'),
        borderColor: COLORS,
        borderWidth: 1,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display:false } },
      scales: {
        x: { ticks:{color:'#5a5a7a',font:{size:10}},
             grid:{color:'rgba(255,255,255,0.04)'} },
        y: { ticks:{color:'#5a5a7a'}, grid:{color:'rgba(255,255,255,0.04)'} },
      },
    },
  });
}

function buildUserChart(users) {
  const ctx = document.getElementById('userChart').getContext('2d');
  const datasets = Object.entries(users).map(([uid, u], i) => {
    let cum = 0;
    const cumRewards = u.rewards.map(r => parseFloat((cum += r, cum/
      (u.rewards.indexOf(r)+1)).toFixed(3)));
    return {
      label: uid.length > 16 ? uid.substring(0,16)+'…' : uid,
      data: cumRewards,
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: 'transparent',
      borderWidth: 2, pointRadius: 0, tension: 0.4,
    };
  });
  new Chart(ctx, {
    type: 'line',
    data: { labels: datasets[0]?.data.map((_,i)=>'S'+(i+1)) || [], datasets },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color:'#a0a0c0', font:{size:11} } } },
      scales: {
        x: { ticks:{color:'#5a5a7a'}, grid:{color:'rgba(255,255,255,0.04)'} },
        y: { ticks:{color:'#5a5a7a'}, grid:{color:'rgba(255,255,255,0.04)'},
             min:0, max:1,
             title:{display:true,text:'Cumulative Avg Reward',color:'#6b6b8a'} },
      },
    },
  });
}

function buildTable(profiles) {
  const tbody = document.getElementById('profileTable');
  tbody.innerHTML = profiles.map(p => {
    const r = parseFloat(p.avg_reward || 0);
    const badge = r >= 0.6
      ? '<span class="badge badge-good">Good</span>'
      : r >= 0.4
      ? '<span class="badge badge-mid">Medium</span>'
      : '<span class="badge badge-low">Low</span>';
    return `<tr>
      <td style="font-family:monospace;font-size:12px">${p.user_id}</td>
      <td>${p.session_count}</td>
      <td>${r.toFixed(3)}</td>
      <td>${badge}</td>
      <td>${p.last_action_id}</td>
    </tr>`;
  }).join('');
}

loadData();
setInterval(loadData, 10000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    init_db()
    uvicorn.run("dashboard:app", host="127.0.0.1", port=8001, reload=False)