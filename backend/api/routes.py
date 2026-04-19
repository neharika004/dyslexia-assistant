from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.segmenter import segment_and_score, get_paragraph_difficulty
from ml.simplifier import simplify_text
from ml.bandit import (LinUCBBandit, ACTION_SPACE, build_context_vector,
                       compute_reward, N_ACTIONS, CONTEXT_DIM)
from api.database import init_db, save_session, get_user_session_count
from config import MODEL_SAVE_PATH, BASE_DIR

router = APIRouter()

MODEL_FULL_PATH = os.path.join(BASE_DIR, MODEL_SAVE_PATH)

_bandits: dict[str, LinUCBBandit] = {}


def get_bandit(user_id: str) -> LinUCBBandit:
    if user_id not in _bandits:
        b = LinUCBBandit()
        user_path = os.path.join(MODEL_FULL_PATH, user_id)
        b.load(user_path)
        _bandits[user_id] = b
    return _bandits[user_id]


class AnalyzeRequest(BaseModel):
    text: str
    user_id: str
    reading_speed_wpm: Optional[float] = 150.0
    regression_count: Optional[int] = 0
    session_duration_s: Optional[float] = 60.0
    article_url: Optional[str] = ""


class FeedbackRequest(BaseModel):
    user_id: str
    action_id: int
    context_vector: list[float]
    explicit_feedback: float
    reading_speed_wpm: float
    baseline_speed: float
    regression_count: int
    baseline_regressions: int
    article_url: Optional[str] = ""


@router.get("/health")
def health():
    return {"status": "ok", "message": "DysRead backend is running"}


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    sentences = segment_and_score(req.text)
    sentences = simplify_text(sentences)
    avg_difficulty = get_paragraph_difficulty(sentences)
    session_number = get_user_session_count(req.user_id)
    bandit = get_bandit(req.user_id)
    ctx = build_context_vector(
        avg_difficulty=avg_difficulty,
        reading_speed_wpm=req.reading_speed_wpm,
        regression_count=req.regression_count,
        session_duration_s=req.session_duration_s,
        avg_feedback=0.5,
        session_number=session_number,
        paragraph_length=len(req.text),
    )
    action_id = bandit.select_action(ctx)
    config = ACTION_SPACE[action_id]
    return {
        "action_id": action_id,
        "config": config,
        "context_vector": ctx.tolist(),
        "sentences": [
            {"original": s["sentence"],
             "display": s["display_text"],
             "difficulty": s["difficulty"],
             "simplified": s["was_simplified"]}
            for s in sentences
        ],
        "avg_difficulty": avg_difficulty,
        "session_number": session_number,
    }


@router.post("/feedback")
def feedback(req: FeedbackRequest):
    bandit = get_bandit(req.user_id)
    baseline_speed = req.baseline_speed if req.baseline_speed > 0 else 150.0
    speed_gain = (req.reading_speed_wpm - baseline_speed) / baseline_speed
    baseline_reg = req.baseline_regressions if req.baseline_regressions > 0 else 1
    reg_reduction = (baseline_reg - req.regression_count) / baseline_reg
    feedback_norm = (req.explicit_feedback - 1) / 4.0
    reward = compute_reward(feedback_norm, speed_gain, reg_reduction)
    ctx = np.array(req.context_vector, dtype=np.float64)
    bandit.update(req.action_id, ctx, reward)
    user_path = os.path.join(MODEL_FULL_PATH, req.user_id)
    bandit.save(user_path)
    save_session(
        user_id=req.user_id,
        action_id=req.action_id,
        context_vector=req.context_vector,
        reward=reward,
        reading_speed_wpm=req.reading_speed_wpm,
        regression_count=req.regression_count,
        explicit_feedback=req.explicit_feedback,
        article_url=req.article_url,
    )
    return {"reward": reward, "message": "Model updated successfully"}


@router.get("/stats/{user_id}")
def get_stats(user_id: str):
    bandit = get_bandit(user_id)
    session_count = get_user_session_count(user_id)
    return {
        "user_id": user_id,
        "session_count": session_count,
        "total_updates": bandit.n_updates,
        "avg_reward": round(bandit.total_reward / max(bandit.n_updates, 1), 4),
        "action_counts": bandit.action_counts,
        "most_used_config": ACTION_SPACE[
            bandit.action_counts.index(max(bandit.action_counts))
        ],
    }