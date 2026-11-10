"""
Lead extraction, persistence, and statistics manager for Universal Client Chatbot Studio.
Guarantees clean lead validation, prevents false positives, and persists to local JSON.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

DATA_DIR = Path(__file__).parent.parent / "data"
LEADS_FILE = DATA_DIR / "leads.json"

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

INVALID_NAMES = {
    "hi", "hello", "hey", "yes", "no", "sure", "ok", "okay", "thanks", "thank",
    "please", "fine", "cool", "test", "demo", "website", "blockchain", "ai",
    "software", "app", "quote", "price", "pricing", "service", "services",
    "product", "products", "project", "work", "help", "info", "question",
    "ceo", "founder", "director", "manager", "lead", "leads", "user", "guest"
}

def init_lead_storage():
    """Ensure data directory and leads.json exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LEADS_FILE.exists():
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

def is_valid_name(name_candidate: str) -> bool:
    """Validate that candidate string is an actual plausible name, not gibberish or noise."""
    if not name_candidate:
        return False
    
    clean = name_candidate.strip()
    if len(clean) < 2 or len(clean) > 40:
        return False

    if clean.lower() in INVALID_NAMES:
        return False

    # Check for vowels (prevents keyboard mash like 'jfjfjd')
    vowels = set("aeiouyAEIOUY")
    if not any(char in vowels for char in clean):
        return False

    # Must contain only alphabetic characters, spaces, hyphens
    if not re.match(r"^[A-Za-z\s\-']+$", clean):
        return False

    return True

def extract_lead_from_message(message: str) -> Dict[str, Optional[str]]:
    """
    Extract email and explicitly stated name from user message.
    Strictly ignores random single words, gibberish, and non-name inputs.
    """
    clean_msg = message.strip()
    
    # 1. Email extraction
    found_email = None
    email_match = EMAIL_REGEX.search(clean_msg)
    if email_match:
        cand_email = email_match.group(0).lower()
        if "." in cand_email.split("@")[-1] and len(cand_email.split(".")[-1]) >= 2:
            found_email = cand_email

    # 2. Name extraction: MUST have explicit intro phrase (e.g. "my name is Alex", "I am Sarah")
    found_name = None
    name_patterns = [
        r"(?:my name is|i am|i'm|this is|call me)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)",
        r"^([A-Za-z]+(?:\s+[A-Za-z]+)?)\s*,\s*.*@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    ]
    stopwords = {"and", "my", "email", "mail", "contact", "phone", "here", "please", "the", "with"}
    
    for pattern in name_patterns:
        match = re.search(pattern, clean_msg, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            words = candidate.split()
            valid_words = []
            for w in words:
                if w.lower() in stopwords:
                    break
                valid_words.append(w)
            
            if valid_words and len(valid_words) <= 3:
                candidate_name = " ".join(valid_words).title()
                if is_valid_name(candidate_name):
                    found_name = candidate_name
                    break

    return {"name": found_name, "email": found_email}

def save_lead(
    session_id: str,
    name: Optional[str],
    email: str,
    interest: Optional[str] = None,
    notes: Optional[str] = None,
    business_name: Optional[str] = None
) -> Dict[str, Any]:
    """Save or update a lead in leads.json file."""
    init_lead_storage()
    
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            leads: List[Dict[str, Any]] = json.load(f)
    except Exception:
        leads = []

    # Check if lead with this email already exists
    existing_index = None
    for idx, item in enumerate(leads):
        if item.get("email", "").lower() == email.lower():
            existing_index = idx
            break

    timestamp = datetime.now().isoformat()
    clean_name = name.title() if name and is_valid_name(name) else None

    if existing_index is not None:
        if clean_name and not leads[existing_index].get("name"):
            leads[existing_index]["name"] = clean_name
        if interest:
            leads[existing_index]["interest"] = interest
        if business_name:
            leads[existing_index]["business_name"] = business_name
        leads[existing_index]["updated_at"] = timestamp
        saved_lead = leads[existing_index]
    else:
        saved_lead = {
            "id": f"lead_{len(leads) + 1:04d}",
            "session_id": session_id,
            "business_name": business_name or "General Client",
            "name": clean_name or "Interested Visitor",
            "email": email,
            "interest": interest or "General Inquiry",
            "notes": notes or "Captured via Chatbot",
            "created_at": timestamp,
            "updated_at": timestamp
        }
        leads.insert(0, saved_lead)

    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2)

    return saved_lead

def get_all_leads() -> List[Dict[str, Any]]:
    """Retrieve all leads stored in leads.json."""
    init_lead_storage()
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def clear_all_leads():
    """Clear all captured leads."""
    init_lead_storage()
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)
