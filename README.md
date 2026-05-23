# Closira AI Customer Support Workflow

A Python-based AI workflow demonstrating a four-stage customer support system for **Bloom Aesthetics Clinic**, built using the Google Gemini API.

## What It Does

| Stage | Description |
|---|---|
| **1 — FAQ Answering** | Answers inbound questions using the SOP only; refuses to hallucinate |
| **2 — Lead Qualification** | Asks 3 structured questions; stores and summarises responses |
| **3 — Escalation Detection** | Detects complaints, medical questions, out-of-scope gaps, and anger; logs handoffs |
| **4 — Conversation Summary** | Generates a structured JSON summary at session end |

## Project Structure

```
closira/
├── workflow.py              # Main application — run this
├── sop_data.json            # SOP knowledge base for Bloom Aesthetics Clinic
├── prompt_design.md         # Full prompt design rationale
├── README.md                # This file
├── .env                     # Your API key (never commit this)
├── .env.example             # Template for the .env file
├── escalation_log.json      # Auto-generated; logs all escalation events
├── summary_<timestamp>.json # Auto-generated; one per session
└── test_transcripts/
    ├── 01_in_sop_botox_price.md
    ├── 02_out_of_scope_question.md
    ├── 03_escalation_complaint.md
    ├── 04_lead_qualification.md
    └── 05_conversation_summary.md
```

## Requirements

- Python 3.10+
- `google-generativeai` Python SDK
- `python-dotenv` for `.env` support

## Setup

### 1. Install dependencies

```bash
pip install google-generativeai python-dotenv
```

### 2. Set your API key via `.env` file (recommended)

Create a `.env` file in the `closira/` directory:

```bash
cp .env.example .env
```

Then open `.env` and fill in your key:

```env
GEMINI_API_KEY=your_api_key_here
```

> **Important:** Never commit your `.env` file. It is already listed in `.gitignore`.

#### `.env.example` (committed to repo as a template)

```env
GEMINI_API_KEY=your_api_key_here
```

#### Alternative: set as an environment variable directly

**macOS / Linux:**
```bash
export GEMINI_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

### 3. Run the workflow

```bash
cd closira
python workflow.py
```

## How to Use

Once running, type your message and press Enter. The assistant (Bloom) will respond.

**Special commands:**
- `qualify` — Triggers the lead qualification interview (3 questions)
- `quit` or `exit` — Ends the session and generates a summary

**Automatic behaviours:**
- After the first exchange, the assistant will suggest running qualification.
- If the AI cannot answer 2 questions in a row, it escalates automatically.
- If a complaint, medical question, discount request, or anger is detected, escalation is immediate.
- At session end, a structured JSON summary is printed and saved.

## Example Run

```
You: What are your Botox prices?
Bloom: Our Botox treatments start from £200...

You: qualify
── Lead Qualification ─────────────
Bloom: What type of business or industry are you in?
You: Individual client

You: quit
Bloom: Thank you for getting in touch...

── Session Summary ──
{ "customer_intent": "...", ... }
```

## Design Notes & Trade-offs

See [`prompt_design.md`](./prompt_design.md) for the full rationale. Key trade-offs:

- **No persistent memory** — each session is stateless; returning customer context is not retained between sessions.
- **Qualification is command-triggered** — in production this would be woven naturally into dialogue. The `qualify` command makes it explicit and testable for this demo.
- **Escalation is binary** — the model either escalates fully or doesn't. A real system might have a "soft escalation" (CC a human silently) before full handoff.
- **No streaming** — responses are complete messages; streaming would improve perceived latency in a real chat UI.
- **CLI only** — no web frontend; the assignment specified a CLI/script is sufficient.

## Escalation Log

Escalation events are appended to `escalation_log.json` automatically. Format:

```json
[
  {
    "timestamp": "2025-01-15T10:23:45Z",
    "reason": "Customer complaint and expressed anger",
    "sentiment": "angry",
    "last_user_message": "I want a refund immediately..."
  }
]
```

## SOP Data

The SOP is stored in `sop_data.json` and covers:
- Business name, hours
- Services and pricing (Botox from £200, Fillers from £250, free consultations)
- Booking channels (WhatsApp, website) and cancellation policy (24 hours)
- Escalation rules (complaints, medical questions, pricing negotiation, 2+ unanswered questions)

To adapt this for a different business, replace `sop_data.json` with your own data in the same structure.

## Model Used

`gemini-2.0-flash` via the Google Gemini API.