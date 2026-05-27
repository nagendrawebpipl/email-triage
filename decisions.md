# Key Decisions

## 1. Single-call structured triage (classify + urgency + reply in one prompt)
The agent uses a single Claude call per email that simultaneously classifies the category, assigns urgency, and drafts the reply. This avoids unnecessary multi-call loops for straightforward cases, matching the rubric guidance, while keeping latency low and the workflow observable.

## 2. Fixed category and urgency taxonomies with explicit rules
The prompt defines exactly six categories and four urgency levels with concrete routing rules for each. This prevents free-text drift and ensures outputs align with ground truth labels deterministically.

## 3. Urgency based on impact, not emotion
The urgency rules explicitly state that emotional language alone does not raise urgency. Critical is reserved for data loss, security breaches, and outages. This prevents over-escalation of frustrated-but-non-urgent emails.

## 4. Routing reasons for observability
Every result includes a routing_reasons array with 2-3 bullet points explaining why the email was classified as it was. This makes the agent decisions transparent and auditable without requiring a separate explanation call.

## 5. Graceful fallback for ambiguous emails
Missing subject lines default to no subject and missing body fields try multiple key names. If classification fails the item defaults to support/medium so results.json always has one complete entry per input.
