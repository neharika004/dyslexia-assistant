import numpy as np
import json
import os


ACTION_SPACE = [
    {"font": "OpenDyslexic", "letter_spacing": "2px", "line_height": "2.0",
     "bg_color": "#FFFDF0", "word_spacing": "4px", "simplify": "high"},
    {"font": "OpenDyslexic", "letter_spacing": "2px", "line_height": "1.8",
     "bg_color": "#FFFFFF", "word_spacing": "2px", "simplify": "moderate"},
    {"font": "OpenDyslexic", "letter_spacing": "4px", "line_height": "2.2",
     "bg_color": "#E8F4F8", "word_spacing": "4px", "simplify": "high"},
    {"font": "Arial",        "letter_spacing": "2px", "line_height": "2.0",
     "bg_color": "#FFFDF0", "word_spacing": "4px", "simplify": "moderate"},
    {"font": "Arial",        "letter_spacing": "4px", "line_height": "2.2",
     "bg_color": "#E8F4F8", "word_spacing": "4px", "simplify": "high"},
    {"font": "Comic Sans MS","letter_spacing": "2px", "line_height": "2.0",
     "bg_color": "#FFFFFF", "word_spacing": "2px", "simplify": "moderate"},
    {"font": "Comic Sans MS","letter_spacing": "4px", "line_height": "1.8",
     "bg_color": "#FFFDF0", "word_spacing": "4px", "simplify": "none"},
    {"font": "Verdana",      "letter_spacing": "2px", "line_height": "2.0",
     "bg_color": "#E8F4F8", "word_spacing": "2px", "simplify": "moderate"},
    {"font": "Verdana",      "letter_spacing": "4px", "line_height": "2.2",
     "bg_color": "#FFFFFF", "word_spacing": "4px", "simplify": "high"},
    {"font": "Arial",        "letter_spacing": "0px", "line_height": "1.6",
     "bg_color": "#FFFFFF", "word_spacing": "0px", "simplify": "none"},
]

N_ACTIONS = len(ACTION_SPACE)
CONTEXT_DIM = 7


class LinUCBBandit:
    def __init__(self, n_actions: int = N_ACTIONS,
                 context_dim: int = CONTEXT_DIM, alpha: float = 1.2):
        self.n_actions = n_actions
        self.context_dim = context_dim
        self.alpha = alpha
        self.A = [np.eye(context_dim) for _ in range(n_actions)]
        self.b = [np.zeros(context_dim) for _ in range(n_actions)]
        self.action_counts = [0] * n_actions
        self.total_reward = 0.0
        self.n_updates = 0

    def select_action(self, context: np.ndarray) -> int:
        scores = []
        for i in range(self.n_actions):
            theta = np.linalg.solve(self.A[i], self.b[i])
            A_inv = np.linalg.inv(self.A[i])
            uncertainty = self.alpha * np.sqrt(context @ A_inv @ context)
            scores.append(float(theta @ context + uncertainty))
        return int(np.argmax(scores))

    def update(self, action: int, context: np.ndarray, reward: float):
        self.A[action] += np.outer(context, context)
        self.b[action] += reward * context
        self.action_counts[action] += 1
        self.total_reward += reward
        self.n_updates += 1

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        state = {
            "A": [a.tolist() for a in self.A],
            "b": [b.tolist() for b in self.b],
            "action_counts": self.action_counts,
            "total_reward": self.total_reward,
            "n_updates": self.n_updates,
            "alpha": self.alpha,
        }
        with open(os.path.join(path, "bandit.json"), "w") as f:
            json.dump(state, f)

    def load(self, path: str):
        fpath = os.path.join(path, "bandit.json")
        if not os.path.exists(fpath):
            return
        with open(fpath, "r") as f:
            state = json.load(f)
        self.A = [np.array(a) for a in state["A"]]
        self.b = [np.array(b) for b in state["b"]]
        self.action_counts = state["action_counts"]
        self.total_reward = state["total_reward"]
        self.n_updates = state["n_updates"]
        self.alpha = state.get("alpha", 1.2)


def build_context_vector(
    avg_difficulty: float,
    reading_speed_wpm: float,
    regression_count: int,
    session_duration_s: float,
    avg_feedback: float,
    session_number: int,
    paragraph_length: int,
) -> np.ndarray:
    return np.array([
        float(avg_difficulty),
        min(reading_speed_wpm / 300.0, 1.0),
        min(regression_count / 20.0, 1.0),
        min(session_duration_s / 300.0, 1.0),
        float(avg_feedback),
        min(session_number / 50.0, 1.0),
        min(paragraph_length / 500.0, 1.0),
    ], dtype=np.float64)


def compute_reward(
    explicit_feedback: float,
    speed_gain: float,
    regression_reduction: float,
) -> float:
    reward = (
        0.45 * max(0.0, min(explicit_feedback, 1.0)) +
        0.35 * max(0.0, min(speed_gain, 1.0)) +
        0.20 * max(0.0, min(regression_reduction, 1.0))
    )
    return round(reward, 4)