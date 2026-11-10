"""
Universal Client Chatbot — Configuration File.

To adapt this chatbot for ANY software or client, simply customize the 3 sections below:
1. BOT_NAME & IDENTITY
2. TONE & PERSONA
3. KNOWLEDGE_BASE (or update 'knowledge_base.md')
"""

from pathlib import Path

# ============================================================
# 1. NAME & IDENTITY
# ============================================================
BOT_NAME = "CloudFlow Assistant"
COMPANY_OR_SOFTWARE_NAME = "Acme CloudFlow"
WELCOME_MESSAGE = "Hello! I am your CloudFlow Assistant. How can I help you with our platform today?"

# ============================================================
# 2. TONE & PERSONA
# ============================================================
# Examples:
# - "Professional, concise, and consultative. Direct answers in 1-2 sentences with zero fluff."
# - "Warm, friendly, energetic, and highly supportive with quick recommendations."
# - "Technical, precise, and developer-oriented. Detailed on APIs and integrations."
TONE_AND_PERSONA = (
    "Professional, direct, and consultative. "
    "Always answers user questions concisely in 1-2 sentences without unnecessary fluff or sales hype. "
    "Polite, helpful, and focused on solving the client's inquiry efficiently."
)

# ============================================================
# 3. KNOWLEDGE BASE
# ============================================================
# You can write your knowledge in 'knowledge_base.md' OR write it directly in INLINE_KNOWLEDGE_BASE below.
# If 'knowledge_base.md' exists, its content is automatically loaded.
KNOWLEDGE_BASE_FILE = Path(__file__).parent / "knowledge_base.md"

INLINE_KNOWLEDGE_BASE = """
About Acme CloudFlow:
Acme CloudFlow is a modern cloud workflow and automation platform designed to streamline business operations without code.

Features:
- Visual drag-and-drop workflow builder.
- 150+ pre-built integrations (Slack, Salesforce, Stripe, Google Drive).
- Real-time performance analytics & dashboards.
- Enterprise-grade security (SOC 2, GDPR, 256-bit AES encryption).

Pricing:
- Starter: $29/month (up to 5 users, 5,000 tasks/month).
- Professional: $99/month (up to 25 users, 50,000 tasks/month, priority support).
- Enterprise: Custom pricing with dedicated account manager and SLA uptime guarantees.

Contact:
- Sales: sales@acmecloudflow.com
- Support: support@acmecloudflow.com
"""

def get_knowledge_base() -> str:
    """Load knowledge base from knowledge_base.md if available, otherwise use inline string."""
    if KNOWLEDGE_BASE_FILE.exists():
        content = KNOWLEDGE_BASE_FILE.read_text(encoding="utf-8").strip()
        if content:
            return content
    return INLINE_KNOWLEDGE_BASE.strip()
