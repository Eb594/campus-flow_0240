"""Validation and lifecycle safety (Engineer A area)."""

import unittest
from unittest import mock

from campus_flow import validation as v
from helpers import ManagerTestCase


class TestPriorityRules(unittest.TestCase):
    def test_priority_rule_precedence(self):
        cases = [
            ("high", 10, "critical"), ("high", 9, "high"),
            ("medium", 10, "high"), ("low", 10, "high"),
            ("medium", 1, "medium"), ("low", 3, "medium"),
            ("low", 2, "low"),
        ]
        for urgency, users, expected in cases:
            with self.subTest(urgency=urgency, users=users):
                self.assertEqual(v.calculate_priority(urgency, users), expected)


class TestTransitionTable(unittest.TestCase):
    def test_legal_and_illegal_transitions(self):
        legal = [("open", "in_progress"), ("in_progress", "resolved"),
                 ("resolved", "open")]
        for current, new in legal:
            with self.subTest(current=current, new=new):
                v.check_transition(current, new, "Operator A")  # no error
        illegal = [("open", "resolved"), ("in_progress", "open"),
                   ("resolved", "in_progress"), ("open", "open")]
        for current, new in illegal:
            with self.subTest(current=current, new=new):
                with self.assertRaises(ValueError):
                    v.check_transition(current, new, "Operator A")

    def test_start_requires_assignee(self):
        with self.assertRaises(ValueError):
            v.check_transition("open", "in_progress", None)


class TestValidationRejectsBadInput(ManagerTestCase):
    def test_unassigned_open_to_in_progress_rejected_and_unchanged(self):
        ticket = self.make()
        self.assert_rejected_unchanged(
            self.manager.update_status, ticket["id"], "in_progress")
        self.assertEqual(ticket["status"], "open")

    def test_resolved_ticket_assignment_rejected_and_unchanged(self):
        ticket = self.make_resolved()
        self.assert_rejected_unchanged(
            self.manager.assign_ticket, ticket["id"], "Operator B")
        self.assertEqual(ticket["assigned_to"], "Operator A")

    def test_invalid_affected_users_rejected(self):
        for bad in (0, -3, 2.5, "3", True, False, None):
            with self.subTest(value=bad):
                self.assert_rejected_unchanged(
                    self.manager.create_ticket, "Wifi", "Network", "low", bad)
        self.assertEqual(self.manager.tickets, [])

    def test_invalid_category_urgency_title_rejected(self):
        self.assert_rejected_unchanged(self.manager.create_ticket, "Wifi", "Furniture", "low", 1)
        self.assert_rejected_unchanged(self.manager.create_ticket, "Wifi", "Network", "urgent", 1)
        self.assert_rejected_unchanged(self.manager.create_ticket, "   ", "Network", "low", 1)
        self.assert_rejected_unchanged(self.manager.create_ticket, None, "Network", "low", 1)

    def test_category_is_normalised(self):
        self.assertEqual(self.make(category="  nEtWoRk ")["category"], "Network")

    def test_invalid_assign_status_and_unknown_id_change_nothing(self):
        ticket = self.make()
        self.assert_rejected_unchanged(self.manager.assign_ticket, ticket["id"], "  ")
        self.assert_rejected_unchanged(self.manager.assign_ticket, "T999", "Operator A")
        self.assert_rejected_unchanged(self.manager.update_status, ticket["id"], "closed")
        self.assert_rejected_unchanged(self.manager.update_status, "T999", "open")
        self.assert_rejected_unchanged(self.manager.update_status, ticket["id"], "resolved")

    def test_ticket_ids_stay_unique(self):
        ids = [self.make()["id"] for _ in range(12)]
        self.assertEqual(len(set(ids)), 12)
        self.assertEqual(ids[-1], "T012")


class TestFailedSaveRollsBack(ManagerTestCase):
    """If writing the file fails, memory must not keep the change."""

    def test_each_mutation_is_undone_when_save_fails(self):
        ticket = self.make()
        self.manager.assign_ticket(ticket["id"], "Operator A")
        before = self.snapshot()
        with mock.patch.object(self.manager, "save_tickets", side_effect=OSError("disk full")):
            for call in (
                lambda: self.manager.create_ticket("New", "Other", "low", 1),
                lambda: self.manager.assign_ticket(ticket["id"], "Operator B"),
                lambda: self.manager.update_status(ticket["id"], "in_progress"),
                lambda: self.manager.add_note(ticket["id"], "Mentor A", "Router rebooted"),
            ):
                with self.assertRaises(OSError):
                    call()
                self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
