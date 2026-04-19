import requests
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


def simplify_sentence(sentence: str) -> str:
    prompt = (
        "You are a reading assistant helping someone with dyslexia. "
        "Rewrite the following sentence using shorter words and simpler grammar. "
        "Keep the exact same meaning. Do not add any explanation. "
        "Only output the rewritten sentence and nothing else.\n\n"
        f"Original: {sentence}\n"
        "Simplified:"
    )
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=30,
        )
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            result = re.sub(r"^(Simplified:|Here is|Here's)[\s:]*", "", result,
                            flags=re.IGNORECASE).strip()
            return result if result else sentence
    except Exception:
        pass
    return sentence


def simplify_text(sentences: list[dict]) -> list[dict]:
    output = []
    for item in sentences:
        if item.get("needs_adaptation") and item.get("difficulty", 0) >= 0.5:
            simplified = simplify_sentence(item["sentence"])
            output.append({**item, "display_text": simplified, "was_simplified": True})
        else:
            output.append({**item, "display_text": item["sentence"],
                           "was_simplified": False})
    return output