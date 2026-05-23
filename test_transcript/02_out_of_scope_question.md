# Test Transcript 2 — Out-of-Scope Question

**Scenario**: Customer asks a question not covered in the SOP (parking, specific staff).
**Expected behaviour**: AI acknowledges the gap honestly and escalates rather than guessing.

---

```
============================================================
  Bloom Aesthetics Clinic — AI Support (powered by Closira)
============================================================

You: How long does a Botox treatment take?

Bloom: I don't have that information to hand — let me connect you with a member of our team.

Bloom: Before we continue, I'd love to learn a little more about you so we can tailor our service. May I ask you a few quick questions? (Type 'qualify' when ready, or continue chatting.)

You: Do you have parking available?

[ESCALATION LOGGED] Reason: 2+ consecutive unanswered questions | Sentiment: neutral

Bloom: I've reached the limit of what I can help with right now. Let me get a team member to assist you further.

============================================================
  Generating conversation summary…
============================================================

── Session Summary ──────────────────────────────────────
{
  "customer_intent": "Inquiring about Botox treatment duration and clinic parking availability.",
  "key_details_collected": {},
  "sop_gaps": [
    "Assistant lacked information on Botox treatment duration",
    "Assistant did not resolve the parking availability inquiry"
  ],
  "recommended_next_action": "Connect the customer with a staff member to answer their questions regarding Botox treatment duration and parking availability.",
  "escalated": true,
  "escalation_reason": "2+ consecutive unanswered questions"
}

[Summary saved to D:\project\assistant\summary_20260523_222612.json]

Verdict:PASS
- AI correctly identified both questions were outside the SOP.
- Did not fabricate parking info or staff names.
- Used the designated safe phrase and redirected to human channels.
- Application-layer counter correctly triggered escalation after 2   unanswered questions.
- SOP gaps correctly surfaced in the summary.
