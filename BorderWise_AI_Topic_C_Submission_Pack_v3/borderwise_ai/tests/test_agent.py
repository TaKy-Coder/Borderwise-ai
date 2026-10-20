import os
import unittest
from unittest.mock import patch
from agent import answer, audit_event

class AgentFallbackTests(unittest.TestCase):
    def test_greeting_fallback_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            result = answer("Hello BorderWise", api_key="")
        self.assertEqual(result["mode"], "local-fallback")
        self.assertIn("BorderWise", result["answer"])

    def test_immigration_safety_response(self):
        with patch.dict(os.environ, {}, clear=True):
            result = answer("What are current visa proof of funds rules?", api_key="")
        self.assertIn("official", result["answer"].lower())
        self.assertIn("cannot confirm", result["answer"].lower())

    def test_audit_event_excludes_financial_payload(self):
        event = audit_event("budget_calculation", "success")
        self.assertNotIn("amount", " ".join(event.keys()).lower())
        self.assertNotIn("prompt", " ".join(event.keys()).lower())
        self.assertIn("data_policy", event)

if __name__ == "__main__":
    unittest.main()
