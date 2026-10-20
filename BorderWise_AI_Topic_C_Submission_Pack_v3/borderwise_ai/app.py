from __future__ import annotations
import json
import os
import streamlit as st
from finance_tools import calculate_student_budget, compare_transfer_quotes
from agent import answer, audit_event

st.set_page_config(page_title="BorderWise AI", page_icon="🌍", layout="wide")

# Compact custom styling, using standard Streamlit primitives only.
st.markdown("""
<style>
.block-container {padding-top: 1.35rem; max-width: 1180px;}
.hero {padding: 1.25rem 1.5rem; border-radius: 18px; color: white; background: linear-gradient(120deg,#102a43,#145374 60%,#168aad); margin-bottom: 1rem;}
.hero h1 {margin-bottom:.25rem; font-size:2.25rem;}
.hero p {margin:.1rem 0; color:#e5f3fa;}
.small-note {font-size:.85rem; color:#64748b;}
div[data-testid="stMetric"] {border:1px solid #dbe4ed; border-radius:12px; padding:12px; background:rgba(127,164,190,.05);}
</style>
""", unsafe_allow_html=True)

if "audit" not in st.session_state:
    st.session_state.audit = []
if "chat" not in st.session_state:
    st.session_state.chat = []
if "latest_budget" not in st.session_state:
    st.session_state.latest_budget = None

st.markdown("""
<div class="hero">
  <h1>🌍 BorderWise AI</h1>
  <p><b>Cross-border & Student Finance Assistant</b></p>
  <p>Plan your study-abroad budget, compare transfer quotes, and understand your funding gap — with transparent calculations.</p>
</div>
""", unsafe_allow_html=True)

st.warning("Prototype / demo mode. Exchange rates are user-entered assumptions, not live quotes. No bank connection, credit decision, visa verification, or money transfer is performed.")
with st.sidebar:
    st.subheader("BorderWise controls")
    st.caption("Competition track: Topic C")
    api_ready = bool(os.getenv("OPENAI_API_KEY"))
    st.write("AI mode:", "LLM + safe calculator tools" if api_ready else "Local demo mode (no API key)")
    st.write("Permissions: read-only calculations")
    st.divider()
    st.markdown("**Privacy rule**")
    st.caption("Never enter passwords, PINs, OTPs, full card numbers, bank credentials, or passport scans.")
    st.divider()
    st.markdown("**Need official requirements?**")
    st.caption("Visa and proof-of-funds requirements change. Verify with the relevant official authority before making decisions.")

tabs = st.tabs(["Budget Planner", "Transfer Comparison", "Credit & Readiness", "Ask BorderWise", "Audit & Demo"])

