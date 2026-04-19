import os
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", 8000))
MODEL_SAVE_PATH = os.getenv("MODEL_SAVE_PATH", "ml/bandit_state")
DB_PATH = os.getenv("DB_PATH", "evaluation/sessions.db")
COMMON_WORDS_PATH = os.getenv("COMMON_WORDS_PATH", "common_words.txt")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMON_WORDS_FULL_PATH = os.path.join(BASE_DIR, COMMON_WORDS_PATH)