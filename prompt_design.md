# Prompt Design — Closira / Bloom Aesthetics Clinic

## 1. System Prompt

```
You are Bloom, the friendly AI assistant for Bloom Aesthetics Clinic.
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
{ ... full SOP JSON ... }
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
{"action": "ESCALATE", "reason": "<short reason>", "sentiment": "<neutral|frustrated|angry>"}

## Normal Response Format
For all non-escalation replies, respond in plain conversational text only.
Do not use JSON in normal responses.
```

---

## 2. Design Decisions

### 2.1 SOP Injection via `<SOP>` Tags
The full SOP JSON is embedded in the system prompt inside `<SOP>` XML-style tags. This gives the
model a clearly delimited "source of truth" region. Structured JSON was chosen over prose because:
- It preserves data relationships (e.g. price + currency + notes per service).
- It is easy to extend without restructuring the prompt.
- It reads well to both the model and human reviewers.

### 2.2 Named Persona ("Bloom")
Naming the assistant after the clinic creates a branded, coherent identity. It also anchors the
model's behaviour — responses in character as "Bloom the receptionist" are naturally more restrained
and professional than a generic assistant persona.

### 2.3 Explicit Role Description
The system prompt states the assistant's job in one sentence: *"help customers with enquiries,
qualify leads, and ensure they get the right support."* This prevents the model from interpreting
its role too broadly (e.g., giving medical advice) or too narrowly (refusing to ask follow-up
questions).

### 2.4 Tone Anchoring via Analogy
Rather than listing adjectives ("be warm, be professional"), the prompt uses the analogy of **"a
knowledgeable receptionist at a premium clinic."** This leverages the model's rich understanding of
what that role looks, sounds, and feels like — more effective than a list of traits.

---

## 3. Hallucination Prevention

Three mechanisms work in combination:

| Mechanism | Implementation |
|---|---|
| **Explicit prohibition** | "You may ONLY answer factual questions using the data below. Do NOT invent prices, services, policies." |
| **Boundary acknowledgment script** | The model is given a specific safe phrase to use when it doesn't know something, reducing the temptation to fill the gap with a plausible guess. |
| **Structured SOP** | JSON format makes it easy for the model to locate specific facts; ambiguity is reduced versus free-text SOPs where facts can blur together. |
| **Unanswered question counter** | The application layer tracks consecutive "I don't know" responses and escalates after 2, preventing the model from being nudged into guessing on repeat attempts. |

The combination of prompt-level instruction and application-level guard means hallucination
prevention is **not** solely dependent on the model following instructions — the code enforces it
independently.

---

## 4. Confidence-Based Escalation

### 4.1 Structured Output Signal
The model is instructed to respond with a specific JSON object **in place of** a normal text reply
when escalation is required:

```json
{"action": "ESCALATE", "reason": "<short reason>", "sentiment": "<neutral|frustrated|angry>"}
```

This is a **hard output format switch**, not a soft confidence score. It avoids ambiguity in
parsing and eliminates the need for a regex/heuristic to detect "low confidence" prose.

### 4.2 Why Not a Confidence Score?
LLMs don't produce reliable numerical confidence in text output. Instead, the prompt teaches the
model to recognise **specific trigger conditions** (complaint, medical question, discount request,
etc.) — these are more reliably detectable than asking the model to self-assess a probability.

### 4.3 Escalation Triggers Defined
The triggers are drawn directly from the SOP's own escalation rules, plus common-sense additions:

1. **Complaint / frustration / anger** — prevents the AI from attempting to de-escalate a serious
   complaint alone, which could worsen the situation.
2. **Medical questions** — aesthetic clinic context; any medical content is out of scope and carries
   liability risk.
3. **Pricing negotiation** — commercial decisions should remain with human staff.
4. **2+ unanswered questions** — if the AI has hit the edge of the SOP twice in a row, further
   attempts to answer are likely to produce unreliable responses.
5. **Explicit human request** — always honoured immediately, no questions asked.

### 4.4 Application-Layer Safety Net
The code also tracks `unanswered_count` independently of the model's output. This means even if
the model fails to trigger JSON escalation, the application will catch repeated gaps and escalate
programmatically. Defence in depth.

### 4.5 Escalation Logging
Every escalation is appended to `escalation_log.json` with:
- UTC timestamp
- Reason string
- Sentiment classification
- The last user message that triggered it

This log is the operational data Closira would use to identify SOP gaps and training needs.

---

## 5. Lead Qualification Design

Qualification is handled outside the main LLM conversation loop as a **structured interview** with
three fixed questions:

1. **Business / industry type** — helps segment the lead (individual vs. corporate vs. referral).
2. **Team / organisation size** — proxy for deal size and complexity.
3. **Current tools in use** — identifies switching opportunity and integration needs.

Answers are stored in a `qualification_data` dict and included verbatim in the session summary
prompt. This keeps qualification data clean and unambiguous — it is not inferred from conversation
prose, so there is no risk of the model misattributing or conflating answers.

The qualification step is offered automatically after the first substantive exchange and can also
be triggered manually with the `qualify` command. This non-intrusive approach avoids interrupting
a customer who has a simple, urgent question.

---

## 6. Conversation Summary Design

A separate `SUMMARY_SYSTEM` prompt is used for the end-of-session summary. This separation is
intentional:
- The conversational system prompt is optimised for customer interaction (brevity, warmth).
- The summary prompt is optimised for structured analytical output (JSON, completeness).

Mixing both roles in one prompt would create tension between the two behaviours.

The summary fields are:

| Field | Purpose |
|---|---|
| `customer_intent` | High-level goal of the customer |
| `key_details_collected` | All factual details gathered (name, service interest, qualification data) |
| `sop_gaps` | Questions the AI could not answer — actionable for SOP improvement |
| `recommended_next_action` | What a human agent should do next |
| `escalated` | Boolean flag for triage |
| `escalation_reason` | Populated if escalation occurred |

---

## 7. Trade-offs and Known Limitations

| Limitation | Notes |
|---|---|
| No persistent memory | Each session starts fresh. Returning customer context not carried over. |
| Qualification is interruption-based | The `qualify` flow pauses the main conversation. In production, this would be woven into the dialogue naturally. |
| Escalation detection relies on model compliance | If the model is prompted adversarially to not follow format instructions, the code-level `unanswered_count` guard is the backstop. |
| Single-turn summary | Summary is generated once at session end, not progressively. Long sessions may lose nuance if context window is constrained. |
| No streaming | Responses are returned as complete messages. Streaming would improve perceived latency in a real chat UI. |
