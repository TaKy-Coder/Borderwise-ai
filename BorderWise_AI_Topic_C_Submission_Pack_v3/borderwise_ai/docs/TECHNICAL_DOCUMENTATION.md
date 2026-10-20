# BorderWise AI — Technical Documentation

## 1. Purpose and scope

BorderWise implements FinTechathon Topic C: Cross-border & Student Finance Assistant. Its target users are international students and families who need a transparent view of tuition timing, initial relocation costs, recurring living expenses, available resources, and the net amount a transfer quote may deliver.

The MVP supports three core workflows: (1) calculate a funding plan, (2) compare user-provided transfer quotes, and (3) review credit-building and cross-border readiness checklists. A chat assistant provides structured help. The arithmetic is executed by deterministic Python functions and not delegated to a language model.

## 2. Architecture

```text
Student / Judge
      |
      v
Browser UI (web/index.html)
      |  HTTP JSON requests to loopback only
      v
web_server.py / server.py
      |                   |
      v                   v
finance_tools.py       agent fallback / optional model API
Budget + transfer      Local rules or Chat Completions tool loop
      |                   |
      +---------> allowlisted calculator tools
                      |
                      v
                 JSON result
                      |
                      v
          Browser results / download / audit event
```

**Components:**
- `web/index.html`: responsive, dependency-free browser interface with six navigable views: overview, budget planner, transfer comparison, readiness checklist, assistant chat, and audit log.
- `server.py`: minimal command-line entry point.
- `web_server.py`: Python standard-library HTTP server and JSON API; binds to `127.0.0.1` by default.
- `finance_tools.py`: deterministic calculator functions, numeric validation, tool schemas and allowlist.
- `agent.py`: local rules-based fallback plus shared assistant policy and tool definitions. The standard-library web server can optionally call a compatible OpenAI Chat Completions model using `urllib`.
- `app.py`: an alternative Streamlit UI; this is no longer required for the recommended browser app.
- `tests/`: calculator, assistant, API-dispatcher and real HTTP integration tests.

The recommended browser app has no third-party Python runtime dependencies. No database, bank API, remittance API, identity verification service, immigration data feed, or payment API is connected.

## 3. Core algorithms

### Student budget

Let:
- `U` = tuition currently due + housing deposit + admin/visa costs + flight + setup costs.
- `M` = rent + utilities/phone + food + transport + insurance + other monthly costs.
- `H` = user-selected planning horizon in months, constrained to 1–60 in the core function (the browser exposes 1–60).
- `S` = available current savings.
- `F` = expected family support per month.
- `R` = user-entered BDT value of one unit of the destination currency.

Then:
- Total planned cost = `U + (M × H)`
- Planned funding = `S + (F × H)`
- Funding gap = `max(0, total planned cost − planned funding)`
- Surplus = `max(0, planned funding − total planned cost)`
- BDT funding gap = `funding gap × R`

The model treats support as arriving each month rather than as cash available immediately. This timing assumption is explicit in the output. It is a planning estimate, not a forecast or proof-of-funds determination.

### Transfer quote comparison

Inputs are a total BDT budget `B` (including fees), user-provided flat fee `fᵢ`, provider quoted rate `rᵢ` measured in BDT per unit of recipient currency, and user-provided reference rate `m`.

For quote `i`:
- Amount available for conversion = `max(0, B − fᵢ)`
- Estimated recipient amount = `max(0, B − fᵢ) / rᵢ`
- Reference amount = `B / m`
- Estimated difference vs reference value in BDT = `max(0, reference amount − recipient amount) × m`

Quotes are ranked by estimated recipient amount. This simplified model does not include percentage fees, intermediary fees, receiving-bank fees, taxes, settlement time, limits, eligibility, rate-lock expiry, or provider reliability. It compares entered figures only and does not verify or endorse a provider.

## 4. Assistant and tool calling

When no API key is configured, the assistant uses a local keyword-based helper. This mode is useful offline but is not a generative AI model. If `OPENAI_API_KEY` is set, the standard-library web server can send the prompt and limited recent chat history to the configured Chat Completions model. The model can request only `calculate_student_budget` and `compare_transfer_quotes` tools. Tool names are checked against an explicit allowlist; calculator inputs are validated; the tool loop is limited to four rounds.

Provider/network errors return a local fallback response without exposing provider error details or credentials to the browser. No `send_money`, account-login, email, document-submission, or other external write tool exists.

## 5. Data flow and privacy

- The browser sends calculator values to the local Python server using JSON.
- The web server binds to `127.0.0.1`, which is intended for use on the same computer; it is not configured as a public deployment.
- Budget and comparison results are returned to the browser and may be downloaded as JSON by the user.
- Checklist selections are held in browser `sessionStorage` only.
- Audit events intentionally exclude user prompts, budget amounts and document content. Audit events are held in server memory and reset when the server stops.
- If model mode is enabled, current chat text and limited recent chat history are sent to the configured model provider. This must be disclosed to users; provider retention practices are outside this application's control.
- API keys are read from the server environment and are not embedded in `web/index.html`.

## 6. Error handling and validation

- Negative, non-finite, non-numeric and zero FX-rate inputs are rejected where invalid.
- Planning months are bounded.
- Empty quote arrays, invalid quote rates and unknown tools are rejected.
- Request JSON is size-limited to 1 MB and validated.
- Model-provider failures fall back to local help instead of enabling an unapproved action.
- Errors returned to browser users are intentionally general for internal errors; terminal logs do not print request bodies.

## 7. Run and test

Recommended Windows entry point: double-click `START_BORDERWISE.bat`. The app opens at `http://127.0.0.1:8501`; keep the terminal window open. No package installation is required beyond Python 3.10+.

Run all unit tests with:

```bash
python -m unittest discover -s tests -v
```

The current suite has 21 tests across four test files. They cover arithmetic, validation, quote ranking, tool restrictions, fallback responses, audit minimization, and the local API dispatcher. They are not a full security audit or proof of complete browser end-to-end testing.

## 8. Limitations and roadmap

This version uses illustrative defaults, user-entered exchange rates, and no live external data source. It is not suitable for initiating transfers or relying on legal/immigration rules. Appropriate next steps include source-backed FX retrieval with timestamps, official government links, extended provider fee models, end-to-end browser tests, dependency scanning, rate limiting, production deployment isolation, and a privacy/retention review before adding persistence.
