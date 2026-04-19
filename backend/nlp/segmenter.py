import spacy
from nlp.features import extract_features, compute_difficulty_score

nlp = spacy.load("en_core_web_sm")

DIFFICULTY_THRESHOLD = 0.45


def segment_and_score(text: str) -> list[dict]:
    doc = nlp(text)
    results = []
    for sent in doc.sents:
        sentence = sent.text.strip()
        if len(sentence) < 10:
            continue
        features = extract_features(sentence)
        score = compute_difficulty_score(features)
        results.append({
            "sentence": sentence,
            "features": features,
            "difficulty": score,
            "needs_adaptation": score >= DIFFICULTY_THRESHOLD,
        })
    return results


def get_paragraph_difficulty(sentences: list[dict]) -> float:
    if not sentences:
        return 0.0
    return round(sum(s["difficulty"] for s in sentences) / len(sentences), 4)