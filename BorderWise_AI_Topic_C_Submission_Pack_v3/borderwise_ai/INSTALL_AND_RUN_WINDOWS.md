# Start BorderWise AI on Windows (no pip installation needed)

## Easiest method

1. Extract the full ZIP archive.
2. Make sure Python 3.10 or newer is installed.
3. Open the extracted `borderwise_ai` folder.
4. Double-click `START_BORDERWISE.bat`.
5. A browser should open at `http://127.0.0.1:8501`.
6. Keep the black terminal window open while using the app. Close the app with **Ctrl+C** in that terminal.

The browser version in `web/` uses the Python standard library only. It does not need Streamlit, OpenAI's Python package, or any `pip install` step. Internet access is not needed for local mode.

## Test the application

Double-click `RUN_TESTS.bat`, or open PowerShell in this folder and run:

```powershell
py -m unittest discover -s tests -v
```

The tests cover calculation logic and local API behavior. They do not establish an independent security audit.

## Optional model-powered chat

Without an API key, all calculators work and chat uses a local rules-based helper. To enable model-powered chat, create an API key with the model provider and set it in the same PowerShell window before starting the server:

```powershell
$env:OPENAI_API_KEY="YOUR_ACTUAL_API_KEY"
$env:BORDERWISE_MODEL="gpt-4.1-mini"
py server.py
```

The default web app keeps the key on the Python server, not in browser JavaScript. When model mode is enabled, chat prompts and limited recent chat context are sent to the configured provider, and API charges may apply. Never publish the key. No live FX, bank connections, or payment functionality are included.

## Notes

- The local server binds to `127.0.0.1`, not the public network.
- This browser app does not persist audit records after the server stops.
- Checklist selections are stored only for the current browser session.
- Rates, costs, and transfer quotes are assumptions supplied by the user.
- Verify immigration and proof-of-funds requirements using official sources.
