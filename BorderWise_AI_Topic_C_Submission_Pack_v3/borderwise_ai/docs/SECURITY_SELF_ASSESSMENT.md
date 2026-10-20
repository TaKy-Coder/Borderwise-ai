# BorderWise AI — Security Self-Assessment

## Scope

This assessment describes the submitted prototype only. It is not a third-party audit, penetration test, legal opinion, or certification.

## Permission tiers

| Tier | Status | Capability |
|---|---|---|
| Tier 0 — Read-only calculations | Implemented | Calculate plans and compare user-entered quotes; export JSON results. |
| Tier 1 — Informational assistance | Implemented | Provide general checklists and bounded natural-language help. |
| Tier 2 — External read access | Not implemented | Live FX feeds, provider APIs, official immigration pages, account balances. Requires source validation and explicit scope. |
| Tier 3 — External write actions | Not implemented | Transfers, account changes, emails, credit applications or immigration submissions. Would require strong authentication, explicit user review and transaction-specific confirmation. |

## Controls implemented

1. **Least privilege:** no bank, email, browser automation, filesystem, or payment tools are exposed to the model.
2. **Tool allowlist:** only two named calculator tools can execute from model requests; unknown tool names fail closed.
3. **Input validation:** numeric inputs reject invalid negative values and invalid rates; planning horizon is bounded.
4. **Bounded loop:** tool-calling iteration count is capped.
5. **No credential collection:** system instructions tell the agent not to request passwords, PINs, OTPs, card numbers, or bank credentials.
6. **No claim of live data:** exchange rates and quotes are explicitly user-provided; immigration requirements must be checked with official authorities.
7. **Privacy-minimized audit:** local event log does not include prompts, personal documents or money amounts.
8. **Secrets hygiene:** `.env` and secret files are excluded via `.gitignore`; API keys should be configured outside source control.
9. **Manual user control:** all displayed form inputs and outputs are reviewable; no financial action can be triggered.
10. **Local binding:** the recommended standard-library server binds to `127.0.0.1` by default and limits JSON request bodies to 1 MB. This is intended for a local demo, not public hosting.

## Known risks and mitigations

| Risk | Impact | Current mitigation | Remaining work |
|---|---|---|---|
| Outdated or incorrect FX quote | Budget or comparison error | No live rate claim; input is labeled assumption | Add source, timestamp, stale-rate detection and provider-side verification. |
| Simplified transfer fee model | Misranking if hidden fees exist | Explicit warning and limited formula | Model percentage, intermediary, recipient-bank and tax fees; test with providers. |
| LLM hallucination | Misleading financial or immigration answer | Prompt boundaries and calculator tools; no official-source retrieval claim | Add citations from authoritative sources, retrieval evaluation and red-team tests. |
| Prompt injection in user chat | Model may attempt to exceed role | Tools are constrained; no side-effect tools exist | Additional prompt-injection tests and structured output validation. |
| API data disclosure | User chat sent to a third-party model provider | API integration optional; local mode works without key | Add explicit opt-in, data minimization UI, provider retention review. |
| API key leakage | Unauthorized API use | Environment-variable pattern and `.gitignore` | Use managed secrets and key rotation in deployment. |
| Shared/public demo deployment | Other users may view or abuse session/app | Server binds to localhost by default; audit memory is local | Authentication, rate limits, per-user session isolation and monitoring before public deployment. |
| Incorrect country-specific credit guidance | Financial harm | Only general checklist; no product recommendation or score prediction | Research per-country rules and consult local regulatory requirements. |
| Overreliance on budget gap | User treats estimate as guaranteed proof of funds | Scope disclaimer; chosen horizon and assumed FX explicit | Add scenario ranges, contingency buffers and official requirements links. |
| Dependency vulnerabilities | Code compromise | Dependencies listed and bounded | Pin tested versions and run a dependency vulnerability scan. |

## Risk boundaries

**Not allowed in this version:** initiating or approving a money transfer; making credit decisions; logging in to a bank account; collecting credentials or identity documents; submitting immigration forms; claiming guaranteed visa eligibility; or representing demo values as current market values.

## Pre-demo checklist

- [ ] Use only fictional/demo figures or obtain consent before entering any personal financial estimates.
- [ ] Do not enter real credentials, OTPs, card data, or passport images.
- [ ] Keep API keys out of slides, screen recordings, logs and repository history.
- [ ] Show that the exchange rate is a user-entered assumption.
- [ ] Demonstrate the safe response to questions about visa / proof-of-funds rules.
- [ ] Verify downloadable output contains only the intended demo scenario.
- [ ] Explain that this is a prototype and not a payment service or official adviser.
