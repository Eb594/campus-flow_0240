import json
import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class TestTicketStorage(unittest.TestCase):
    """Test JSON persistence and saved ticket validation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_ticket(self, title="Network issue"):
        return self.manager.create_ticket(
            title,
            "Network",
            "high",
            2,
        )

    def test_tickets_are_saved_to_json(self):
        """Creating a ticket should save it to the JSON file."""
        ticket = self.create_ticket()

        self.assertTrue(self.file_path.exists())

        saved_data = json.loads(
            self.file_path.read_text(encoding="utf-8")
        )

        self.assertEqual(len(saved_data), 1)
        self.assertEqual(saved_data[0]["id"], ticket["id"])
        self.assertEqual(saved_data[0]["title"], ticket["title"])

    def test_saved_tickets_can_be_reloaded(self):
        """A new manager should load previously saved tickets."""
        ticket = self.create_ticket()

        reloaded = TicketManager(file_path=self.file_path)

        self.assertEqual(len(reloaded.tickets), 1)
        self.assertEqual(reloaded.tickets[0]["id"], ticket["id"])
        self.assertEqual(reloaded.tickets[0]["title"], ticket["title"])

    def test_ticket_ids_continue_after_reload(self):
        """New IDs should continue after the highest saved ID."""
        first = self.create_ticket("First ticket")

        reloaded = TicketManager(file_path=self.file_path)
        second = reloaded.create_ticket(
            "Second ticket",
            "Hardware",
            "low",
            1,
        )

        self.assertEqual(first["id"], "T001")
        self.assertEqual(second["id"], "T002")

    def test_missing_file_starts_with_empty_tickets(self):
        """A missing file should not prevent a fresh start."""
        missing_file = Path(self.temp_dir.name) / "missing.json"

        manager = TicketManager(file_path=missing_file)

        self.assertEqual(manager.tickets, [])
        self.assertEqual(manager.next_id, 1)

    def test_malformed_json_raises_clear_error(self):
        """Malformed JSON should raise ValueError."""
        self.file_path.write_text(
            "{invalid json",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            TicketManager(file_path=self.file_path)

    def test_duplicate_ticket_ids_are_rejected(self):
        """Saved tickets must not contain duplicate IDs."""
        duplicate_tickets = [
            {
                "id": "T001",
                "title": "First ticket",
                "category": "Other",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": "T001",
                "title": "Second ticket",
                "category": "Other",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
            },
        ]

        self.file_path.write_text(
            json.dumps(duplicate_tickets),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Duplicate ticket ID"):
            TicketManager(file_path=self.file_path)

    def test_invalid_saved_priority_is_rejected(self):
        """Saved priority must match the priority rules."""
        invalid_tickets = [
            {
                "id": "T001",
                "title": "Network issue",
                "category": "Network",
                "urgency": "high",
                "affected_users": 2,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
            }
        ]

        self.file_path.write_text(
            json.dumps(invalid_tickets),
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            TicketManager(file_path=self.file_path)

    def test_status_changes_are_persisted(self):
        """Status changes should survive a reload."""
        ticket = self.create_ticket()

        self.manager.update_status(ticket["id"], "in_progress") if False else None

        self.manager.assign_ticket(ticket["id"], "John")
        self.manager.update_status(ticket["id"], "in_progress")

        reloaded = TicketManager(file_path=self.file_path)

        self.assertEqual(reloaded.tickets[0]["status"], "in_progress")

    def test_assignment_is_persisted(self):
        """Staff assignments should survive a reload."""
        ticket = self.create_ticket()

        self.manager.assign_ticket(ticket["id"], "John")

        reloaded = TicketManager(file_path=self.file_path)

        self.assertEqual(reloaded.tickets[0]["assigned_to"], "John")


if __name__ == "__main__":
    unittest.main()
