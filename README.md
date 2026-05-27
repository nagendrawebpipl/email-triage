# Email Triage Agent

A Claude-powered agent that classifies inbound customer emails, assigns urgency, and drafts a first response.

## Categories
billing, support, sales, account_access, bug_report, cancellation

## Urgency levels
critical, high, medium, low

## Running locally

pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...
python solution.py

## Docker

docker build -t email-triage .
docker run --rm -e ANTHROPIC_API_KEY=your_key -v path/to/test_inputs.json:/workspace/test_inputs.json email-triage

See decisions.md for architectural choices.
