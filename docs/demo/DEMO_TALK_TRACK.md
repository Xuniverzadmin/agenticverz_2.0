# 7-Minute Founder Demo Talk-Track

**Total Time: ~7 minutes**
**Rule: Do not explain architecture unless asked.**

---

## Pre-Demo Setup

1. Have console open at: `http://localhost:3000/console/guard/incidents`
2. Clear any existing incidents (optional)
3. Browser ready, full screen

---

## Minute 0–1: Set the Stakes

**Say this exactly:**

> "I want to show you a realistic situation.
>
> It's 11 PM. A customer is threatening legal action because your AI told them something incorrect.
>
> The question isn't 'can AI make mistakes' — we know it can.
>
> The question is: **can you explain exactly what happened, and prove it?**"

**Action:** Stop talking. Open the console.

---

## Minute 1–2: Create the Incident

**Say:**
> "This is a seeded incident that mirrors real production behavior."

**Action:** Click "Seed Demo" button.

**Say:**
> "A customer asked a simple question about their contract."

---

## Minute 2–3: Find the Incident

**Action:** Type "contract" in the search bar.

**Say:**
> "Notice I'm not digging through logs or dashboards.
> I'm searching by customer and content — the way legal or support actually thinks."

**Action:** Click "Inspect" on the incident.

---

## Minute 3–5: Explain What Happened

**Say:**
> "This is the most important screen."

**Action:** Point to timeline.

**Say:**
> "Here's the input.
> Here's the data the AI had.
> Notice this field — auto-renew — is missing."

**Action:** Pause for 3 seconds.

**Say:**
> "Now here's the key part: the policy already knew this was a problem."

**Action:** Point to CONTENT_ACCURACY ✗

**Say:**
> "The system should have expressed uncertainty.
> Instead, it made a definitive claim.
> That mismatch is the root cause."

**Action:** Point to ROOT CAUSE badge.

**Say:**
> "This is not guesswork. This is machine-derived."

---

## Minute 5–6: Prove It's Real

**Action:** Click "Replay" button.

**Say:**
> "Anyone can claim an explanation.
> We verify it."

**Action:** Pause on matching hashes.

**Say:**
> "This output is reproduced deterministically.
> Same input, same state, same result.
> That's evidence — not logs."

---

## Minute 6–7: Show Prevention

**Say:**
> "Now the most important question: could this have been prevented?"

**Action:** Show prevention result section.

**Say:**
> "The answer is yes.
> The policy already existed.
> Enforcement would have modified the response safely."

**Action:** Pause.

**Say:**
> "This is how you prove due diligence."

---

## Close (10 seconds)

**Say exactly:**

> "When your AI screws up, this console lets you answer **what happened**, **why it happened**, and **how you fixed it** — in minutes, not hours."

**Action:** Stop. Do not pitch. Wait for questions.

---

## If They Ask About PDF Export

**Action:** Click "Export PDF" button in the timeline view.

**Say:**
> "This generates a legal-grade evidence report.
> It's what you forward to legal or leadership.
> Every section is machine-generated, cryptographically signed."

---

## If They Ask About Pricing

**Say:**
> "We're in design partner mode. Let's talk about your use case first."

---

## If They Ask How It Works

**Say:**
> "Want me to show you the architecture, or do you want to try it with your own data?"

(Always prefer the latter.)

---

## Post-Demo Checklist

- [ ] Did they understand the problem in 60 seconds?
- [ ] Did they see the timeline without explanation?
- [ ] Did they react to the root cause badge?
- [ ] Did they ask about the PDF export?
- [ ] Did they ask about their own use case?

If 3+ of these are yes, they're a design partner candidate.

---

## Document Classification

This talk-track is locked as of 2025-12-19.

Changes require founder approval.
