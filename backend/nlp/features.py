import spacy
import pyphen
import re
from nltk.corpus import stopwords
from config import COMMON_WORDS_FULL_PATH

nlp = spacy.load("en_core_web_sm")
dic = pyphen.Pyphen(lang="en_US")
stop_words = set(stopwords.words("english"))

with open(COMMON_WORDS_FULL_PATH, "r") as f:
    COMMON_WORDS = set(w.strip().lower() for w in f.readlines()[:5000])


def count_syllables(word: str) -> int:
    word = re.sub(r"[^a-zA-Z]", "", word)
    if not word:
        return 0
    hyphenated = dic.inserted(word.lower())
    return max(1, hyphenated.count("-") + 1)


def get_tree_depth(token) -> int:
    depth = 0
    while token.head != token:
        token = token.head
        depth += 1
    return depth


def extract_features(sentence: str) -> dict:
    doc = nlp(sentence)
    tokens = [t for t in doc if t.is_alpha]

    if not tokens:
        return _empty_features()

    # 1. Mean syllables per word
    syllable_counts = [count_syllables(t.text) for t in tokens]
    mean_syllables = sum(syllable_counts) / len(syllable_counts)

    # 2. Percentage of long words (more than 3 syllables)
    long_word_ratio = sum(1 for s in syllable_counts if s > 3) / len(syllable_counts)

    # 3. Syntactic tree depth (complexity of grammar)
    depths = [get_tree_depth(t) for t in doc]
    max_depth = max(depths) if depths else 0
    mean_depth = sum(depths) / len(depths) if depths else 0

    # 4. Type-token ratio (vocabulary diversity — high = more varied = harder)
    unique_words = set(t.text.lower() for t in tokens)
    ttr = len(unique_words) / len(tokens)

    # 5. Visual crowding score (avg word length — longer words crowd more)
    avg_word_length = sum(len(t.text) for t in tokens) / len(tokens)
    crowding = avg_word_length / 10.0  # normalize to roughly 0-1

    # 6. Working memory load (subordinate clauses, conjunctions)
    subordinators = {"because", "although", "while", "since", "unless",
                     "whereas", "whenever", "if", "that", "which", "who"}
    wm_load = sum(1 for t in doc if t.text.lower() in subordinators) / max(len(tokens), 1)

    # 7. Word familiarity (% of uncommon words)
    unfamiliar_ratio = sum(
        1 for t in tokens if t.text.lower() not in COMMON_WORDS
    ) / len(tokens)

    # 8. Sentence length normalized
    sent_length_norm = min(len(tokens) / 40.0, 1.0)

    features = {
        "mean_syllables": round(mean_syllables, 4),
        "long_word_ratio": round(long_word_ratio, 4),
        "max_depth": round(max_depth / 10.0, 4),
        "mean_depth": round(mean_depth / 5.0, 4),
        "ttr": round(ttr, 4),
        "crowding": round(crowding, 4),
        "wm_load": round(wm_load, 4),
        "unfamiliar_ratio": round(unfamiliar_ratio, 4),
        "sent_length_norm": round(sent_length_norm, 4),
    }
    return features


def _empty_features() -> dict:
    return {k: 0.0 for k in [
        "mean_syllables", "long_word_ratio", "max_depth", "mean_depth",
        "ttr", "crowding", "wm_load", "unfamiliar_ratio", "sent_length_norm"
    ]}


def compute_difficulty_score(features: dict) -> float:
    weights = {
        "mean_syllables": 0.15,
        "long_word_ratio": 0.20,
        "max_depth": 0.10,
        "mean_depth": 0.10,
        "ttr": 0.05,
        "crowding": 0.10,
        "wm_load": 0.10,
        "unfamiliar_ratio": 0.15,
        "sent_length_norm": 0.05,
    }
    score = 0.0
    for key, w in weights.items():
        val = features.get(key, 0.0)
        if key == "mean_syllables":
            val = min(val / 3.0, 1.0)
        score += w * val
    return round(min(score, 1.0), 4)