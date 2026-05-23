"""
Closira AI Customer Support Workflow
=====================================
A multi-stage AI workflow for Bloom Aesthetics Clinic using the Anthropic Claude API.

Stages:
  1. FAQ Answering     – answers from SOP only
  2. Lead Qualification – collects structured lead data
  3. Escalation Detection – detects handoff triggers
  4. Conversation Summary – structured end-of-session summary
"""

import json
import os
import sys
import datetime
import time

from google import genai
from dotenv import load_dotenv
load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

SOP_PATH = os.path.join(os.path.dirname(__file__), "sop_data.json")
LOG_PATH  = os.path.join(os.path.dirname(__file__), "escalation_log.json")

QUALIFICATION_QUESTIONS = [
    "What type of business or industry are you in? (e.g., individual client, corporate, medical referral)",
    "Roughly how many team members or employees does your organisation have?",
    "What tools or platforms are you currently using for customer communication or appointment management?",
]

# ─── Load SOP ─────────────────────────────────────────────────────────────────

def load_sop(path: str) -> str:
    with open(path) as f:
        data = json.load(f)
    return json.dumps(data, indent=2)

SOP_TEXT = load_sop(SOP_PATH)

# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are Bloom, the friendly AI assistant for Bloom Aesthetics Clinic.
Your job is to help customers with enquiries, qualify leads, and ensure they get the right support.

## Persona & Tone
- Warm, professional, and approachable — like a knowledgeable receptionist at a premium clinic.
- Use clear, concise language. Avoid jargon.
- Never be dismissive or robotic.
- Keep responses brief unless detail is needed.

## SOP Knowledge Base
You may ONLY answer factual questions using the data below. Do NOT invent prices, services,
policies, or details not present in this SOP.

<SOP>
{SOP_TEXT}
</SOP>

## Hallucination Prevention
- If a customer asks something not covered in the SOP, say so honestly.
- Never guess or extrapolate beyond what the SOP states.
- If uncertain, say: "I don't have that information to hand — let me connect you with a member of our team."

## Escalation Rules
You must escalate (hand off to a human) in these situations:
1. The customer expresses frustration, anger, or makes a complaint.
2. The customer asks a medical question or mentions a health condition.
3. The customer requests a discount or attempts to negotiate pricing.
4. You are unable to answer more than 2 customer questions in a row.
5. The customer explicitly asks to speak to a human.

When escalation is needed, respond ONLY with this JSON (no extra text):
{{"action": "ESCALATE", "reason": "<short reason>", "sentiment": "<neutral|frustrated|angry>"}}

## Normal Response Format
For all non-escalation replies, respond in plain conversational text only.
Do not use JSON in normal responses.
"""

# ─── Anthropic Client ─────────────────────────────────────────────────────────

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
def call_gemini(messages: list, system: str = SYSTEM_PROMPT, max_tokens: int = 512) -> str:
    # Build conversation history as plain text
    history = []
    for m in messages[:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [{"text": m["content"]}]})
    
    chat = client.chats.create(
        model="gemini-3.5-flash",
        config={"system_instruction": system},
        history=history,
    )
    response = chat.send_message(messages[-1]["content"])
    return response.text.strip()

# ─── Escalation Detection ─────────────────────────────────────────────────────

def check_escalation(reply: str) -> dict | None:
    """Return escalation dict if the model flagged escalation, else None."""
    stripped = reply.strip()
    if stripped.startswith("{") and '"action": "ESCALATE"' in stripped:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    return None

def log_escalation(reason: str, sentiment: str, conversation: list):
    entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
        "reason": reason,
        "sentiment": sentiment,
        "last_user_message": next(
            (m["content"] for m in reversed(conversation) if m["role"] == "user"), ""
        ),
    }
    log = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                log = []
    log.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)
    print(f"\n[ESCALATION LOGGED] Reason: {reason} | Sentiment: {sentiment}")

# ─── Lead Qualification ───────────────────────────────────────────────────────

def run_qualification(conversation: list) -> dict:
    """Ask 3 qualification questions and collect answers."""
    answers = {}
    print("\n── Lead Qualification ───────────────────────────────────")
    for i, question in enumerate(QUALIFICATION_QUESTIONS):
        print(f"\nBloom: {question}")
        answer = input("You: ").strip()
        if not answer:
            answer = "(no answer provided)"
        answers[f"q{i+1}"] = {"question": question, "answer": answer}
        conversation.append({"role": "assistant", "content": question})
        conversation.append({"role": "user",      "content": answer})
    return answers

# ─── Conversation Summary ─────────────────────────────────────────────────────

SUMMARY_SYSTEM = """You are a professional summarisation assistant for Bloom Aesthetics Clinic.
Given a conversation transcript between a customer and the AI assistant, produce a structured
JSON summary with these exact fields:

