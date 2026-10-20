"""Deterministic, auditable calculators used by BorderWise AI.

All amounts are user-provided assumptions or clearly labeled demo values.
No live FX, bank, immigration, or payment-system integrations are included.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Iterable
import math


def _nonnegative(name: str, value: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return value


def calculate_student_budget(
    *,
    currency: str = "EUR",
    bdt_per_currency: float = 130.0,
    tuition_due: float = 0,
    housing_deposit: float = 0,
    visa_admin_costs: float = 0,
    flight_cost: float = 0,
    setup_costs: float = 0,
    monthly_rent: float = 0,
    monthly_utilities: float = 0,
    monthly_food: float = 0,
    monthly_transport: float = 0,
    monthly_insurance: float = 0,
    monthly_other: float = 0,
    planning_months: int = 12,
    current_savings: float = 0,
    monthly_support: float = 0,
) -> dict[str, Any]:
    """Calculate a transparent student-finance planning estimate.

    The planning horizon is user selected. Family support is modeled as arriving
    every month of the horizon; it is not treated as upfront cash.
    """
    currency = str(currency or "EUR").upper().strip()
    if not currency.isalpha() or not 3 <= len(currency) <= 5:
        raise ValueError("currency must be a currency code such as EUR")
    bdt_per_currency = _nonnegative("bdt_per_currency", bdt_per_currency)
    if bdt_per_currency <= 0:
        raise ValueError("bdt_per_currency must be greater than zero")
    if isinstance(planning_months, bool) or int(planning_months) != planning_months or not 1 <= int(planning_months) <= 60:
        raise ValueError("planning_months must be an integer from 1 to 60")
    planning_months = int(planning_months)

    upfront_names = ["tuition_due", "housing_deposit", "visa_admin_costs", "flight_cost", "setup_costs"]
    monthly_names = ["monthly_rent", "monthly_utilities", "monthly_food", "monthly_transport", "monthly_insurance", "monthly_other"]
    inputs: dict[str, float] = {}
    for name in upfront_names + monthly_names + ["current_savings", "monthly_support"]:
        inputs[name] = _nonnegative(name, locals()[name])

    upfront = sum(inputs[n] for n in upfront_names)
    monthly_burn = sum(inputs[n] for n in monthly_names)
    planned_cost = upfront + monthly_burn * planning_months
    funding = inputs["current_savings"] + inputs["monthly_support"] * planning_months
    gap = max(0.0, planned_cost - funding)
    surplus = max(0.0, funding - planned_cost)
    result = {
        "currency": currency,
        "planning_months": planning_months,
        "assumptions": {
            "fx_rate": f"1 {currency} = {bdt_per_currency:,.4f} BDT (user-entered assumption; not live FX)",
            "family_support_timing": "Modeled as monthly inflows throughout the planning horizon",
            "scope": "Planning estimate only; amounts and fees must be verified independently",
        },
        "upfront_costs": round(upfront, 2),
        "monthly_burn": round(monthly_burn, 2),
        "living_cost_over_horizon": round(monthly_burn * planning_months, 2),
        "total_planned_cost": round(planned_cost, 2),
        "current_savings": round(inputs["current_savings"], 2),
        "planned_family_support": round(inputs["monthly_support"] * planning_months, 2),
        "total_planned_funding": round(funding, 2),
        "funding_gap": round(gap, 2),
        "surplus": round(surplus, 2),
        "average_monthly_gap": round(gap / planning_months, 2),
        "total_planned_cost_bdt": round(planned_cost * bdt_per_currency, 2),
        "funding_gap_bdt": round(gap * bdt_per_currency, 2),
        "average_monthly_gap_bdt": round((gap / planning_months) * bdt_per_currency, 2),
    }
    return result


def compare_transfer_quotes(
    *,
    transfer_budget_bdt: float,
    mid_market_bdt_per_unit: float,
    quotes: Iterable[dict[str, Any]],
    currency: str = "EUR",
) -> dict[str, Any]:
    """Compare user-entered transfer quotes; do not fetch or execute transfers."""
    budget = _nonnegative("transfer_budget_bdt", transfer_budget_bdt)
    mid = _nonnegative("mid_market_bdt_per_unit", mid_market_bdt_per_unit)
    if budget <= 0 or mid <= 0:
        raise ValueError("Transfer budget and reference rate must be greater than zero")
    evaluated = []
    for idx, q in enumerate(quotes, start=1):
        name = str(q.get("name", f"Quote {idx}"))[:80]
        fee = _nonnegative(f"{name} fee_bdt", q.get("fee_bdt", 0))
        rate = _nonnegative(f"{name} quote_rate", q.get("quote_rate", 0))
        if rate <= 0:
            raise ValueError(f"{name}: quoted BDT per {currency} must be greater than zero")
        if fee >= budget:
            received = 0.0
        else:
            received = (budget - fee) / rate
        fair_target = budget / mid
        opportunity_cost = max(0.0, fair_target - received) * mid
        evaluated.append({
            "name": name,
            "fee_bdt": round(fee, 2),
            "quoted_bdt_per_unit": round(rate, 6),
            "budget_bdt": round(budget, 2),
            "amount_after_fee_bdt": round(max(0.0, budget - fee), 2),
            "recipient_amount": round(received, 4),
            "recipient_currency": currency.upper(),
            "effective_bdt_per_unit": round(budget / received, 6) if received > 0 else None,
            "estimated_cost_vs_mid_market_bdt": round(opportunity_cost, 2),
            "reference_amount_at_mid_market": round(fair_target, 4),
        })
    if not evaluated:
        raise ValueError("Provide at least one transfer quote")
    ranked = sorted(evaluated, key=lambda x: x["recipient_amount"], reverse=True)
    return {
        "currency": currency.upper(),
        "warning": "Comparison uses only quotes entered by the user. It does not verify providers, fees, exchange rates, transfer speed, or eligibility, and it does not send money.",
        "ranking_basis": f"Highest estimated recipient amount in {currency.upper()} for the same total BDT budget",
        "best_estimated_quote": ranked[0]["name"],
        "quotes": ranked,
    }


def public_tool_specs() -> list[dict[str, Any]]:
    """Small LLM tool set with no payments, account access, or external writes."""
    return [
        {
            "type": "function",
            "function": {
                "name": "calculate_student_budget",
                "description": "Calculate a student budget from user-provided inputs. Never invent missing values; ask user to use the budget form if details are missing.",
                "parameters": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "currency": {"type": "string", "description": "Destination spending currency, e.g. EUR"},
                        "bdt_per_currency": {"type": "number", "description": "User-entered BDT per one unit of destination currency; not live FX"},
                        "tuition_due": {"type": "number"}, "housing_deposit": {"type": "number"},
                        "visa_admin_costs": {"type": "number"}, "flight_cost": {"type": "number"},
                        "setup_costs": {"type": "number"}, "monthly_rent": {"type": "number"},
                        "monthly_utilities": {"type": "number"}, "monthly_food": {"type": "number"},
                        "monthly_transport": {"type": "number"}, "monthly_insurance": {"type": "number"},
                        "monthly_other": {"type": "number"}, "planning_months": {"type": "integer"},
                        "current_savings": {"type": "number"}, "monthly_support": {"type": "number"},
                    },
                    "required": ["currency", "bdt_per_currency", "tuition_due", "housing_deposit", "visa_admin_costs", "flight_cost", "setup_costs", "monthly_rent", "monthly_utilities", "monthly_food", "monthly_transport", "monthly_insurance", "monthly_other", "planning_months", "current_savings", "monthly_support"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compare_transfer_quotes",
                "description": "Compare transfer quotes explicitly supplied by the user. This never verifies providers or initiates a transaction.",
                "parameters": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "transfer_budget_bdt": {"type": "number"},
                        "mid_market_bdt_per_unit": {"type": "number", "description": "User-provided reference rate, not a live quote"},
                        "currency": {"type": "string"},
                        "quotes": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {"name": {"type": "string"}, "fee_bdt": {"type": "number"}, "quote_rate": {"type": "number"}}, "required": ["name", "fee_bdt", "quote_rate"]}},
                    },
                    "required": ["transfer_budget_bdt", "mid_market_bdt_per_unit", "quotes", "currency"],
                },
            },
        },
    ]


def execute_public_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "calculate_student_budget":
        return calculate_student_budget(**arguments)
    if name == "compare_transfer_quotes":
        return compare_transfer_quotes(**arguments)
    raise ValueError("Tool is not on the allowlist")
