#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from pathlib import Path
import anthropic

TEST_INPUTS_PATH = Path(os.environ.get("TEST_INPUTS_PATH", "test_inputs.json"))
RESULTS_PATH     = Path(os.environ.get("RESULTS_PATH",     "results.json"))

TRIAGE_PROMPT = (
    "You are a customer support triage agent for a SaaS company.\n"
    "Classify the inbound customer email below, assess urgency, and draft a concise first response.\n\n"
    "## Email\n"
    "Subject: {subject}\n"
    "From: {sender}\n"
    "Body:\n{body}\n\n"
    "## Classification rules\n\n"
    "CATEGORY - pick exactly one:\n"
    "- billing        : invoices, charges, refunds, payment failures, subscription pricing\n"
    "- support        : how-to questions, feature confusion, general help requests\n"
    "- sales          : pricing enquiries, upgrade interest, demo requests, new purchase intent\n"
    "- account_access : login failures, password reset, locked accounts, 2FA issues\n"
    "- bug_report     : reproducible errors, crashes, unexpected behaviour, data loss\n"
    "- cancellation   : requests to cancel, downgrade, or not renew\n\n"
    "URGENCY - pick exactly one:\n"
    "- critical : data loss, security breach, complete service outage, payment fraud\n"
    "- high     : user completely blocked, billing error affecting money, bug with no workaround\n"
    "- medium   : degraded functionality, billing confusion, general support with workaround\n"
    "- low      : sales enquiry, general question, feature request, cancellation notice\n\n"
    "## Instructions\n"
    "1. Identify the category based on the dominant intent of the email.\n"
    "2. Assign urgency using the rules above. Emotional language alone does not raise urgency.\n"
    "3. Draft a reply that acknowledges the issue, states the next action, and sets expectations. Keep under 120 words.\n"
    "4. List 2-3 routing reasons explaining your classification.\n\n"
    "Respond ONLY with a JSON object, no markdown fences:\n"
    '{{"category": "<category>", "urgency": "<urgency>", "confidence": "<high|medium|low>", '
    '"routing_reasons": ["<reason1>", "<reason2>"], '
    '"draft_reply": "<reply under 120 words>", '
    '"required_reply_points": ["<point1>", "<point2>", "<point3>"]}}'
)

def _call(client, prompt, retries=3):
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except (json.JSONDecodeError, anthropic.APIError) as exc:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(f"Claude failed: {exc}") from exc

def process_item(client, item):
    inp     = item.get("input", item)
    subject = inp.get("subject", "(no subject)")
    sender  = inp.get("from", inp.get("sender", "customer"))
    body    = inp.get("body", inp.get("email_body", inp.get("text", "")))
    prompt  = TRIAGE_PROMPT.format(subject=subject, sender=sender, body=body)
    result  = _call(client, prompt)
    return {
        "id": item["id"],
        "output": {
            "category":              result.get("category", "support"),
            "urgency":               result.get("urgency", "medium"),
            "confidence":            result.get("confidence", "medium"),
            "routing_reasons":       result.get("routing_reasons", []),
            "draft_reply":           result.get("draft_reply", ""),
            "required_reply_points": result.get("required_reply_points", []),
        },
    }

def main():
    if not TEST_INPUTS_PATH.exists():
        print(f"ERROR: {TEST_INPUTS_PATH} not found", file=sys.stderr)
        sys.exit(1)
    test_inputs = json.loads(TEST_INPUTS_PATH.read_text())
    client      = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    results     = []
    total       = len(test_inputs)
    for idx, item in enumerate(test_inputs, 1):
        inp     = item.get("input", item)
        subject = inp.get("subject", "(no subject)")
        print(f"[{idx}/{total}] Triaging: {subject[:60]} ...")
        try:
            result = process_item(client, item)
            results.append(result)
            cat = result["output"]["category"]
            urg = result["output"]["urgency"]
            print(f"  Done - {cat} / {urg}")
        except Exception as exc:
            print(f"  Error: {exc}", file=sys.stderr)
            results.append({
                "id": item["id"],
                "output": {
                    "category": "support",
                    "urgency": "medium",
                    "confidence": "low",
                    "routing_reasons": [],
                    "draft_reply": f"ERROR: {exc}",
                    "required_reply_points": [],
                },
            })
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nDone - {len(results)} results written to {RESULTS_PATH}")

if __name__ == "__main__":
    main()

