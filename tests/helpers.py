"""Shared test base class: a manager that saves to a temporary file."""

import copy
import tempfile
import unittest
from pathlib import Path

from campus_flow.tickets import TicketManager


class ManagerTestCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.path = self.dir / "tickets.json"
        self.manager = TicketManager(file_path=self.path)

    def make(self, title="Wifi down", category="Network", urgency="high", users=2):
        return self.manager.create_ticket(title, category, urgency, users)

    def make_in_progress(self, **kwargs):
        ticket = self.make(**kwargs)
        self.manager.assign_ticket(ticket["id"], "Operator A")
        self.manager.update_status(ticket["id"], "in_progress")
        return ticket

    def make_resolved(self, **kwargs):
        ticket = self.make_in_progress(**kwargs)
        self.manager.update_status(ticket["id"], "resolved")
        return ticket

    def snapshot(self):
        return copy.deepcopy(self.manager.tickets)

    def file_text(self):
        return self.path.read_text(encoding="utf-8") if self.path.exists() else None

    def assert_rejected_unchanged(self, func, *args):
        """func(*args) must raise ValueError and change neither memory nor file."""
        memory, saved = self.snapshot(), self.file_text()
        with self.assertRaises(ValueError):
            func(*args)
        self.assertEqual(self.snapshot(), memory)
        self.assertEqual(self.file_text(), saved)
