import os, json, re
from dotenv import load_dotenv
from openai import OpenAI

# ---------- ENV & GLOBALS ----------
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN", "").strip()
PUSHOVER_USER  = os.getenv("PUSHOVER_USER", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me").strip()
RESUME_SOURCE_URL = os.getenv("RESUME_SOURCE_URL", "").strip()
SYSTEM_PROMPT   = os.getenv("SYSTEM_PROMPT", "").strip()

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DATA_DIR = "data"
QA_PATH = os.path.join(DATA_DIR, "qa_seed.json")
FACTS_PATH = os.path.join(DATA_DIR, "profile_facts.json")
DOCS_DIR = os.path.join(DATA_DIR, "docs")
PROFILE_DOC = os.path.join(DOCS_DIR, "profile_resume.txt")
LEADS_CSV = os.path.join(DATA_DIR, "leads.csv")

GREETING_RE = re.compile(
    r"^\s*(hi|hello|hey|good\s*(morning|afternoon|evening)|hallo|servus|grüezi)\b",
    re.IGNORECASE,
)

UNKNOWN_LOG = os.path.join(DATA_DIR, "unknown_questions.log")

# Suggested quick-ask questions
_SUGGESTED_QUESTIONS_RAW = os.getenv("SUGGESTED_QUESTIONS", "").strip()
SUGGESTED_QUESTIONS = []
if _SUGGESTED_QUESTIONS_RAW:
    try:
        loaded = json.loads(_SUGGESTED_QUESTIONS_RAW)
        if isinstance(loaded, list) and all(isinstance(x, str) for x in loaded):
            SUGGESTED_QUESTIONS = loaded
        else:
            print("SUGGESTED_QUESTIONS env is not a list of strings; falling back to defaults.")
    except Exception as e:
        print("Could not parse SUGGESTED_QUESTIONS env as JSON; falling back to defaults:", e)

if not SUGGESTED_QUESTIONS:
    SUGGESTED_QUESTIONS = [
        "Where are you based right now? Are you open to hybrid in Zurich/Zug?",
        "What is your work authorization in Switzerland and the EU?",
        "What’s your notice period and earliest start date?"
    ]

CSS = """
/* Hide Gradio footer (API link + branding) */
footer, #footer, [data-testid="footer"], [data-testid="block-footer"] {
  display: none !important;
}
"""