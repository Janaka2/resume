import os, json, re, requests
from datetime import datetime, timezone
from typing import Any
from config import PUSHOVER_TOKEN, PUSHOVER_USER, LEADS_CSV, UNKNOWN_LOG

def push_pushover(text: str) -> None:
    if not (PUSHOVER_TOKEN and PUSHOVER_USER):
        return
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": PUSHOVER_TOKEN, "user": PUSHOVER_USER, "message": text},
            timeout=8,
        )
    except Exception as e:
        print("Pushover error:", e, flush=True)

def load_json(path: str, fallback: Any):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"load_json error {path}: {e}")
        return fallback

def save_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, "Saved."
    except Exception as e:
        return False, f"Save error: {e}"

def safe_read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def fetch_resume_text_from_url(url: str, timeout=10) -> str:
    if not url:
        return ""
    try:
        r = requests.get(url, timeout=timeout)
        if r.ok:
            text = r.text
            text = re.sub(r"<[^>]+>", " ", text)
            return re.sub(r"\s+", " ", text).strip()
        return ""
    except Exception as e:
        print("RESUME_SOURCE_URL fetch failed:", e)
        return ""

def append_unknown_log(q: str):
    try:
        ts = datetime.now(timezone.utc).isoformat()
        with open(UNKNOWN_LOG, "a", encoding="utf-8") as f:
            f.write(f"{ts}\t{q}\n")
    except Exception as e:
        print("append_unknown_log error:", e)

def append_lead(name: str, email: str, phone: str, company: str, message: str) -> str:
    try:
        header_needed = not os.path.exists(LEADS_CSV)
        with open(LEADS_CSV, "a", encoding="utf-8") as f:
            if header_needed:
                f.write("timestamp_utc,name,email,phone,company,message\n")
            ts = datetime.now(timezone.utc).isoformat()
            row = [
                ts,
                (name or "").replace(",", " "),
                (email or "").replace(",", " "),
                (phone or "").replace(",", " "),
                (company or "").replace(",", " "),
                (message or "").replace("\n", " ").replace(",", " "),
            ]
            f.write(",".join(row) + "\n")
        push_pushover(f"New lead: {name} | {email} | {phone} | {company}")
        return "Thank you—your details were received. I’ll follow up."
    except Exception as e:
        return f"Sorry, I couldn't save your details: {e}"
