import unittest
from scripts.ingest import category_for, clean_text, parse_date, resolve_location, parse_feed

SOURCE = {"id":"test-feed","name":"Test publisher","url":"https://example.gov.in/rss","publisher":"Example public institution"}

class IngestTests(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(clean_text("<p>Water &amp; sanitation</p>"), "Water & sanitation")
    def test_parse_date(self):
        self.assertEqual(parse_date("Sun, 18 Oct 2026 10:00:00 +0530"), "2026-10-18T04:30:00Z")
    def test_category(self):
        self.assertEqual(category_for("Cabinet approves new climate policy"), "Environment")
        self.assertEqual(category_for("Lok Sabha parliamentary question"), "Parliament")
    def test_city_location_is_caveated(self):
        result = resolve_location("A meeting was held in Mumbai")
        self.assertEqual(result["location"], "Mumbai, Maharashtra")
        self.assertIn("not independently verified", result["locationConfidence"])
    def test_unknown_location_does_not_invent_city(self):
        result = resolve_location("A national programme was announced")
        self.assertEqual(result["locationScope"], "national")
        self.assertIn("no event location inferred", result["locationConfidence"])
    def test_feed_keeps_source_and_timestamp(self):
        xml = b"""<?xml version="1.0"?><rss version="2.0"><channel><item><title>New public water policy</title><link>https://example.gov.in/release/123</link><description>Water quality measures.</description><pubDate>Sun, 18 Oct 2026 10:00:00 +0530</pubDate><guid>123</guid></item></channel></rss>"""
        records = parse_feed(xml, SOURCE)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source"], "https://example.gov.in/release/123")
        self.assertEqual(records[0]["publishedAt"], "2026-10-18T04:30:00Z")
        self.assertEqual(records[0]["sourceType"], "official-rss")

if __name__ == "__main__":
    unittest.main()
