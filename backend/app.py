"""
Universal Chatbot Studio & Agent Desk API Server.
Supports multi-industry presets, live preview configuration, real-time chat, lead capture & CSV export.
"""

import os
import io
import csv
import json
import socket
from pathlib import Path
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from backend.presets import PRESETS
from backend.llm_client import ChatClient
from backend.lead_manager import (
    extract_lead_from_message,
    save_lead,
    get_all_leads,
    clear_all_leads,
    init_lead_storage
)
from backend.session_manager import (
    get_or_create_session,
    reset_session,
    update_session_profile,
    append_session_message,
    get_session_history,
    get_total_chats_count,
    init_session_storage
)

# Initialize storage and LLM client
init_lead_storage()
init_session_storage()
chat_client = ChatClient()

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
CONFIG_FILE = BASE_DIR / "data" / "active_config.json"

def load_active_config() -> dict:
    """Load active configuration or initialize with Dental Clinic preset."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return PRESETS["dental"]

def save_active_config(cfg: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

active_config = load_active_config()

async def home(request):
    """Serve the Agent Desk Prototype interface."""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(index_path)

async def presets_endpoint(request):
    """Return all pre-built client presets."""
    return JSONResponse(PRESETS)

async def config_endpoint(request):
    """Get or update active chatbot configuration."""
    global active_config
    if request.method == "GET":
        active_config = load_active_config()
        return JSONResponse(active_config)
    elif request.method == "POST":
        try:
            data = await request.json()
            active_config = load_active_config()
            active_config.update(data)
            save_active_config(active_config)
            return JSONResponse({"status": "success", "config": active_config})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=400)

async def session_endpoint(request):
    """Get or initialize visitor session."""
    session_id = request.query_params.get("sessionId", "guest-session")
    session = get_or_create_session(session_id)
    return JSONResponse({
        "sessionId": session["session_id"],
        "userProfile": session["user_profile"],
        "history": session.get("messages", []),
        "isReturning": session.get("is_returning", False)
    })

async def transcript_endpoint(request):
    """Return full message transcript of a specific session for lead auditing."""
    session_id = request.query_params.get("sessionId")
    if not session_id:
        return JSONResponse({"error": "Missing sessionId parameter"}, status_code=400)
    session = get_or_create_session(session_id)
    return JSONResponse({
        "sessionId": session_id,
        "userProfile": session.get("user_profile", {}),
        "messages": session.get("messages", [])
    })

async def reset_session_endpoint(request):
    """Reset session history to simulate a brand-new visitor."""
    try:
        body = await request.json()
        session_id = body.get("sessionId", "guest-session")
    except Exception:
        session_id = "guest-session"
    
    reset = reset_session(session_id)
    return JSONResponse({"status": "reset", "session": reset})

async def chat_endpoint(request):
    """Handle chat messages, dynamic persona responses & silent lead detection."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    session_id = body.get("sessionId", "guest-session")
    user_message = body.get("message", "").strip()
    override_config = body.get("config") or active_config

    if not user_message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    # 1. Retrieve persistent session & profile
    session = get_or_create_session(session_id)
    profile = session.get("user_profile", {})

    # 2. Extract lead details
    extracted = extract_lead_from_message(user_message)
    saved_lead = None

    if extracted["name"]:
        profile["name"] = extracted["name"]
        update_session_profile(session_id, name=extracted["name"])

    if extracted["email"]:
        profile["email"] = extracted["email"]
        update_session_profile(session_id, email=extracted["email"])
        saved_lead = save_lead(
            session_id=session_id,
            name=profile.get("name"),
            email=extracted["email"],
            interest=user_message[:120],
            notes=f"Inquiry: '{user_message}'",
            business_name=override_config.get("businessName")
        )
        print(f"[Lead Manager] Captured Lead for {override_config.get('businessName')}: {saved_lead}")

    # 3. Persist user message to history
    append_session_message(session_id, "user", user_message)
    conversation_history = get_session_history(session_id)

    # 4. Generate grounded 1-2 sentence response using custom persona
    reply = chat_client.generate_response(
        conversation_history=conversation_history,
        user_profile=profile,
        config=override_config
    )

    # 5. Persist assistant reply to history
    append_session_message(session_id, "assistant", reply)

    # Return reply along with lead info and updated stats
    return JSONResponse({
        "reply": reply,
        "leadCaptured": saved_lead,
        "userProfile": profile,
        "chatsCount": get_total_chats_count(),
        "leadsCount": len(get_all_leads()),
        "isMockMode": chat_client.client is None
    })

async def get_leads_endpoint(request):
    """API endpoint to view all captured leads and metrics."""
    leads = get_all_leads()
    chats_count = get_total_chats_count()
    return JSONResponse({
        "total": len(leads),
        "leads": leads,
        "chatsCount": chats_count,
        "leadsCount": len(leads)
    })

async def export_leads_csv(request):
    """Export captured leads to CSV format for download."""
    leads = get_all_leads()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Lead ID", "Business", "Name", "Email", "Interest", "Captured At"])
    for l in leads:
        writer.writerow([
            l.get("id", ""),
            l.get("business_name", ""),
            l.get("name", ""),
            l.get("email", ""),
            l.get("interest", ""),
            l.get("created_at", "")
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="captured_leads.csv"'}
    )

async def clear_leads_endpoint(request):
    """Clear captured leads."""
    clear_all_leads()
    return JSONResponse({"status": "cleared", "total": 0, "leads": []})

def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def find_available_port(preferred: int = 8003) -> int:
    if is_port_available(preferred):
        return preferred
    for port in range(preferred + 1, preferred + 50):
        if is_port_available(port):
            return port
    return preferred

# Starlette Middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# Starlette Routes
routes = [
    Route("/", home),
    Route("/api/presets", presets_endpoint, methods=["GET"]),
    Route("/api/config", config_endpoint, methods=["GET", "POST"]),
    Route("/api/session", session_endpoint, methods=["GET"]),
    Route("/api/session/transcript", transcript_endpoint, methods=["GET"]),
    Route("/api/session/reset", reset_session_endpoint, methods=["POST"]),
    Route("/api/chat", chat_endpoint, methods=["POST"]),
    Route("/api/leads", get_leads_endpoint, methods=["GET"]),
    Route("/api/leads/export", export_leads_csv, methods=["GET"]),
    Route("/api/leads/clear", clear_leads_endpoint, methods=["POST"]),
    Mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static"),
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    preferred_port = int(os.environ.get("PORT", 8003))
    port = find_available_port(preferred_port)

    print("\n" + "=" * 65)
    print(f"🚀 Universal Chatbot Studio & Agent Desk is running!")
    print(f"👉 Open in browser:  http://localhost:{port}")
    print(f"👉 Leads API:        http://localhost:{port}/api/leads")
    print(f"👉 Presets API:      http://localhost:{port}/api/presets")
    print("=" * 65 + "\n")
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)
