import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class TestTicketCreation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "tickets.json"
        self.manager = TicketManager(file_path=self.data_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_valid_ticket(self):
        ticket = self.manager.create_ticket(
            "Broken classroom projector",
            "The projector in Room 12 is not working."
        )

        self.assertEqual(ticket["id"], 1)
        self.assertEqual(ticket["priority"], "medium")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(len(self.manager.tickets), 1)

    def test_high_priority_ticket(self):
        ticket = self.manager.create_ticket(
            "Urgent server failure",
            "The server is down."
        )

        self.assertEqual(ticket["priority"], "high")

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_ticket(
                "",
                "The projector is broken."
            )

        self.assertEqual(len(self.manager.tickets), 0)

    def test_empty_description_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_ticket(
                "Broken projector",
                "   "
            )

        self.assertEqual(len(self.manager.tickets), 0)

    def test_ticket_ids_are_unique(self):
        first = self.manager.create_ticket(
            "First ticket",
            "First description"
        )

        second = self.manager.create_ticket(
            "Second ticket",
            "Second description"
        )

        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(second["id"], 2)


if __name__ == "__main__":
    unittest.main()
