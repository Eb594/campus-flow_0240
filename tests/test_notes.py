"""Follow-up notes (Engineer A area)."""

import unittest

from helpers import ManagerTestCase
from campus_flow.tickets import TicketManager


class TestNotes(ManagerTestCase):
    def test_valid_note_is_added_with_sequential_ids(self):
        ticket = self.make()
        first = self.manager.add_note(ticket["id"], "Mentor A", "Wi-Fi router reboot attempted")
        second = self.manager.add_note(ticket["id"], "Mentor B", "Investigating switch ports")
        self.assertEqual(first, {"note_id": "N001", "author": "Mentor A",
                                 "message": "Wi-Fi router reboot attempted"})
        self.assertEqual(second["note_id"], "N002")
        self.assertEqual(ticket["notes"], [first, second])

    def test_new_ticket_starts_with_empty_notes(self):
        self.assertEqual(self.make()["notes"], [])

    def test_rejected_notes_do_not_consume_an_id(self):
        ticket = self.make()
        tid = ticket["id"]
        bad = [("  ", "Long enough"), ("Mentor A", "    "), ("Mentor A", "abcd"),
               ("Mentor A", "  abcd  "), ("Mentor A", "x" * 301), ("Mentor A", None),
               (None, "Long enough")]
        for author, message in bad:
            with self.subTest(author=author, message=message):
                self.assert_rejected_unchanged(self.manager.add_note, tid, author, message)
        self.assertEqual(self.manager.add_note(tid, "Mentor A", "Valid note")["note_id"], "N001")

    def test_message_length_boundaries(self):
        tid = self.make()["id"]
        self.assertEqual(self.manager.add_note(tid, "A", "12345")["note_id"], "N001")
        self.assertEqual(self.manager.add_note(tid, "A", "x" * 300)["note_id"], "N002")
        self.assertEqual(self.manager.add_note(tid, "A", "  hello  ")["message"], "hello")

    def test_resolved_ticket_rejects_note_until_reopened(self):
        ticket = self.make_in_progress()
        tid = ticket["id"]
        self.manager.add_note(tid, "Mentor A", "Wi-Fi router reboot attempted")
        self.manager.add_note(tid, "Mentor B", "Investigating switch ports")
        self.manager.update_status(tid, "resolved")

        self.assert_rejected_unchanged(self.manager.add_note, tid, "Mentor A", "Late comment here")
        self.assertEqual(len(self.manager.get_notes(tid)), 2)  # old notes kept

        self.manager.update_status(tid, "open")
        self.assertEqual(self.manager.add_note(tid, "Mentor A", "Back to work now")["note_id"], "N003")

    def test_notes_allowed_for_in_progress_and_ids_are_per_ticket(self):
        first, second = self.make_in_progress(), self.make()
        self.manager.add_note(first["id"], "A", "note on first")
        self.assertEqual(self.manager.add_note(second["id"], "A", "note on second")["note_id"], "N001")

    def test_get_notes_in_id_order_and_unknown_ticket(self):
        tid = self.make()["id"]
        for text in ("first note", "second note", "third note"):
            self.manager.add_note(tid, "A", text)
        self.assertEqual([n["note_id"] for n in self.manager.get_notes(tid)],
                         ["N001", "N002", "N003"])
        self.assert_rejected_unchanged(self.manager.add_note, "T999", "A", "no such ticket")
        with self.assertRaises(ValueError):
            self.manager.get_notes("T999")

    def test_get_notes_returns_copies(self):
        tid = self.make()["id"]
        self.manager.add_note(tid, "A", "original text")
        self.manager.get_notes(tid)[0]["message"] = "tampered"
        self.assertEqual(self.manager.get_notes(tid)[0]["message"], "original text")

    def test_notes_and_next_note_id_survive_reload(self):
        tid = self.make()["id"]
        self.manager.add_note(tid, "Mentor A", "first note here")
        self.manager.add_note(tid, "Mentor B", "second note here")
        reloaded = TicketManager(file_path=self.path)
        self.assertEqual(reloaded.get_notes(tid), self.manager.get_notes(tid))
        self.assertEqual(reloaded.add_note(tid, "Mentor A", "third note here")["note_id"], "N003")


if __name__ == "__main__":
    unittest.main()
