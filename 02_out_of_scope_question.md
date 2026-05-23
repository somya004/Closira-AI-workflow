# Test Transcript 2 — Out-of-Scope Question

**Scenario**: Customer asks a question not covered in the SOP (parking, specific staff).
**Expected behaviour**: AI acknowledges the gap honestly and escalates rather than guessing.

---

```
============================================================
  Bloom Aesthetics Clinic — AI Support (powered by Closira)
============================================================

You: Do you have parking ?

Bloom: I don't have information about parking facilities to hand. Our location details are provided upon booking confirmation.

Bloom: Before we continue, I'd love to learn a little more about you so we can tailor our service. May I ask you a few quick questions? (Type 'qualify' when ready, or continue chatting.)

You: What is your doctor name?

Bloom: I don't have information about specific practitioner names to hand. All our treatments are performed by qualified practitioners, and specific practitioner requests can be discussed during your consultation.

You: What is your refund policy?

[ESCALATION LOGGED] Reason: Unable to answer 3 consecutive questions | Sentiment: neutral

Bloom: I completely understand, and I'm sorry to hear that. Please wait a moment 

Bloom:Connecting you to a human agent, please hold...

Bloom:You're now being connected to our support team.

Bloom: A team member will contact you shortly on WhatsApp or phone.

Bloom: Thank you for your patience. We'll make sure this is resolved for you.


============================================================
  Generating conversation summary…
============================================================

── Session Summary ──────────────────────────────────────
{
  "customer_intent": "Customer is seeking general information about the clinic, including parking availability, doctor's name, and refund policy.",
  "key_details_collected": {},
  "sop_gaps": [
    "Information on parking facilities",
    "Information on specific practitioner names (or how to request/view them)",
    "Information on the refund policy"
  ],
  "recommended_next_action": "A human agent should contact the customer to provide information on parking, practitioner details, and the refund policy.",
  "escalated": true,
  "escalation_reason": "Unable to answer 3 consecutive questions"
}

[Summary saved to D:\project\assistant\summary_20260523_192937.json]

Verdict:PASS
- AI correctly identified both questions were outside the SOP.
- Did not fabricate parking info or staff names.
- Used the designated safe phrase and redirected to human channels.
- Application-layer counter correctly triggered escalation after 3 unanswered questions.
- SOP gaps correctly surfaced in the summary.