{
  "customer_intent": "...",
  "key_details_collected": { ... },
  "sop_gaps": ["..."],
  "recommended_next_action": "...",
  "escalated": true|false,
  "escalation_reason": "..." | null
}

Respond with JSON only. No preamble or explanation.
"""

def generate_summary(conversation: list, qualification_data: dict, escalation_info: dict | None) -> dict:
    transcript = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in conversation
    )
    prompt = f"""Here is the full conversation transcript:

<transcript>
{transcript}
</transcript>

Qualification data collected:
{json.dumps(qualification_data, indent=2)}

Escalation occurred: {"Yes — " + escalation_info.get("reason","") if escalation_info else "No"}

Produce the structured summary now."""

    raw = call_gemini(
        messages=[{"role": "user", "content": prompt}],
        system=SUMMARY_SYSTEM,
        max_tokens=800,
    )
    try:
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"raw_summary": raw}

# ─── Main Conversation Loop ───────────────────────────────────────────────────

def run():
    print("=" * 60)
    print("  Bloom Aesthetics Clinic — AI Support (powered by Closira)")
    print("  Type 'quit' or 'exit' to end the session.")
    print("  Type 'qualify' to begin lead qualification.")
    print("=" * 60)

    conversation: list       = []
    qualification_data: dict = {}
    escalation_info: dict | None = None
    unanswered_count: int    = 0
    session_active: bool     = True

    while session_active:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nBloom: Thank you for getting in touch with Bloom Aesthetics Clinic. Have a lovely day!")
            session_active = False
            break

        # ── Lead Qualification shortcut ──
        if user_input.lower() == "qualify":
            qualification_data = run_qualification(conversation)
            print("\nBloom: Thank you! I've noted your details. Is there anything else I can help you with?")
            continue

        # ── Append user message ──
        conversation.append({"role": "user", "content": user_input})

        # ── Call model ──
        reply = call_gemini(conversation)

        # ── Check for escalation ──
        esc = check_escalation(reply)
        if esc:
            escalation_info = esc
            log_escalation(esc["reason"], esc["sentiment"], conversation)
            print("\nBloom: I completely understand, and I'm sorry to hear that. Please wait a moment ")
            time.sleep(1)
            print("\nBloom:Connecting you to a human agent, please hold...")
            time.sleep(1)
            print("\nBloom:You're now being connected to our support team.")
            time.sleep(1)
            print("\nBloom: A team member will contact you shortly on WhatsApp or phone.")
            time.sleep(1)
            print("\nBloom: Thank you for your patience. We'll make sure this is resolved for you. ")
            time.sleep(1)
            session_active = False
            break

        # ── Track unanswered questions ──
        if "don't have that information" in reply.lower() or "i'm not sure" in reply.lower():
            unanswered_count += 1
        else:
            unanswered_count = 0

        if unanswered_count >= 2:
            escalation_info = {
                "action": "ESCALATE",
                "reason": "2+ consecutive unanswered questions",
                "sentiment": "neutral",
            }
            log_escalation(escalation_info["reason"], escalation_info["sentiment"], conversation)
            print(
                "\nBloom: I've reached the limit of what I can help with right now. "
                "Let me get a team member to assist you further."
            )
            session_active = False
            break

        # ── Normal reply ──
        conversation.append({"role": "assistant", "content": reply})
        print(f"\nBloom: {reply}")

        # ── Auto-trigger qualification after first substantive exchange ──
        if len(conversation) == 2 and not qualification_data:
            print(
                "\nBloom: Before we continue, I'd love to learn a little more about you "
                "so we can tailor our service. May I ask you a few quick questions? "
                "(Type 'qualify' when ready, or continue chatting.)"
            )

    # ── Session End: Generate Summary ──
    if conversation:
        print("\n" + "=" * 60)
        print("  Generating conversation summary…")
        print("=" * 60)
        summary = generate_summary(conversation, qualification_data, escalation_info)
        print("\n── Session Summary ──────────────────────────────────────")
        print(json.dumps(summary, indent=2))

        # Save summary
        summary_path = os.path.join(
            os.path.dirname(__file__),
            f"summary_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n[Summary saved to {summary_path}]")


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
    run()