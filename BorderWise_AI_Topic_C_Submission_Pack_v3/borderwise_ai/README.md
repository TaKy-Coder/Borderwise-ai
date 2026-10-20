# BorderWise AI — FinTechathon 2026, Topic C

**Cross-border & Student Finance Assistant**

BorderWise is a local-first prototype for students planning study-abroad finances. It estimates costs and funding gaps, compares user-entered transfer quotes, provides cross-border readiness checklists, and offers an assistant with safe calculator tools.

## Start the working browser app (recommended)

The project now includes a zero-extra-dependency web application. It uses Python's standard library and does **not** require Streamlit or any `pip install` step.

### Windows

1. Extract the ZIP archive.
2. Install Python 3.10 or newer if it is not already installed.
3. Double-click `START_BORDERWISE.bat` inside the `borderwise_ai` folder.
4. Your browser should open at `http://127.0.0.1:8501`.
5. Keep the terminal window open while using the app. Press `Ctrl+C` in that window to stop it.

If double-click launch does not work, open PowerShell in the project folder and run:

```powershell
py server.py
```

See `INSTALL_AND_RUN_WINDOWS.md` for more help.

### macOS / Linux

```bash
python3 server.py
```

The server is available at `http://127.0.0.1:8501` by default. To change the port, set the `BORDERWISE_PORT` environment variable before starting.

## What works

- **Student budget planner:** one-time tuition / arrival costs, monthly living costs, savings, recurring family support, funding gap, and a BDT equivalent based on the user's exchange-rate assumption.
- **Transfer quote comparison:** compares manually entered fees and exchange rates for the same BDT budget, then ranks quotes by estimated recipient amount.
- **Credit and cross-border readiness checklists:** educational questions to review before choosing products, paying tuition, or relying on visa-related information.
- **Ask BorderWise:** local rules-based replies without an API key, or optional model-powered replies with two allowlisted calculator tools.
- **Audit log:** keeps limited event metadata in server memory; does not store chat prompts or financial amounts in those audit events.
- **JSON downloads:** export budget calculations, quote comparisons, and the audit log.
- **Automated tests:** run the calculation and local API tests with Python's `unittest`.

## Optional model-powered chat

Without a key, all deterministic tools work and the chat uses the local rules-based helper. To enable model-powered chat, supply a valid model-provider API key to the local server process. In Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="YOUR_ACTUAL_API_KEY"
$env:BORDERWISE_MODEL="gpt-4.1-mini"
py server.py
```

The key stays on the Python server and is not embedded in the HTML. When enabled, chat messages and limited recent chat context are sent to the configured model provider, and usage may incur charges. The local server uses the standard library for this API request; no OpenAI SDK is required by the browser app. Do not publish the key.

## Test the app

Double-click `RUN_TESTS.bat`, or run:

```powershell
py -m unittest discover -s tests -v
```

The suite currently contains 21 automated unit and HTTP integration tests. Tests do not replace end-to-end browser testing or an independent security review.

## Project map

```text
server.py                        simple launcher entrypoint
web_server.py                    standard-library HTTP server + local API
web/index.html                   full responsive browser application
finance_tools.py                 deterministic budget and quote calculations
agent.py                         local fallback and optional model tool specifications
app.py                           alternative Streamlit UI (requires Streamlit)
requirements.txt                 notes that the recommended browser app has no dependencies
requirements-llm.txt             OpenAI SDK for alternative Streamlit UI model chat
START_BORDERWISE.bat             Windows one-click launcher
RUN_TESTS.bat                    Windows test runner
INSTALL_AND_RUN_WINDOWS.md       setup guide

tests/test_finance_tools.py      calculator tests
tests/test_agent.py              agent fallback tests
tests/test_web_server.py         local web API dispatcher tests
tests/test_http_integration.py   real local HTTP integration tests

docs/TECHNICAL_DOCUMENTATION.md architecture and calculations
docs/SECURITY_SELF_ASSESSMENT.md security controls and limitations
docs/TEST_REPORT.md              existing test report; update it with your local results
docs/EXECUTION_EVIDENCE.md       evidence and verification limitations
docs/demo_scenario_output.json   fictional scenario output
docs/GITHUB_PUBLISH.md           publishing instructions
DEMO_SCRIPT.md                   demo presentation script
PITCH_DECK.pptx                  editable pitch deck
PITCH_DECK.pdf                   PDF pitch deck
SUBMISSION_CHECKLIST.md          submission checklist
```

## Explicit limitations

This is a competition prototype, not a bank, remittance provider, credit broker, immigration adviser, or regulated financial service. It does not fetch live exchange rates, verify provider quotes, access bank accounts, store financial documents, apply for credit, submit immigration documents, or execute transfers. Prefilled figures are illustrative only. Verify current market values and official requirements independently before making real decisions.

The local fallback is rules-based, not a generative AI model. The optional model has no web-browsing capability in this prototype. The audit log is in memory and resets when the server stops. The browser checklist uses session-scoped browser storage. The server binds to `127.0.0.1` and is intended for local demonstrations.

## Future work before production

1. Add a trusted FX source with retrieval time, source attribution, and stale-data warnings.
2. Add official country-specific immigration links with last-checked dates.
3. Add read-only remittance-provider integrations only after permissions and compliance are reviewed.
4. Add robust fee models for intermediary and receiving-bank charges.
5. Add a privacy-aware persistent data layer only with explicit consent and a retention policy.
6. Add end-to-end testing, dependency scanning, rate limiting, and an independent security review.
