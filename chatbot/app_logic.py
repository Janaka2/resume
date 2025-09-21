from datetime import datetime, timezone
import time, requests

from config import (
    SYSTEM_PROMPT, GREETING_RE, UNKNOWN_LOG, PUSHOVER_TOKEN, PUSHOVER_USER,
    FACTS_PATH, QA_PATH, PROFILE_DOC, RESUME_SOURCE_URL, client
)
from utils import append_unknown_log, load_json, safe_read_text, fetch_resume_text_from_url
from retriever import retriever
from llm import call_llm

def answer_query(chat_history, user_input):
    question = (user_input or "").strip()
    if not question:
        return chat_history, "Please enter a question."

    if GREETING_RE.match(question):
        bot = (
            "Hi—I'm Janaka. I can answer quick screening topics like location & work authorization, notice period & start date, "
            "compensation, onsite/remote, tech stack, and recent project impact. Tap a quick question below or ask anything specific."
        )
        chat_history = chat_history + [(question, bot)]
        return chat_history, ""

    top = retriever.search(question, k=6)
    if not top:
        try:
            with open(UNKNOWN_LOG, "a", encoding="utf-8") as f:
                ts = datetime.now(timezone.utc).isoformat()
                f.write(f"{ts}\t{question}\n")
        except Exception:
            pass

        if PUSHOVER_TOKEN and PUSHOVER_USER:
            try:
                requests.post(
                    "https://api.pushover.net/1/messages.json",
                    data={
                        "token": PUSHOVER_TOKEN,
                        "user": PUSHOVER_USER,
                        "message": f"Unknown Q logged: {question}",
                    },
                    timeout=8,
                )
            except Exception:
                pass

        bot = (
            "I don't have that detail in my profile yet. "
            "If you’d like, use the Contact tab to leave your email/phone and I’ll follow up. "
            "You can also reach me at janaka2@gmail.com or +41 76 224 84 45."
        )
        chat_history = chat_history + [(question, bot)]
        return chat_history, ""

    answer = call_llm(SYSTEM_PROMPT, top, question)
    chat_history = chat_history + [(question, answer)]
    return chat_history, ""

def health() -> str:
    facts = load_json(FACTS_PATH, {})
    qa = load_json(QA_PATH, [])
    resume_present = bool(safe_read_text(PROFILE_DOC)) or bool(fetch_resume_text_from_url(RESUME_SOURCE_URL))
    import json
    return json.dumps(
        {
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "qa_count": len(qa),
            "facts_loaded": bool(facts),
            "resume_loaded": bool(resume_present),
            "openai_ready": bool(client is not None),
        },
        indent=2,
    )

def ask_quick(state_, q: str):
    # Reuse the same logic as typing+Send
    return answer_query(state_, q)
