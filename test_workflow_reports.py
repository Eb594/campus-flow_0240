import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class WorkflowAndReportTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_unassigned_ticket_cannot_start(self):
        ticket = self.manager.create_ticket("Network", "Network issue")

        with self.assertRaises(ValueError):
            self.manager.update_status(ticket["id"], "in_progress")

        self.assertEqual(ticket["status"], "open")

    def test_ticket_workflow(self):
        ticket = self.manager.create_ticket("Network", "Network issue")
        ticket_id = ticket["id"]

        self.manager.assign_ticket(ticket_id, "John")
        self.manager.update_status(ticket_id, "in_progress")
        self.assertEqual(ticket["status"], "in_progress")

        self.manager.update_status(ticket_id, "resolved")
        self.assertEqual(ticket["status"], "resolved")

        self.manager.update_status(ticket_id, "open")
        self.assertEqual(ticket["status"], "open")

    def test_cannot_resolve_open_ticket_directly(self):
        ticket = self.manager.create_ticket("Network", "Network issue")

        with self.assertRaises(ValueError):
            self.manager.update_status(ticket["id"], "resolved")

    def test_status_change_is_saved(self):
        ticket = self.manager.create_ticket("Network", "Network issue")
        self.manager.assign_ticket(ticket["id"], "John")
        self.manager.update_status(ticket["id"], "in_progress")

        reloaded = TicketManager(self.file_path)

        self.assertEqual(reloaded.tickets[0]["status"], "in_progress")

    def test_report_counts_status_and_priority(self):
        self.manager.create_ticket("General request", "Help needed")
        self.manager.create_ticket("Critical server", "Critical failure")
        self.manager.create_ticket("Broken projector", "Projector failure")

        report = self.manager.generate_report()

        self.assertEqual(report["total_tickets"], 3)
        self.assertEqual(report["by_status"]["open"], 3)
        self.assertEqual(report["by_status"]["in_progress"], 0)
        self.assertEqual(report["by_status"]["resolved"], 0)
        self.assertEqual(report["by_priority"]["critical"], 1)
        self.assertEqual(report["by_priority"]["medium"], 1)
        self.assertEqual(report["by_priority"]["low"], 1)

    def test_empty_report(self):
        report = self.manager.generate_report()

        self.assertEqual(report["total_tickets"], 0)
        self.assertTrue(all(
            count == 0 for count in report["by_status"].values()
        ))
        self.assertTrue(all(
            count == 0 for count in report["by_priority"].values()
        ))


if __name__ == "__main__":
    unittest.main()