with tabs[0]:
    st.subheader("Student budget planner")
    st.caption("Enter estimates in the destination currency. The starter profile is illustrative; replace it with your own figures.")
    with st.form("budget_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            currency = st.selectbox("Destination spending currency", ["EUR", "GBP", "USD", "CAD", "AUD"], index=0)
            fx = st.number_input("Assumed BDT per 1 unit", min_value=0.0001, value=130.0, step=1.0, format="%.4f", help="Demo assumption only; enter a current, verified rate yourself.")
            months = st.slider("Planning horizon (months)", min_value=1, max_value=24, value=12)
            tuition = st.number_input("Tuition due within this plan", min_value=0.0, value=3000.0, step=250.0)
            deposit = st.number_input("Housing deposit / initial rent", min_value=0.0, value=1200.0, step=100.0)
        with c2:
            visa_admin = st.number_input("Visa / admin costs", min_value=0.0, value=150.0, step=25.0)
            flight = st.number_input("Flight cost", min_value=0.0, value=650.0, step=50.0)
            setup = st.number_input("Other setup costs", min_value=0.0, value=500.0, step=50.0)
            rent = st.number_input("Monthly rent", min_value=0.0, value=550.0, step=50.0)
            utilities = st.number_input("Monthly utilities / phone", min_value=0.0, value=100.0, step=10.0)
        with c3:
            food = st.number_input("Monthly food", min_value=0.0, value=250.0, step=25.0)
            transport = st.number_input("Monthly transport", min_value=0.0, value=60.0, step=10.0)
            insurance = st.number_input("Monthly insurance", min_value=0.0, value=120.0, step=10.0)
            other = st.number_input("Other monthly costs", min_value=0.0, value=100.0, step=10.0)
            savings = st.number_input("Available savings", min_value=0.0, value=5000.0, step=250.0)
            support = st.number_input("Expected family support per month", min_value=0.0, value=300.0, step=50.0)
        submitted = st.form_submit_button("Calculate my plan", type="primary", use_container_width=True)
    if submitted:
        try:
            result = calculate_student_budget(
                currency=currency, bdt_per_currency=fx,
                tuition_due=tuition, housing_deposit=deposit, visa_admin_costs=visa_admin,
                flight_cost=flight, setup_costs=setup, monthly_rent=rent,
                monthly_utilities=utilities, monthly_food=food, monthly_transport=transport,
                monthly_insurance=insurance, monthly_other=other, planning_months=months,
                current_savings=savings, monthly_support=support,
            )
            st.session_state.latest_budget = result
            st.session_state.audit.append(audit_event("budget_calculation", "success"))
        except Exception as exc:
            st.error(str(exc))
    result = st.session_state.latest_budget
    if result:
        st.divider()
        st.subheader("Your estimate")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total planned cost", f'{result["total_planned_cost"]:,.2f} {result["currency"]}')
        m2.metric("Monthly living cost", f'{result["monthly_burn"]:,.2f} {result["currency"]}')
        m3.metric("Funding gap", f'{result["funding_gap"]:,.2f} {result["currency"]}')
        m4.metric("Gap in BDT", f'৳{result["funding_gap_bdt"]:,.0f}')
        st.progress(min(1.0, result["total_planned_funding"] / result["total_planned_cost"]) if result["total_planned_cost"] else 1.0)
        st.caption(f'Planned funding covers {min(100, result["total_planned_funding"] / result["total_planned_cost"] * 100 if result["total_planned_cost"] else 100):.1f}% of estimated plan. Assumed rate: {result["assumptions"]["fx_rate"]}.')
        with st.expander("Calculation details and assumptions"):
            st.json(result)
        st.download_button("Download budget summary (JSON)", data=json.dumps(result, indent=2), file_name="borderwise_budget_summary.json", mime="application/json")

with tabs[1]:
    st.subheader("Compare transfer quotes")
    st.caption("Use quotes you independently obtained for the same transfer budget. Comparison is mathematical, not an endorsement or payment instruction.")
    with st.form("transfer_form"):
        a, b = st.columns(2)
        with a:
            budget_bdt = st.number_input("Total available budget (BDT, including fees)", min_value=1.0, value=100000.0, step=5000.0)
            reference_fx = st.number_input("Reference mid-market rate (BDT per EUR)", min_value=0.0001, value=130.0, step=1.0, format="%.4f", help="User-provided reference only; not fetched live.")
        with b:
            currency2 = st.selectbox("Recipient currency", ["EUR", "GBP", "USD", "CAD", "AUD"], index=0, key="transfer_currency")
            st.caption("For a simplified comparison, flat fees are paid from the total budget before currency conversion.")
        st.markdown("**Quote A**")
        x1, x2, x3 = st.columns(3)
        with x1: name_a = st.text_input("Provider / quote label", "Quote A")
        with x2: fee_a = st.number_input("Total fee (BDT)", min_value=0.0, value=500.0, step=50.0, key="fee_a")
        with x3: rate_a = st.number_input(f"Quoted BDT per {currency2}", min_value=0.0001, value=132.0, step=0.5, format="%.4f", key="rate_a")
        st.markdown("**Quote B**")
        y1, y2, y3 = st.columns(3)
        with y1: name_b = st.text_input("Provider / quote label", "Quote B")
        with y2: fee_b = st.number_input("Total fee (BDT)", min_value=0.0, value=250.0, step=50.0, key="fee_b")
        with y3: rate_b = st.number_input(f"Quoted BDT per {currency2}", min_value=0.0001, value=133.0, step=0.5, format="%.4f", key="rate_b")
        compare = st.form_submit_button("Compare quotes", type="primary", use_container_width=True)
    if compare:
        try:
            comparison = compare_transfer_quotes(transfer_budget_bdt=budget_bdt, mid_market_bdt_per_unit=reference_fx, currency=currency2, quotes=[{"name": name_a, "fee_bdt": fee_a, "quote_rate": rate_a}, {"name": name_b, "fee_bdt": fee_b, "quote_rate": rate_b}])
            st.session_state.transfer_result = comparison
            st.session_state.audit.append(audit_event("transfer_quote_comparison", "success"))
        except Exception as exc:
            st.error(str(exc))
    comparison = st.session_state.get("transfer_result")
    if comparison:
        st.divider()
        st.success(f'Highest estimated recipient amount: {comparison["best_estimated_quote"]}')
        for quote in comparison["quotes"]:
            with st.container(border=True):
                st.markdown(f'**{quote["name"]}**')
                c1, c2, c3 = st.columns(3)
                c1.metric("Recipient receives", f'{quote["recipient_amount"]:,.2f} {quote["recipient_currency"]}')
                c2.metric("Fee", f'৳{quote["fee_bdt"]:,.2f}')
                c3.metric("Estimated cost vs reference", f'৳{quote["estimated_cost_vs_mid_market_bdt"]:,.2f}')
                st.caption(f'Quoted rate: {quote["quoted_bdt_per_unit"]:,.4f} BDT per {quote["recipient_currency"]}. Effective rate: {quote["effective_bdt_per_unit"]}.')
        st.info(comparison["warning"])
        st.download_button("Download comparison (JSON)", data=json.dumps(comparison, indent=2), file_name="borderwise_transfer_comparison.json", mime="application/json")

with tabs[2]:
    st.subheader("Credit-building and cross-border readiness")
    st.caption("A general educational checklist. It is not country-specific financial or legal advice, and the app does not recommend or open credit products.")
    left, right = st.columns(2)
    with left:
        st.markdown("**Before choosing a credit product**")
        for item in [
            "Confirm eligibility for international students with a regulated bank or official provider.",
            "Ask whether the product reports to a local credit bureau and what information is reported.",
            "Compare interest, annual/monthly fees, foreign-exchange markup, late fees, and cash-advance costs.",
            "Understand payment dates, minimum payments, grace periods, and consequences of missed payments.",
            "Borrow only what you can repay; a debit card or basic account may be sufficient for daily spending.",
        ]:
            st.checkbox(item, key="credit_" + str(abs(hash(item))))
    with right:
        st.markdown("**Cross-border readiness checklist**")
        for item in [
            "Keep a tuition invoice and written payment deadline from the institution.",
            "Obtain transfer quotes directly from providers and confirm all fees and recipient amount.",
            "Use a named reference exchange rate and record when and where it was checked.",
            "Verify visa / proof-of-funds rules through the relevant official immigration authority.",
            "Keep receipts and transfer confirmations; never share PINs or OTPs with an agent.",
        ]:
            st.checkbox(item, key="ready_" + str(abs(hash(item))))
    st.info("Credit history, eligibility, and immigration rules vary by country and provider. BorderWise does not predict credit scores, guarantee eligibility, or verify official requirements in this version.")

with tabs[3]:
    st.subheader("Ask BorderWise")
    st.caption("For general questions use chat. For reliable calculations, enter numbers in the planner forms and inspect the calculation details.")
    for item in st.session_state.chat:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    prompt = st.chat_input("Ask about budgeting, transfer quotes, or financial preparation...")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history = st.session_state.chat[:-1]
                response = answer(prompt, history=history)
                st.markdown(response["answer"])
                if response.get("tools_used"):
                    st.caption("Tools used: " + ", ".join(response["tools_used"]))
                else:
                    st.caption("Mode: " + response.get("mode", "local"))
        st.session_state.chat.append({"role": "assistant", "content": response["answer"]})
        st.session_state.audit.append(audit_event("chat_message", response.get("mode", "completed")))

with tabs[4]:
    st.subheader("Audit log and demo checklist")
    st.markdown("This local log records event type and outcome only. It intentionally does not store prompts, currency amounts, or sensitive documents.")
    if st.session_state.audit:
        st.dataframe(st.session_state.audit, use_container_width=True, hide_index=True)
        st.download_button("Download audit log (JSON)", data=json.dumps(st.session_state.audit, indent=2), file_name="borderwise_audit_log.json", mime="application/json")
    else:
        st.info("No actions logged yet. Run a budget estimate or quote comparison to generate local execution evidence.")
    st.divider()
    st.markdown("**Suggested live demo**")
    st.markdown("1. Build a 12-month budget using the illustrative profile.  2. Change the assumed FX rate and observe the BDT gap.  3. Compare two manually entered remittance quotes.  4. Ask about visa/proof-of-funds requirements and show the safety response.  5. Download a JSON result and show the privacy-minimized audit entry.")
    st.caption("All example values are fictional demo inputs and are not intended to represent actual country living costs, current market rates, or official immigration requirements.")

st.divider()
st.caption("BorderWise AI · FinTechathon 2026 · Topic C · Prototype only, no financial institution affiliation implied")
