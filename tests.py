import json
import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class TestTicketCreation(unittest.TestCase):
    """Test ticket creation and validation."""

    def setUp(self):
        """Create a temporary file for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        """Remove temporary test files."""
        self.temp_dir.cleanup()

    def test_create_valid_ticket(self):
        """A valid ticket should be created successfully."""
        ticket = self.manager.create_ticket(
            "Broken projector",
            "The classroom projector is not working."
        )

        self.assertEqual(ticket["id"], 1)
        self.assertEqual(ticket["title"], "Broken projector")
        self.assertEqual(
            ticket["description"],
            "The classroom projector is not working."
        )
        self.assertEqual(ticket["priority"], "medium")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assignee"])

    def test_empty_title_is_rejected(self):
        """An empty title should raise ValueError."""
        with self.assertRaises(ValueError):
            self.manager.create_ticket(
                "   ",
                "The classroom projector is broken."
            )

    def test_empty_description_is_rejected(self):
        """An empty description should raise ValueError."""
        with self.assertRaises(ValueError):
            self.manager.create_ticket(
                "Broken projector",
                "   "
            )

    def test_high_priority_ticket(self):
        """A ticket containing urgent keywords should have high priority."""
        ticket = self.manager.create_ticket(
            "Urgent server failure",
            "The server needs immediate attention."
        )

        self.assertEqual(ticket["priority"], "high")

    def test_ticket_ids_are_unique(self):
        """Each new ticket should receive a unique ID."""
        first = self.manager.create_ticket(
            "First ticket",
            "First description."
        )

        second = self.manager.create_ticket(
            "Second ticket",
            "Second description."
        )

        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(first["id"], 1)
        self.assertEqual(second["id"], 2)


class TestTicketAssignment(unittest.TestCase):
    """Test assigning tickets to staff members."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

        self.ticket = self.manager.create_ticket(
            "Broken projector",
            "The classroom projector is broken."
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_assign_ticket(self):
        """An existing ticket can be assigned to a staff member."""
        result = self.manager.assign_ticket(
            self.ticket["id"],
            "John"
        )

        self.assertEqual(result["assignee"], "John")

    def test_empty_staff_name_is_rejected(self):
        """An empty staff name should be rejected."""
        with self.assertRaises(ValueError):
            self.manager.assign_ticket(
                self.ticket["id"],
                "   "
            )

        self.assertIsNone(self.ticket["assignee"])

    def test_unknown_ticket_id_is_rejected(self):
        """An unknown ticket ID should be rejected."""
        with self.assertRaises(ValueError):
            self.manager.assign_ticket(999, "John")

    def test_assignee_is_saved(self):
        """The assigned staff member should survive reloading."""
        self.manager.assign_ticket(self.ticket["id"], "John")

        reloaded_manager = TicketManager(file_path=self.file_path)

        self.assertEqual(
            reloaded_manager.tickets[0]["assignee"],
            "John"
        )


class TestWorkQueue(unittest.TestCase):
    """Test ticket queue ordering and filtering."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_work_queue_priority_order(self):
        """Critical, high, medium, and low tickets should be ordered."""
        low = self.manager.create_ticket(
            "General question",
            "I need some information."
        )

        medium = self.manager.create_ticket(
            "Broken keyboard",
            "The keyboard is broken."
        )

        high = self.manager.create_ticket(
            "Urgent server",
            "Urgent server problem."
        )

        critical = self.manager.create_ticket(
            "Critical outage",
            "Critical service outage."
        )

        queue = self.manager.get_work_queue()

        self.assertEqual(
            [ticket["id"] for ticket in queue],
            [
                critical["id"],
                high["id"],
                medium["id"],
                low["id"]
            ]
        )

    def test_queue_ties_use_ascending_ticket_id(self):
        """Tickets with equal priority should be ordered by ID."""
        first = self.manager.create_ticket(
            "First urgent ticket",
            "Urgent attention required."
        )

        second = self.manager.create_ticket(
            "Second urgent ticket",
            "Urgent attention required."
        )

        queue = self.manager.get_work_queue()

        self.assertEqual(
            [ticket["id"] for ticket in queue],
            [first["id"], second["id"]]
        )

    def test_queue_excludes_non_open_tickets(self):
        """Resolved tickets should not appear in the open work queue."""
        ticket = self.manager.create_ticket(
            "Urgent server",
            "Urgent server failure."
        )

        ticket["status"] = "resolved"

        queue = self.manager.get_work_queue()

        self.assertNotIn(ticket, queue)

    def test_empty_work_queue(self):
        """An empty queue should return an empty list."""
        self.assertEqual(self.manager.get_work_queue(), [])

    def test_work_queue_does_not_change_ticket_order(self):
        """Getting the queue should not reorder stored tickets."""
        self.manager.create_ticket("First ticket", "General request.")
        self.manager.create_ticket("Urgent ticket", "Urgent request.")

        original_ids = [
            ticket["id"] for ticket in self.manager.tickets
        ]

        self.manager.get_work_queue()

        updated_ids = [
            ticket["id"] for ticket in self.manager.tickets
        ]

        self.assertEqual(updated_ids, original_ids)


class TestTicketPersistence(unittest.TestCase):
    """Test saving, loading, and validating JSON ticket data."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tickets_reload_from_json(self):
        """Saved tickets should be available after reloading."""
        ticket = self.manager.create_ticket(
            "Broken monitor",
            "The monitor is broken."
        )

        reloaded_manager = TicketManager(file_path=self.file_path)

        self.assertEqual(len(reloaded_manager.tickets), 1)
        self.assertEqual(
            reloaded_manager.tickets[0]["id"],
            ticket["id"]
        )
        self.assertEqual(
            reloaded_manager.tickets[0]["title"],
            "Broken monitor"
        )

    def test_ticket_ids_remain_unique_after_reload(self):
        """New IDs should continue after the highest saved ID."""
        self.manager.create_ticket(
            "First ticket",
            "First description."
        )

        reloaded_manager = TicketManager(file_path=self.file_path)

        second = reloaded_manager.create_ticket(
            "Second ticket",
            "Second description."
        )

        self.assertEqual(second["id"], 2)

    def test_missing_file_starts_with_no_tickets(self):
        """A missing JSON file should start with an empty ticket list."""
        new_file = Path(self.temp_dir.name) / "missing.json"

        manager = TicketManager(file_path=new_file)

        self.assertEqual(manager.tickets, [])
        self.assertEqual(manager.next_id, 1)

    def test_malformed_json_is_rejected(self):
        """Malformed JSON should raise a clear error."""
        self.file_path.write_text(
            "{invalid json",
            encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            TicketManager(file_path=self.file_path)

    def test_duplicate_ticket_ids_are_rejected(self):
        """Duplicate IDs in saved data should be rejected."""
        duplicate_tickets = [
            {
                "id": 1,
                "title": "First ticket",
                "description": "First description.",
                "priority": "low",
                "status": "open",
                "assignee": None
            },
            {
                "id": 1,
                "title": "Second ticket",
                "description": "Second description.",
                "priority": "low",
                "status": "open",
                "assignee": None
            }
        ]

        self.file_path.write_text(
            json.dumps(duplicate_tickets),
            encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "Duplicate ticket ID"):
            TicketManager(file_path=self.file_path)


if __name__ == "__main__":
    unittest.main()