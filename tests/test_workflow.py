import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class WorkflowAndReportTests(unittest.TestCase):
    """Test ticket status changes and reports."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_ticket(self):
        return self.manager.create_ticket(
            "Network issue", "Network", "high", 2
        )

    def test_unassigned_ticket_cannot_start(self):
        ticket = self.create_ticket()

        with self.assertRaises(ValueError):
            self.manager.update_status(ticket["id"], "in_progress")

        self.assertEqual(ticket["status"], "open")

    def test_assigned_ticket_can_follow_workflow(self):
        ticket = self.create_ticket()
        ticket_id = ticket["id"]

        self.manager.assign_ticket(ticket_id, "John")
        self.manager.update_status(ticket_id, "in_progress")
        self.assertEqual(ticket["status"], "in_progress")

        self.manager.update_status(ticket_id, "resolved")
        self.assertEqual(ticket["status"], "resolved")

    def test_open_ticket_cannot_be_resolved_directly(self):
        ticket = self.create_ticket()

        with self.assertRaises(ValueError):
            self.manager.update_status(ticket["id"], "resolved")

    def test_resolved_ticket_must_be_reopened_before_modification(self):
        ticket = self.create_ticket()
        ticket_id = ticket["id"]

        self.manager.assign_ticket(ticket_id, "John")
        self.manager.update_status(ticket_id, "in_progress")
        self.manager.update_status(ticket_id, "resolved")

        with self.assertRaises(ValueError):
            self.manager.assign_ticket(ticket_id, "Mary")

        self.manager.update_status(ticket_id, "open")
        result = self.manager.assign_ticket(ticket_id, "Mary")

        self.assertEqual(result["assigned_to"], "Mary")

    def test_status_change_is_saved(self):
        ticket = self.create_ticket()
        self.manager.assign_ticket(ticket["id"], "John")
        self.manager.update_status(ticket["id"], "in_progress")

        reloaded = TicketManager(file_path=self.file_path)

        self.assertEqual(reloaded.tickets[0]["status"], "in_progress")

    def test_report_counts_status_and_priority(self):
        self.manager.create_ticket("Major outage", "Network", "high", 12)
        self.manager.create_ticket("Small outage", "Network", "low", 4)
        self.manager.create_ticket("General question", "Other", "low", 1)

        report = self.manager.generate_report()

        self.assertEqual(report["total_tickets"], 3)
        self.assertEqual(report["by_status"]["open"], 3)
        self.assertEqual(report["by_status"]["in_progress"], 0)
        self.assertEqual(report["by_status"]["resolved"], 0)

        self.assertEqual(report["by_priority"]["critical"], 1)
        self.assertEqual(report["by_priority"]["medium"], 1)
        self.assertEqual(report["by_priority"]["low"], 1)
        self.assertEqual(report["by_priority"]["high"], 0)

    def test_empty_report(self):
        report = self.manager.generate_report()

        self.assertEqual(report["total_tickets"], 0)
        self.assertTrue(
            all(count == 0 for count in report["by_status"].values())
        )
        self.assertTrue(
            all(count == 0 for count in report["by_priority"].values())
        )


if __name__ == "__main__":
    unittest.main()