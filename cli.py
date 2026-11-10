#!/usr/bin/env python3
"""
Interactive Terminal CLI for Universal Client Chatbot.
Test your client's chatbot directly from the command line.
"""

import sys
import uuid
from bot_config import BOT_NAME, COMPANY_OR_SOFTWARE_NAME, WELCOME_MESSAGE
from backend.llm_client import ChatClient
from backend.lead_manager import (
    extract_lead_from_message,
    save_lead,
    init_lead_storage
)
from backend.session_manager import (
    get_or_create_session,
    update_session_profile,
    append_session_message,
    get_session_history,
    init_session_storage
)

def run_cli():
    init_lead_storage()
    init_session_storage()
    
    chat_client = ChatClient()
    session_id = f"cli_{uuid.uuid4().hex[:8]}"
    session = get_or_create_session(session_id)
    profile = session.get("user_profile", {})

    print("\n" + "=" * 65)
    print(f"🤖 {BOT_NAME} — {COMPANY_OR_SOFTWARE_NAME} Interactive Terminal")
    print("=" * 65)
    print(f"{BOT_NAME}: {WELCOME_MESSAGE}")
    print("Type 'exit' or 'quit' to end the session.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print(f"\n{BOT_NAME}: Goodbye! Thank you for chatting with {COMPANY_OR_SOFTWARE_NAME}.\n")
            break

        # Lead extraction
        extracted = extract_lead_from_message(user_input)
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
                interest=user_input[:100],
                notes=f"Captured via CLI: '{user_input}'"
            )
            print(f"   [Lead Saved: {saved_lead['email']} ({saved_lead['name']})]")

        # Session tracking
        append_session_message(session_id, "user", user_input)
        history = get_session_history(session_id)

        # Generate response
        reply = chat_client.generate_response(history, user_profile=profile)
        append_session_message(session_id, "assistant", reply)

        print(f"\n{BOT_NAME}: {reply}\n")

if __name__ == "__main__":
    run_cli()
