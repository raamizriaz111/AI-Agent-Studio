"""
Session and conversation history manager for Universal Client Chatbot Studio.
Handles session persistence, distinguishing between new and returning users.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

DATA_DIR = Path(__file__).parent.parent / "data"
SESSIONS_FILE = DATA_DIR / "sessions.json"

def init_session_storage():
    """Ensure data directory and sessions.json exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_FILE.exists():
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)

def load_sessions() -> Dict[str, Any]:
    init_session_storage()
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_sessions(sessions: Dict[str, Any]):
    init_session_storage()
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)

def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Retrieve an existing session or initialize a new one."""
    sessions = load_sessions()
    now = datetime.now().isoformat()
    
    if session_id in sessions:
        session = sessions[session_id]
        session["last_active"] = now
        session["is_returning"] = True
    else:
        session = {
            "session_id": session_id,
            "created_at": now,
            "last_active": now,
            "is_returning": False,
            "user_profile": {
                "name": None,
                "email": None,
                "is_lead_captured": False
            },
            "messages": []
        }
        sessions[session_id] = session

    save_sessions(sessions)
    return session

def reset_session(session_id: str) -> Dict[str, Any]:
    """Reset a session to simulate a brand-new visitor."""
    sessions = load_sessions()
    now = datetime.now().isoformat()
    session = {
        "session_id": session_id,
        "created_at": now,
        "last_active": now,
        "is_returning": False,
        "user_profile": {
            "name": None,
            "email": None,
            "is_lead_captured": False
        },
        "messages": []
    }
    sessions[session_id] = session
    save_sessions(sessions)
    return session

def update_session_profile(session_id: str, name: Optional[str] = None, email: Optional[str] = None):
    """Update known user profile details for a session."""
    sessions = load_sessions()
    if session_id not in sessions:
        get_or_create_session(session_id)
        sessions = load_sessions()

    session = sessions[session_id]
    profile = session.get("user_profile", {})
    if name:
        profile["name"] = name
    if email:
        profile["email"] = email
    if profile.get("email"):
        profile["is_lead_captured"] = True

    session["user_profile"] = profile
    session["last_active"] = datetime.now().isoformat()
    sessions[session_id] = session
    save_sessions(sessions)

def append_session_message(session_id: str, role: str, content: str):
    """Append a message to the persistent session history."""
    sessions = load_sessions()
    if session_id not in sessions:
        get_or_create_session(session_id)
        sessions = load_sessions()

    session = sessions[session_id]
    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    session["last_active"] = datetime.now().isoformat()
    sessions[session_id] = session
    save_sessions(sessions)

def get_session_history(session_id: str) -> List[Dict[str, str]]:
    """Return list of messages formatted for LLM consumption [{'role': ..., 'content': ...}]."""
    session = get_or_create_session(session_id)
    return [
        {"role": m["role"], "content": m["content"]}
        for m in session.get("messages", [])
    ]

def get_total_chats_count() -> int:
    """Return total number of chat sessions that have messages."""
    sessions = load_sessions()
    return sum(1 for s in sessions.values() if len(s.get("messages", [])) > 0)
