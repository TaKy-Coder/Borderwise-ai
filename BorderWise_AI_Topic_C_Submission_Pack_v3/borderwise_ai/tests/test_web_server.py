import os
import unittest
from unittest.mock import patch

import web_server


class WebApiTests(unittest.TestCase):
    def setUp(self):
        web_server.AUDIT_LOG.clear()

    def test_health_endpoint_does_not_expose_api_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            status, data = web_server.process_api("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertFalse(data["llm_configured"])
        self.assertNotIn("OPENAI_API_KEY", data)

    def test_budget_endpoint_returns_expected_gap(self):
        payload = {
            "currency": "EUR", "bdt_per_currency": 130, "planning_months": 12,
            "tuition_due": 3000, "housing_deposit": 1200, "visa_admin_costs": 150,
            "flight_cost": 650, "setup_costs": 500, "monthly_rent": 550,
            "monthly_utilities": 100, "monthly_food": 250, "monthly_transport": 60,
            "monthly_insurance": 120, "monthly_other": 100,
            "current_savings": 5000, "monthly_support": 300,
        }
        status, body = web_server.process_api("POST", "/api/budget", payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["total_planned_cost"], 19660.0)
        self.assertEqual(body["result"]["funding_gap"], 11060.0)
        self.assertEqual(body["result"]["funding_gap_bdt"], 1437800.0)

    def test_budget_endpoint_rejects_negative_input(self):
        status, body = web_server.process_api("POST", "/api/budget", {"tuition_due": -1})
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_transfer_endpoint_ranks_by_recipient_amount(self):
        status, body = web_server.process_api("POST", "/api/transfer", {
            "transfer_budget_bdt": 100000,
            "mid_market_bdt_per_unit": 130,
            "currency": "EUR",
            "quotes": [
                {"name": "Quote A", "fee_bdt": 500, "quote_rate": 132},
                {"name": "Quote B", "fee_bdt": 250, "quote_rate": 133},
            ],
        })
        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["best_estimated_quote"], "Quote A")
        self.assertAlmostEqual(body["result"]["quotes"][0]["recipient_amount"], 753.7879, places=3)

    def test_local_chat_does_not_need_api_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            status, body = web_server.process_api("POST", "/api/chat", {"message": "How do I compare transfer quotes?"})
        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["mode"], "local-fallback")
        self.assertIn("Transfer Comparison", body["result"]["answer"])

    def test_audit_does_not_store_message_or_financial_payload(self):
        web_server.process_api("POST", "/api/chat", {"message": "My private message with amount 123456"})
        status, body = web_server.process_api("GET", "/api/audit")
        self.assertEqual(status, 200)
        serialized = str(body)
        self.assertNotIn("private message", serialized)
        self.assertNotIn("123456", serialized)
        self.assertIn("chat_message", serialized)

    def test_unknown_api_route_returns_not_found(self):
        status, body = web_server.process_api("POST", "/api/not-a-tool", {})
        self.assertEqual(status, 404)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
