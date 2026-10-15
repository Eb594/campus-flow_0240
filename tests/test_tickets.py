import json
import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class TestTicketCreation(unittest.TestCase):
    """Test ticket creation, validation, priorities, and IDs."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_valid_ticket(self):
        ticket = self.manager.create_ticket(
            "Broken projector", "Hardware", "medium", 2
        )

        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["title"], "Broken projector")
        self.assertEqual(ticket["category"], "Hardware")
        self.assertEqual(ticket["urgency"], "medium")
        self.assertEqual(ticket["affected_users"], 2)
        self.assertEqual(ticket["priority"], "medium")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_ticket("   ", "Hardware", "low", 1)

        self.assertEqual(self.manager.tickets, [])

    def test_invalid_category_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_ticket(
                "Broken projector", "Furniture", "low", 1
            )

    def test_invalid_urgency_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_ticket(
                "Broken projector", "Hardware", "urgent", 1
            )

    def test_zero_affected_users_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_ticket(
                "Network issue", "Network", "high", 0
            )

    def test_high_urgency_and_ten_users_is_critical(self):
        ticket = self.manager.create_ticket(
            "Network outage", "Network", "high", 12
        )
        self.assertEqual(ticket["priority"], "critical")

    def test_high_urgency_with_two_users_is_high(self):
        ticket = self.manager.create_ticket(
            "Computer problem", "Hardware", "high", 2
        )
        self.assertEqual(ticket["priority"], "high")

    def test_four_users_with_low_urgency_is_medium(self):
        ticket = self.manager.create_ticket(
            "Software issue", "Software", "low", 4
        )
        self.assertEqual(ticket["priority"], "medium")

    def test_one_user_with_low_urgency_is_low(self):
        ticket = self.manager.create_ticket(
            "General question", "Other", "low", 1
        )
        self.assertEqual(ticket["priority"], "low")

    def test_ticket_ids_are_unique(self):
        first = self.manager.create_ticket(
            "First ticket", "Other", "low", 1
        )
        second = self.manager.create_ticket(
            "Second ticket", "Other", "low", 1
        )

        self.assertEqual(first["id"], "T001")
        self.assertEqual(second["id"], "T002")
        self.assertNotEqual(first["id"], second["id"])


class TestTicketAssignment(unittest.TestCase):
    """Test assigning tickets to staff."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)
        self.ticket = self.manager.create_ticket(
            "Broken projector", "Hardware", "medium", 2
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_assign_ticket(self):
        result = self.manager.assign_ticket(self.ticket["id"], "John")
        self.assertEqual(result["assigned_to"], "John")

    def test_empty_staff_name_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.assign_ticket(self.ticket["id"], "   ")

        self.assertIsNone(self.ticket["assigned_to"])

    def test_unknown_ticket_id_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.assign_ticket("T999", "John")

    def test_assignment_is_saved(self):
        self.manager.assign_ticket(self.ticket["id"], "John")
        reloaded = TicketManager(file_path=self.file_path)

        self.assertEqual(reloaded.tickets[0]["assigned_to"], "John")


class TestWorkQueue(unittest.TestCase):
    """Test queue filtering and priority ordering."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_work_queue_priority_order(self):
        low = self.manager.create_ticket(
            "General question", "Other", "low", 1
        )
        medium = self.manager.create_ticket(
            "Small outage", "Network", "low", 4
        )
        high = self.manager.create_ticket(
            "Urgent computer issue", "Hardware", "high", 2
        )
        critical = self.manager.create_ticket(
            "Major network outage", "Network", "high", 12
        )

        queue = self.manager.get_work_queue()

        self.assertEqual(
            [ticket["id"] for ticket in queue],
            [critical["id"], high["id"], medium["id"], low["id"]],
        )

    def test_queue_ties_use_ascending_ticket_id(self):
        first = self.manager.create_ticket(
            "First urgent ticket", "Network", "high", 2
        )
        second = self.manager.create_ticket(
            "Second urgent ticket", "Network", "high", 2
        )

        queue = self.manager.get_work_queue()

        self.assertEqual(
            [ticket["id"] for ticket in queue],
            [first["id"], second["id"]],
        )

    def test_queue_excludes_resolved_tickets(self):
        ticket = self.manager.create_ticket(
            "Network issue", "Network", "high", 2
        )
        self.manager.assign_ticket(ticket["id"], "John")
        self.manager.update_status(ticket["id"], "in_progress")
        self.manager.update_status(ticket["id"], "resolved")

        queue = self.manager.get_work_queue()
        self.assertNotIn(ticket, queue)

    def test_empty_work_queue(self):
        self.assertEqual(self.manager.get_work_queue(), [])

    def test_getting_queue_does_not_reorder_stored_tickets(self):
        self.manager.create_ticket("First", "Other", "low", 1)
        self.manager.create_ticket("Urgent", "Network", "high", 2)

        original_ids = [
            ticket["id"] for ticket in self.manager.tickets
        ]
        self.manager.get_work_queue()
        updated_ids = [
            ticket["id"] for ticket in self.manager.tickets
        ]

        self.assertEqual(updated_ids, original_ids)


class TestTicketPersistence(unittest.TestCase):
    """Test saving, reloading, and validating JSON data."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tickets_reload_from_json(self):
        ticket = self.manager.create_ticket(
            "Broken monitor", "Hardware", "medium", 2
        )
        reloaded = TicketManager(file_path=self.file_path)

        self.assertEqual(len(reloaded.tickets), 1)
        self.assertEqual(reloaded.tickets[0]["id"], ticket["id"])
        self.assertEqual(reloaded.tickets[0]["title"], "Broken monitor")

    def test_ids_continue_after_reload(self):
        self.manager.create_ticket("First", "Other", "low", 1)
        reloaded = TicketManager(file_path=self.file_path)

        second = reloaded.create_ticket("Second", "Other", "low", 1)
        self.assertEqual(second["id"], "T002")

    def test_missing_file_starts_empty(self):
        missing_file = Path(self.temp_dir.name) / "missing.json"
        manager = TicketManager(file_path=missing_file)

        self.assertEqual(manager.tickets, [])
        self.assertEqual(manager.next_id, 1)

    def test_malformed_json_is_rejected(self):
        self.file_path.write_text("{invalid json", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            TicketManager(file_path=self.file_path)

    def test_duplicate_ticket_ids_are_rejected(self):
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
            json.dumps(duplicate_tickets), encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "Duplicate ticket ID"):
            TicketManager(file_path=self.file_path)


if __name__ == "__main__":
    unittest.main()