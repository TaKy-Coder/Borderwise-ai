import unittest
from finance_tools import calculate_student_budget, compare_transfer_quotes, execute_public_tool

class BudgetTests(unittest.TestCase):
    def test_budget_arithmetic(self):
        r = calculate_student_budget(currency="EUR", bdt_per_currency=130,
            tuition_due=1000, housing_deposit=500, visa_admin_costs=100,
            flight_cost=400, setup_costs=200, monthly_rent=500,
            monthly_utilities=100, monthly_food=200, monthly_transport=50,
            monthly_insurance=100, monthly_other=50, planning_months=2,
            current_savings=2000, monthly_support=300)
        self.assertEqual(r["upfront_costs"], 2200)
        self.assertEqual(r["monthly_burn"], 1000)
        self.assertEqual(r["total_planned_cost"], 4200)
        self.assertEqual(r["total_planned_funding"], 2600)
        self.assertEqual(r["funding_gap"], 1600)
        self.assertEqual(r["funding_gap_bdt"], 208000)

    def test_budget_rejects_negative(self):
        with self.assertRaises(ValueError):
            calculate_student_budget(monthly_food=-1)

    def test_zero_rate_rejected(self):
        with self.assertRaises(ValueError):
            calculate_student_budget(bdt_per_currency=0)

class QuoteTests(unittest.TestCase):
    def test_best_quote_by_recipient_amount(self):
        r = compare_transfer_quotes(transfer_budget_bdt=100000, mid_market_bdt_per_unit=130,
            currency="EUR", quotes=[
                {"name":"A", "fee_bdt":500, "quote_rate":132},
                {"name":"B", "fee_bdt":250, "quote_rate":133},
            ])
        self.assertEqual(r["best_estimated_quote"], "A")
        self.assertGreater(r["quotes"][0]["recipient_amount"], r["quotes"][1]["recipient_amount"])

    def test_quote_requires_at_least_one(self):
        with self.assertRaises(ValueError):
            compare_transfer_quotes(transfer_budget_bdt=1000, mid_market_bdt_per_unit=130, quotes=[])

    def test_disallowed_tool(self):
        with self.assertRaises(ValueError):
            execute_public_tool("send_money", {})

if __name__ == "__main__":
    unittest.main()
