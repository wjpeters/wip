import asyncio
import os
import unittest
from unittest.mock import patch

from app.market import DemoFixtureProvider, provider_status


class MarketAdapterTests(unittest.TestCase):
    def test_demo_fixture_has_provenance_and_never_claims_live_data(self):
        quote = asyncio.run(DemoFixtureProvider().quote("BTC/EUR"))
        self.assertEqual(quote["provider_id"], "demo-fixture")
        self.assertEqual(quote["quality"], "SIMULATED")
        self.assertEqual(quote["venue_id"], "SIMULATED")
        self.assertIn("fixtures/", quote["origin_feed_id"])
        self.assertTrue(quote["source_time"].startswith("fixture;"))
        self.assertEqual(quote["bid"], "62430.25")
        self.assertEqual(quote["ask"], "62448.20")

    def test_fixture_provider_rejects_unknown_instrument(self):
        with self.assertRaises(KeyError):
            asyncio.run(DemoFixtureProvider().quote("NOPE/EUR"))

    def test_kraken_mode_stays_unverified_until_external_connection_runs(self):
        with patch.dict(os.environ, {"MARKET_MODE": "kraken"}):
            status = provider_status()
        self.assertEqual(status["verification"], "NOT_RUN_EXTERNAL_NETWORK")
        self.assertEqual(status["execution"], "UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
