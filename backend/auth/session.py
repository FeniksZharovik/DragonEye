# auth/session.py
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict

sessions: Dict[str, dict] = {}

def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    session = sessions.get(session_id)
    if session and session["expires_at"] > datetime.utcnow():
        return session
    # Expired or invalid
    if session_id in sessions:
        del sessions[session_id]
    return None

def delete_session(session_id: str):
    sessions.pop(session_id, None)