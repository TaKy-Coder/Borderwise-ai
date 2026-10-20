# BorderWise AI — Execution Evidence

## 1. Automated tests

The recorded test output is in `../tests_output.txt`. It contains 21 passing tests covering arithmetic, invalid inputs, quote ranking, tool allowlisting, local fallback behavior, immigration-rule caution, audit minimization, and web API behavior.

## 2. Local server smoke test

In the build environment, the standard-library server (`server.py`) was started on a local test port. The root route returned the browser HTML, the health endpoint returned the expected local-demo status, and the budget endpoint returned the expected numerical output for the illustrative test profile.

For the demonstration profile, the output was a total planned cost of EUR 19,660, planned funding of EUR 8,600, and a funding gap of EUR 11,060, equivalent to BDT 1,437,800 under the entered assumption of BDT 130/EUR. These are fictional values, not a live quote or a student's real financial plan.

## 3. Simulated scenario

`demo_scenario_output.json` is a reproducible illustrative scenario with fictional budget inputs and fictional transfer quote labels. It does not represent a real account, real provider, verified exchange rate, or actual transfer. `external_side_effects` is `false`.

## 4. Verification limits

The browser interface itself uses standard-library Python to serve a responsive HTML/JavaScript page and no extra pip dependency. The backend smoke checks and JavaScript syntax check passed. A complete manual interactive browser walkthrough, a captured submission video, live exchange-rate testing, and an independent security audit have not been completed in this environment. The team should run the application on the actual presentation computer and capture genuine evidence before claiming full end-to-end verification.
