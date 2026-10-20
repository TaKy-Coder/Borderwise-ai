# BorderWise AI — Test Report

## Unit test evidence

Command:

```bash
python -m unittest discover -s tests -v
```

The current suite has 21 tests across four files.

### Calculator tests (`tests/test_finance_tools.py`)

1. `test_budget_arithmetic` — verifies upfront cost, monthly burn, total plan, funding gap and BDT conversion.
2. `test_budget_rejects_negative` — rejects a negative cost.
3. `test_zero_rate_rejected` — rejects a zero FX rate.
4. `test_best_quote_by_recipient_amount` — ranks quotes by estimated recipient amount.
5. `test_disallowed_tool` — rejects a tool that is not on the allowlist.
6. `test_quote_requires_at_least_one` — rejects an empty quote list.

### Assistant tests (`tests/test_agent.py`)

7. `test_audit_event_excludes_financial_payload` — checks the minimized audit event schema.
8. `test_greeting_fallback_without_key` — checks a local-mode greeting.
9. `test_immigration_safety_response` — directs changing visa/funding requirements to official sources.

### Local web API tests (`tests/test_web_server.py`)

10. `test_health_endpoint_does_not_expose_api_key` — verifies health status doesn't return a secret.
11. `test_budget_endpoint_returns_expected_gap` — verifies the API returns the expected funding gap and BDT equivalent.
12. `test_budget_endpoint_rejects_negative_input` — validates invalid API inputs are rejected.
13. `test_transfer_endpoint_ranks_by_recipient_amount` — checks API quote ranking.
14. `test_local_chat_does_not_need_api_key` — verifies local chat works without an API key.
15. `test_audit_does_not_store_message_or_financial_payload` — checks message content and amounts are not copied into audit events.
16. `test_unknown_api_route_returns_not_found` — rejects unknown routes.

### Real HTTP integration tests (`tests/test_http_integration.py`)

17. `test_http_root_serves_application` — serves the actual browser HTML from a live local HTTP server.
18. `test_http_health` — tests the HTTP health endpoint.
19. `test_http_budget_calculation` — posts a budget over HTTP and checks the numeric result.
20. `test_http_transfer_comparison` — posts two quotes over HTTP and checks the ranking.
21. `test_http_invalid_budget_is_a_400` — confirms invalid input returns an HTTP 400 response.

**Recorded result in this build environment: 21 tests passed.** The test suite was also run after the standard-library browser interface was added.

## Live local server smoke test

The local server was started on a test port, and these checks succeeded:

- `GET /` returned the HTML interface.
- `GET /api/health` returned a healthy local-demo status.
- `POST /api/budget` returned the expected illustrative result: EUR 19,660 planned costs, EUR 8,600 planned funding, EUR 11,060 funding gap, and BDT 1,437,800 at the entered rate of BDT 130/EUR.
- JavaScript syntax was checked with `node --check` after extracting the inline script from the page.

These checks validate HTTP serving and backend requests. They do **not** replace a full interactive browser walkthrough on the submitting team's computer or an independent security review.
