import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))

import app


class AppTests(unittest.TestCase):
    def test_score_calculation(self):
        results = {
            "item_1": "Achieved",
            "item_2": "Partial",
            "item_3": "Did Not Achieve",
            "item_4": "Achieved",
        }
        score, counts = app.calculate_score(results)
        self.assertAlmostEqual(score, 62.5)
        self.assertEqual(counts["Achieved"], 2)
        self.assertEqual(counts["Partial"], 1)
        self.assertEqual(counts["Did Not Achieve"], 1)

    def test_monthly_summary_contains_outlet_scores(self):
        history = [
            {
                "inspection_date": "2026-07-15",
                "outlet": "Pastry and Bakery",
                "score": 92.0,
                "results": {"item_1": "Achieved"},
            },
            {
                "inspection_date": "2026-07-20",
                "outlet": "Sole",
                "score": 84.0,
                "results": {"item_1": "Partial"},
            },
        ]
        summary = app.build_monthly_dashboard(history, "2026-07")
        self.assertIn("Pastry and Bakery", summary["outlet_scores"])
        self.assertIn("Sole", summary["outlet_scores"])
        self.assertIn("Recurring issues", summary)

    def test_not_applicable_items_are_excluded_from_scoring(self):
        results = {
            "item_1": "Achieved",
            "item_2": "Partial",
            "item_3": "Did Not Achieve",
            "item_4": "Not Applicable",
        }
        score, counts = app.calculate_score(results)
        self.assertAlmostEqual(score, 50.0)
        self.assertEqual(counts["Rated Items"], 3)
        self.assertEqual(counts["Achieved"], 1)
        self.assertEqual(counts["Partial"], 1)
        self.assertEqual(counts["Did Not Achieve"], 1)

    def test_export_monthly_pdf_creates_file(self):
        history = [
            {
                "inspection_date": "2026-07-15",
                "outlet": "Lobby Lounge",
                "score": 92.0,
                "results": {f"item_{i}": "Achieved" for i in range(1, 5)},
            }
        ]
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            output_path = handle.name
        self.addCleanup(lambda: os.path.exists(output_path) and os.remove(output_path))

        generated_path = app.export_monthly_pdf(history, "2026-07", output_path=output_path)

        self.assertEqual(generated_path, output_path)
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)

    def test_dynamic_filename_uses_outlet_and_date(self):
        audit_data = {
            "outlet": "Lobby Lounge",
            "inspection_timestamp": "2026-08-05 10:15",
        }
        output_path = app.build_dynamic_output_path(audit_data)
        self.assertIn("lobby lounge", output_path)
        self.assertIn("Food Safety Report", output_path)
        self.assertIn(".pdf", output_path)

    def test_generate_daily_pdf_bytes_returns_bytes(self):
        audit_data = {
            "hotel_name": "Conrad Abu Dhabi Etihad Towers",
            "outlet": "Lobby Lounge",
            "inspection_timestamp": "2026-08-05 10:15",
            "person_on_duty": "Jane",
            "department": "Food & Beverage",
            "auditor_name": "Alex",
            "results": {f"item_{i}": "Achieved" for i in range(1, 5)},
            "observations": "Good",
            "corrective_actions": "None",
            "notes_guidance": "Continue",
            "item_comments": {},
        }
        pdf_bytes, output_path = app.generate_daily_pdf_bytes(audit_data)
        self.assertIsInstance(pdf_bytes, (bytes, bytearray))
        self.assertGreater(len(pdf_bytes), 0)
        self.assertTrue(output_path.endswith(".pdf"))

    def test_generate_monthly_pdf_bytes_returns_bytes(self):
        history = [
            {
                "inspection_date": "2026-07-15",
                "outlet": "Lobby Lounge",
                "score": 92.0,
                "results": {f"item_{i}": "Achieved" for i in range(1, 5)},
            }
        ]
        pdf_bytes, output_path = app.generate_monthly_pdf_bytes(history, "2026-07")
        self.assertIsInstance(pdf_bytes, (bytes, bytearray))
        self.assertGreater(len(pdf_bytes), 0)
        self.assertTrue(output_path.endswith(".pdf"))

    def test_monthly_dashboard_contains_executive_summary_and_risk_heatmap(self):
        history = [
            {
                "inspection_date": "2026-07-15",
                "outlet": "Lobby Lounge",
                "score": 92.0,
                "results": {f"item_{i}": "Achieved" for i in range(1, 5)},
            },
            {
                "inspection_date": "2026-07-20",
                "outlet": "Pool Bar",
                "score": 64.0,
                "results": {f"item_{i}": "Did Not Achieve" if i == 1 else "Achieved" for i in range(1, 5)},
            },
        ]
        summary = app.build_monthly_dashboard(history, "2026-07")
        self.assertIn("executive_summary", summary)
        self.assertIn("risk_heatmap", summary)
        self.assertTrue(summary["risk_heatmap"])

    def test_chart_builders_return_bytes_for_streamlit(self):
        bar_chart = app.build_outlet_bar_chart({"Lobby Lounge": 92.0, "Pool Bar": 64.0})
        trend_chart = app.build_outlet_trend_chart({"Lobby Lounge": [{"date": "2026-07-01", "score": 92.0}]})
        self.assertIsInstance(bar_chart, (bytes, bytearray))
        self.assertIsInstance(trend_chart, (bytes, bytearray))

    def test_rerun_helper_uses_available_streamlit_api(self):
        with mock.patch.object(app.st, "rerun", autospec=True) as mock_rerun:
            app.rerun_app()
            mock_rerun.assert_called_once_with()

    def test_send_report_by_email_requires_configuration(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            output_path = handle.name
        self.addCleanup(lambda: os.path.exists(output_path) and os.remove(output_path))

        sent, message = app.send_report_by_email(output_path, "user@example.com")
        self.assertFalse(sent)
        self.assertIn("configured", message.lower())


if __name__ == "__main__":
    unittest.main()
