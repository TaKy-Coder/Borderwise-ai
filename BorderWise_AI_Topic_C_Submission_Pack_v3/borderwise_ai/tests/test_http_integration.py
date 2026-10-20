"""Real HTTP integration tests for the local browser app."""
import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import web_server


class QuietHandler(web_server.BorderWiseHandler):
    def log_message(self, format, *args):
        pass


class HttpIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        web_server.AUDIT_LOG.clear()

    def get_json(self, path):
        with urlopen(self.base + path, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def post_json(self, path, data):
        req = Request(
            self.base + path,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=2) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_http_root_serves_application(self):
        with urlopen(self.base + "/", timeout=2) as response:
            html = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("BorderWise AI", html)
            self.assertIn('id="budget-form"', html)
            self.assertIn('id="chat-form"', html)

    def test_http_health(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            status, body = self.get_json("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertFalse(body["llm_configured"])

    def test_http_budget_calculation(self):
        payload = {
            "currency": "EUR", "bdt_per_currency": 130, "planning_months": 12,
            "tuition_due": 3000, "housing_deposit": 1200, "visa_admin_costs": 150,
            "flight_cost": 650, "setup_costs": 500, "monthly_rent": 550,
            "monthly_utilities": 100, "monthly_food": 250, "monthly_transport": 60,
            "monthly_insurance": 120, "monthly_other": 100,
            "current_savings": 5000, "monthly_support": 300,
        }
        status, body = self.post_json("/api/budget", payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["funding_gap"], 11060.0)
        self.assertEqual(body["result"]["funding_gap_bdt"], 1437800.0)

    def test_http_transfer_comparison(self):
        payload = {
            "transfer_budget_bdt": 100000,
            "mid_market_bdt_per_unit": 130,
            "currency": "EUR",
            "quotes": [
                {"name": "Quote A", "fee_bdt": 500, "quote_rate": 132},
                {"name": "Quote B", "fee_bdt": 250, "quote_rate": 133},
            ],
        }
        status, body = self.post_json("/api/transfer", payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["best_estimated_quote"], "Quote A")

    def test_http_invalid_budget_is_a_400(self):
        status, body = self.post_json("/api/budget", {"tuition_due": -1})
        self.assertEqual(status, 400)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
