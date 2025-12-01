# auth/session.py
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

sessions: Dict[str, dict] = {}

def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    sessions[session_id] = {
        "user_id": user_id,
        "created_at": now,
        "expires_at": now + timedelta(hours=1)
    }
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    session = sessions.get(session_id)
    if session:
        now = datetime.now(timezone.utc)
        if session["expires_at"] > now:
            return session
        # Expired session - delete it
        del sessions[session_id]
    return None

def delete_session(session_id: str):
    sessions.pop(session_id, None)