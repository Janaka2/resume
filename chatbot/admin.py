# simple in-memory session store for admin actions (used by app.py)
ADMIN_SESSIONS = {}  # token -> expiry epoch
ADMIN_SESSION_TTL = 60 * 60 * 4  # 4 hours
