"""BorderWise agent controller: optional LLM tool calling + safe deterministic fallback."""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Any
from finance_tools import public_tool_specs, execute_public_tool

SYSTEM_PROMPT = """You are BorderWise AI, a cross-border student-finance planning assistant.
Help users understand budgeting, tuition cash flow, and comparisons of transfer quotes they provide.
Rules:
- Use the provided calculator tools for calculations; do not do mental arithmetic when a tool is available.
- Treat all exchange rates, costs, transfer quotes, and sample figures as user inputs unless independently verified by a connected source (none is connected in this MVP).
- Clearly label estimates and assumptions. Never claim an exchange rate, transfer fee, banking product, or immigration requirement is current or verified unless a trusted source was actually fetched; no such web tool is available here.
- Do not provide a guarantee about visas, residence permits, admission, tax, or legal eligibility. Direct users to the relevant official authority for current requirements.
- Do not ask for or accept passwords, PINs, one-time codes, full card numbers, bank login credentials, or passport scans.
- Do not initiate payments, transfers, applications, account changes, or other external actions. This agent is read-only.
- Do not invent missing numbers. If required values are missing, ask for them or direct the user to the budget/transfer form.
- Explain results plainly and include limitations. Provide educational planning, not individualized investment, lending, or legal advice.
"""


def _local_fallback(message: str) -> str:
    m = message.lower().strip()
    if any(k in m for k in ["transfer", "remittance", "exchange rate", "fx rate", "send money"]):
        return ("I can compare transfer quotes you enter in the Transfer Comparison tab. For a fair comparison, enter the same total BDT budget, each provider's full fee, and the quoted BDT-per-EUR rate. "
                "This demo does not fetch live rates or send money. Never share bank passwords, PINs, or OTPs here.")
    if any(k in m for k in ["visa", "blocked account", "proof of funds", "residence permit", "immigration"]):
        return ("I can help you make a checklist, but I cannot confirm current visa, blocked-account, or proof-of-funds rules in this offline demo. Those rules can change. Verify the exact requirement with the destination country's official immigration authority, embassy, or consulate before paying or submitting documents.")
    if any(k in m for k in ["credit", "credit score", "credit history", "credit building", "credit card"]):
        return ("Credit-building systems differ by country and institution. Before using a credit product, ask a regulated bank or official consumer-protection authority about eligibility, reporting, interest, fees, late-payment consequences, and whether the account reports to a local credit bureau. Pay on time, avoid borrowing you cannot repay, and never share banking credentials in this chat. This demo cannot verify product terms or predict a credit score.")
    if any(k in m for k in ["budget", "afford", "cost", "tuition", "living expense", "monthly expense"]):
        return ("Use the Budget Planner tab to enter tuition due, one-time arrival costs, monthly living expenses, available savings, and family support. I'll show your estimated cash requirement and funding gap using your assumptions. Exchange rates are not live unless you connect and verify a data source.")
    if any(k in m for k in ["hello", "hi", "hey"]):
        return ("Hello! I’m BorderWise AI. I help international students plan cross-border study costs and compare transfer quotes using transparent calculations. Try the Budget Planner or Transfer Comparison tabs. No bank connection or payment execution is available in this prototype.")
    return ("I can help with student budgets, tuition cash flow, user-entered remittance quote comparisons, and financial preparation checklists. Use the planner tabs for numerical estimates. For changing exchange rates or immigration rules, verify information with an authoritative current source.")


def answer(message: str, history: list[dict[str, str]] | None = None, api_key: str | None = None, model: str | None = None) -> dict[str, Any]:
    """Answer with optional OpenAI tool calling. Falls back safely without an API key.

    User data is sent to the configured model provider only when the API key is configured
    and the user deliberately sends a message from the chat tab.
    """
    message = (message or "").strip()
    if not message:
        return {"answer": "Please enter a question.", "mode": "local-fallback", "tools_used": []}
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return {"answer": _local_fallback(message), "mode": "local-fallback", "tools_used": []}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        model = model or os.getenv("BORDERWISE_MODEL", "gpt-4.1-mini")
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            for item in history[-8:]:
                if item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
                    msgs.append({"role": item["role"], "content": item["content"][:4000]})
        msgs.append({"role": "user", "content": message[:4000]})
        tools_used: list[str] = []
        for _ in range(4):
            response = client.chat.completions.create(
                model=model,
                messages=msgs,
                tools=public_tool_specs(),
                tool_choice="auto",
                temperature=0.1,
            )
            msg = response.choices[0].message
            if not msg.tool_calls:
                return {"answer": msg.content or "I could not produce a response. Please try again.", "mode": "llm+tools", "tools_used": tools_used}
            msgs.append({"role": "assistant", "content": msg.content, "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                    result = execute_public_tool(name, args)
                    tools_used.append(name)
                    tool_content = json.dumps({"ok": True, "result": result}, ensure_ascii=False)
                except Exception as exc:
                    tool_content = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
                msgs.append({"role": "tool", "tool_call_id": tool_call.id, "content": tool_content[:12000]})
        return {"answer": "I reached the maximum tool-call limit. Please narrow the request and try again.", "mode": "llm+tools", "tools_used": tools_used}
    except Exception as exc:
        # Do not leak API keys or detailed provider errors to the user.
        return {"answer": _local_fallback(message) + "\n\n(LLM service unavailable; local help mode was used.)", "mode": "local-fallback", "tools_used": [], "internal_error_type": type(exc).__name__}


def audit_event(action: str, outcome: str) -> dict[str, str]:
    """Return a privacy-minimized in-memory event; deliberately excludes user inputs."""
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "action": action[:80],
        "outcome": outcome[:80],
        "data_policy": "No prompt, financial amounts, credentials, or document content stored in this event",
    }
