import unittest
from decimal import Decimal

from app.finance import paper_fill


class PaperFillTests(unittest.TestCase):
    def test_buy_limit_fills_at_ask_and_fee_is_exact_decimal(self):
        result = paper_fill(side="BUY", quantity=Decimal("0.010"), limit_price=Decimal("63000"),
                            bid=Decimal("62430.25"), ask=Decimal("62448.20"), available_cash=Decimal("100000"))
        self.assertEqual(result["status"], "FILLED")
        self.assertEqual(result["fill_price"], Decimal("62448.20"))
        self.assertEqual(result["notional"], Decimal("624.48"))
        self.assertEqual(result["fee"], Decimal("1.00"))

    def test_unmarketable_limit_does_not_fill(self):
        result = paper_fill(side="BUY", quantity=Decimal("0.01"), limit_price=Decimal("62000"),
                            bid=Decimal("62430"), ask=Decimal("62448"), available_cash=Decimal("100000"))
        self.assertEqual(result["status"], "OPEN")
        self.assertEqual(result["fill_quantity"], Decimal("0"))

    def test_liquidity_cap_creates_partial_fill(self):
        result = paper_fill(side="BUY", quantity=Decimal("0.080"), limit_price=Decimal("63000"),
                            bid=Decimal("62430"), ask=Decimal("62448"), available_cash=Decimal("100000"))
        self.assertEqual(result["status"], "PARTIALLY_FILLED")
        self.assertEqual(result["fill_quantity"], Decimal("0.050"))

    def test_rejects_insufficient_cash_including_fee(self):
        result = paper_fill(side="BUY", quantity=Decimal("0.010"), limit_price=Decimal("63000"),
                            bid=Decimal("62430"), ask=Decimal("62448"), available_cash=Decimal("600"))
        self.assertEqual(result["status"], "REJECTED")

    def test_invalid_zero_or_side_fails_closed(self):
        with self.assertRaises(ValueError):
            paper_fill(side="BUY", quantity=Decimal("0"), limit_price=Decimal("1"), bid=Decimal("1"), ask=Decimal("1"), available_cash=Decimal("1"))
        with self.assertRaises(ValueError):
            paper_fill(side="HOLD", quantity=Decimal("1"), limit_price=Decimal("1"), bid=Decimal("1"), ask=Decimal("1"), available_cash=Decimal("1"))


if __name__ == "__main__":
    unittest.main()
