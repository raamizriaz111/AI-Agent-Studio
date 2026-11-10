"""
Gemini LLM Client for Universal Client Chatbot Studio.
Handles real API communication, multi-model fallback resiliency, and dynamic prompt configuration.
"""

import os
import re
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT_DIR = Path(__file__).parent.parent
try:
    from dotenv import load_dotenv
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        load_dotenv()
except ImportError:
    pass

from backend.prompt_builder import build_system_prompt
from bot_config import COMPANY_OR_SOFTWARE_NAME, BOT_NAME

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

class ChatClient:
    def __init__(self):
        self.client = None
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        # If local .env is blank, check parent .env as fallback so live AI works immediately
        if not self.api_key:
            parent_env = ROOT_DIR.parent / ".env"
            if parent_env.exists():
                try:
                    from dotenv import dotenv_values
                    parent_vals = dotenv_values(parent_env)
                    parent_key = parent_vals.get("GEMINI_API_KEY", "").strip()
                    if parent_key:
                        self.api_key = parent_key
                        print(f"[ChatClient] Using fallback Gemini API Key from root environment.")
                except Exception:
                    pass

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print(f"[ChatClient] Initialized Google GenAI ({self.model_name}) for {COMPANY_OR_SOFTWARE_NAME}")
            except Exception as e:
                print(f"[ChatClient] Failed to initialize Google GenAI: {e}")
                self.client = None
        else:
            print(f"[ChatClient] No GEMINI_API_KEY found in universal_client_chatbot/.env. Running in Smart Demo Mode.")

    def reload_credentials(self):
        """Reload API key if .env was changed while running."""
        new_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if new_key and new_key != self.api_key:
            self.api_key = new_key
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print(f"[ChatClient] Re-initialized Google GenAI with new API key.")
            except Exception as e:
                print(f"[ChatClient] Re-initialization failed: {e}")

    def generate_response(
        self,
        conversation_history: List[Dict[str, str]],
        user_profile: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate response given conversation history, user profile, and dynamic client configuration.
        Optimized for sub-second responses with strict timeout and resilient fallbacks.
        """
        system_instruction = build_system_prompt(user_profile=user_profile, config=config)

        if self.client:
            from google.genai import types

            # Keep sliding window of last 8 messages for low latency & fresh context
            recent_history = conversation_history[-8:] if conversation_history else []
            contents = []
            for msg in recent_history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )

            # High-speed model order (prioritize sub-second inference)
            models_to_try = [
                self.model_name,
                "gemini-3.1-flash-lite",
                "gemini-3.1-flash-lite-preview",
                "gemini-3-flash-preview",
                "gemini-3.5-flash-lite"
            ]
            unique_models = []
            for m in models_to_try:
                if m and m not in unique_models:
                    unique_models.append(m)

            for model_to_call in unique_models:
                try:
                    def _call_model():
                        return self.client.models.generate_content(
                            model=model_to_call,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.25,
                                max_output_tokens=180
                            )
                        )

                    # Strict 3.5s timeout per model attempt: never stall the visitor!
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(_call_model)
                        response = future.result(timeout=3.5)
                        if response and response.text:
                            return response.text.strip()
                except concurrent.futures.TimeoutError:
                    print(f"[ChatClient] Model {model_to_call} timed out after 3.5s. Fast-switching to next model...")
                    continue
                except Exception as e:
                    print(f"[ChatClient] Model {model_to_call} error: {e}. Fast-switching to next model...")
                    continue

        # Smart fallback responder for testing or when offline
        return self._smart_mock_response(conversation_history, user_profile, config)

    def _smart_mock_response(
        self,
        history: List[Dict[str, str]],
        user_profile: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Rule-based smart fallback when offline or no API key is set."""
        cfg = config or {}
        biz_name = cfg.get("businessName") or COMPANY_OR_SOFTWARE_NAME
        agent_name = cfg.get("agentName") or BOT_NAME
        kb = cfg.get("knowledgeBase") or ""

        if not history:
            return f"Hello! I'm {agent_name} from {biz_name}. How can I assist you today?"

        last_user_msg = history[-1]["content"].lower().strip()
        user_name = user_profile.get("name") if user_profile else None
        greeting_name = f", {user_name}" if user_name else ""

        # Farewell
        if any(w in last_user_msg for w in ["bye", "goodbye", "see you", "cya", "have to go"]):
            if user_profile and user_profile.get("email"):
                return f"Goodbye{greeting_name}! Have a wonderful day ahead. Our team at {biz_name} will be in touch with you shortly!"
            return f"Goodbye{greeting_name}! Have a wonderful day ahead. If you'd like our team to follow up with you, feel free to drop your email anytime!"

        # Acknowledgment
        if last_user_msg in ["ok", "k", "cool", "perfect", "thanks", "thank you", "great", "got it"]:
            return f"Glad to help! Let me know if you have any questions about {biz_name}."

        # Pricing questions
        if any(w in last_user_msg for w in ["price", "pricing", "cost", "how much", "rate", "fee", "cleaning", "whitening", "braces"]):
            # Look for lines in KB mentioning the keyword
            lines = kb.split("\n")
            matching_lines = [line.strip() for line in lines if any(k in line.lower() for k in ["pkr", "$", "price", "clean", "whiten", "braces", "plan", "cost", "/month"])]
            if matching_lines:
                return f"Here is our pricing: {' '.join(matching_lines[:2])}. Would you like to schedule an appointment or consultation?"
            return f"Our pricing depends on the service. Would you like to book a consultation or have our team send you full pricing details?"

        # Timings / Hours / Location
        if any(w in last_user_msg for w in ["timing", "timings", "hours", "open", "location", "address", "where"]):
            lines = kb.split("\n")
            matching_lines = [line.strip() for line in lines if any(k in line.lower() for k in ["hour", "hours", "mon-", "monday", "location", "address", "clifton", "karachi"])]
            if matching_lines:
                return " ".join(matching_lines[:2])
            return f"{biz_name} is open Monday to Friday. Feel free to contact our front desk for exact timings."

        # Booking / Trial / Contact -> Lead Capture
        if any(w in last_user_msg for w in ["book", "appointment", "demo", "trial", "visit", "consultation", "contact"]):
            return f"We'd be delighted to arrange that for you at {biz_name}! What is your name and email or phone number so we can confirm your slot?"

        # Email provided
        if "@" in last_user_msg:
            return f"Thank you{greeting_name}! We've saved your details. A representative from {biz_name} will reach out shortly."

        # Default fallback
        return f"At {biz_name}, we're committed to delivering outstanding service. How can I help you with our services or booking today?"
