import sys
import os
import json
import random
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.bandit import (LinUCBBandit, build_context_vector,
                       compute_reward, ACTION_SPACE, N_ACTIONS)
from api.database import init_db, DB_FULL_PATH

random.seed(42)

USER_PROFILES = [
    {"id": "user_sim_001", "preferred_action": 0, "base_speed": 120, "name": "Profile A"},
    {"id": "user_sim_002", "preferred_action": 2, "base_speed": 95,  "name": "Profile B"},
    {"id": "user_sim_003", "preferred_action": 5, "base_speed": 140, "name": "Profile C"},
    {"id": "user_sim_004", "preferred_action": 7, "base_speed": 80,  "name": "Profile D"},
]

N_SESSIONS = 60


def simulate_reward(action_id: int, preferred_action: int,
                    session_num: int) -> tuple[float, float, int]:
    closeness = 1.0 - min(abs(action_id - preferred_action) / N_ACTIONS, 1.0)
    learning_bonus = min(session_num / 40.0, 0.3)
    noise = random.gauss(0, 0.08)
    feedback = max(0.1, min(1.0, 0.3 + closeness * 0.6 + learning_bonus + noise))

    speed_gain = max(-0.2, min(0.5, closeness * 0.3 + learning_bonus * 0.5
                               + random.gauss(0, 0.05)))
    reg_red = max(-0.1, min(0.4, closeness * 0.25 + random.gauss(0, 0.04)))
    reward = compute_reward(feedback, speed_gain, reg_red)
    speed_wpm = 150 + speed_gain * 150 + random.gauss(0, 10)
    regressions = max(0, int(5 - reg_red * 10 + random.gauss(0, 1)))
    return reward, speed_wpm, regressions


def run_simulation():
    init_db()
    conn = sqlite3.connect(DB_FULL_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE user_id LIKE 'user_sim_%'")
    c.execute("DELETE FROM user_profiles WHERE user_id LIKE 'user_sim_%'")
    conn.commit()
    conn.close()

    all_results = {}

    for profile in USER_PROFILES:
        print(f"Simulating {profile['name']} ({N_SESSIONS} sessions)...")
        bandit = LinUCBBandit()
        rewards = []
        actions = []
        speeds  = []
        start_date = datetime.now() - timedelta(days=N_SESSIONS)

        for i in range(N_SESSIONS):
            difficulty   = random.uniform(0.3, 0.8)
            session_dur  = random.uniform(30, 300)
            para_len     = random.randint(100, 500)
            speed_wpm    = profile["base_speed"] + random.gauss(0, 15)
            regressions  = random.randint(0, 8)

            ctx = build_context_vector(
                avg_difficulty=difficulty,
                reading_speed_wpm=speed_wpm,
                regression_count=regressions,
                session_duration_s=session_dur,
                avg_feedback=sum(rewards[-5:]) / max(len(rewards[-5:]), 1)
                             if rewards else 0.5,
                session_number=i,
                paragraph_length=para_len,
            )

            action = bandit.select_action(ctx)
            reward, out_speed, out_reg = simulate_reward(
                action, profile["preferred_action"], i)

            bandit.update(action, ctx, reward)
            rewards.append(reward)
            actions.append(action)
            speeds.append(out_speed)

            conn = sqlite3.connect(DB_FULL_PATH)
            cur  = conn.cursor()
            ts   = (start_date + timedelta(days=i)).isoformat()
            cur.execute("""
                INSERT INTO sessions
                (user_id, timestamp, action_id, context_vector, reward,
                 reading_speed_wpm, regression_count, explicit_feedback, article_url)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (profile["id"], ts, action, json.dumps(ctx.tolist()),
                  reward, out_speed, out_reg,
                  (reward * 4) + 1, "https://simulation.test"))

            row = cur.execute("SELECT * FROM user_profiles WHERE user_id=?",
                              (profile["id"],)).fetchone()
            if row:
                n = row[1] + 1
                avg = (row[2] * row[1] + reward) / n
                cur.execute("""UPDATE user_profiles
                               SET session_count=?, avg_reward=?, last_action_id=?
                               WHERE user_id=?""",
                            (n, round(avg, 4), action, profile["id"]))
            else:
                cur.execute("""INSERT INTO user_profiles
                               (user_id, session_count, avg_reward, last_action_id)
                               VALUES (?,?,?,?)""",
                            (profile["id"], 1, reward, action))
            conn.commit()
            conn.close()

        all_results[profile["id"]] = {
            "name": profile["name"],
            "rewards": rewards,
            "actions": actions,
            "speeds":  speeds,
        }
        final_reward = sum(rewards[-10:]) / 10
        print(f"  Final avg reward (last 10): {final_reward:.3f}")

    print(f"\nSimulation complete. Data saved to database.")
    return all_results


if __name__ == "__main__":
    run_simulation()