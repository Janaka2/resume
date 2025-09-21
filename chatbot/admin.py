import time, secrets
import gradio as gr
from config import ADMIN_PASSWORD

# simple in-memory session store for admin actions
ADMIN_SESSIONS = {}  # token -> expiry epoch
ADMIN_SESSION_TTL = 60 * 60 * 4  # 4 hours

def _prune_sessions():
    now = time.time()
    expired = [t for t, exp in ADMIN_SESSIONS.items() if exp < now]
    for t in expired:
        ADMIN_SESSIONS.pop(t, None)

def admin_login(pw: str):
    _prune_sessions()
    if not pw:
        return "", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), "Please enter the admin password."
    if pw.strip() != ADMIN_PASSWORD:
        return "", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), "Invalid password."
    token = secrets.token_urlsafe(24)
    ADMIN_SESSIONS[token] = time.time() + ADMIN_SESSION_TTL
    return token, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), "Logged in. Welcome!"

def _check_session(token: str) -> bool:
    _prune_sessions()
    if not token:
        return False
    exp = ADMIN_SESSIONS.get(token)
    if not exp:
        return False
    if exp < time.time():
        ADMIN_SESSIONS.pop(token, None)
        return False
    ADMIN_SESSIONS[token] = time.time() + ADMIN_SESSION_TTL
    return True
