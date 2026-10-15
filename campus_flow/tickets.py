"""Ticket business rules and JSON persistence.

Contract for every mutating method (create_ticket, assign_ticket,
update_status, add_note):
  1. validate all input first (nothing is changed if this fails);
  2. change the ticket data;
  3. save to disk; if saving fails, undo the change and re-raise OSError.
Invalid input raises ValueError. So a rejected action leaves tickets unchanged.
"""

import json
from pathlib import Path

from . import validation as v


def next_ticket_id(tickets):
    """Next free ticket ID, e.g. 'T003'. Compares numbers, not text."""
    highest = max((int(t["id"][1:]) for t in tickets), default=0)
    return f"T{highest + 1:03d}"


def next_note_id(ticket):
    """Next free note ID for one ticket, e.g. 'N003'."""
    highest = max((int(n["note_id"][1:]) for n in ticket["notes"]), default=0)
    return f"N{highest + 1:03d}"


class TicketManager:
    """Manage Campus Flow tickets and JSON persistence."""

    CATEGORIES = v.CATEGORIES
    URGENCIES = set(v.URGENCIES)
    PRIORITY_ORDER = {name: rank for rank, name in enumerate(v.PRIORITIES)}
    VALID_STATUSES = set(v.STATUSES)

    def __init__(self, file_path="tickets.json"):
        self.file_path = Path(file_path)
        self.tickets = []
        self.load_tickets()

    @property
    def next_id(self):
        return int(next_ticket_id(self.tickets)[1:])

    def calculate_priority(self, urgency, affected_users):
        return v.calculate_priority(urgency, affected_users)

    # ----- helpers -----------------------------------------------------

    def _find_ticket(self, ticket_id):
        """Return the ticket with this ID (case/space tolerant) or None."""
        if not isinstance(ticket_id, str):
            return None
        wanted = ticket_id.strip().upper()
        return next((t for t in self.tickets if t["id"] == wanted), None)

    def _get_ticket(self, ticket_id):
        ticket = self._find_ticket(ticket_id)
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found.")
        return ticket

    def _change(self, ticket, field, value):
        """Set ticket[field], save, and undo the change if saving fails."""
        old = ticket[field]
        ticket[field] = value
        try:
            self.save_tickets()
        except OSError:
            ticket[field] = old
            raise

    # ----- tickets -----------------------------------------------------

    def create_ticket(self, title, category, urgency, affected_users):
        title = v.validate_title(title)
        category = v.validate_category(category)
        urgency = v.validate_urgency(urgency)
        priority = v.calculate_priority(urgency, affected_users)

        ticket = {
            "id": next_ticket_id(self.tickets),
            "title": title,
            "category": category,
            "urgency": urgency,
            "affected_users": affected_users,
            "priority": priority,
            "status": "open",
            "assigned_to": None,
            "notes": [],
        }
        self.tickets.append(ticket)
        try:
            self.save_tickets()
        except OSError:
            self.tickets.pop()
            raise
        return ticket

    def search_tickets(self, query):
        """Original search: ticket ID or case-insensitive title substring."""
        query = v.validate_label(query, "Search query").casefold()
        return [
            t for t in self.tickets
            if t["id"].casefold() == query or query in t["title"].casefold()
        ]

    def assign_ticket(self, ticket_id, staff_name):
        staff_name = v.validate_label(staff_name, "Staff name")
        ticket = self._get_ticket(ticket_id)
        if ticket["status"] == "resolved":
            raise ValueError(
                "Reopen the resolved ticket before changing its assignment."
            )
        self._change(ticket, "assigned_to", staff_name)
        return ticket

    def update_status(self, ticket_id, new_status):
        new_status = v.validate_status(new_status)
        ticket = self._get_ticket(ticket_id)
        try:
            v.check_transition(
                ticket["status"], new_status, ticket["assigned_to"]
            )
        except ValueError as error:
            raise ValueError(f"Ticket {ticket['id']}: {error}") from error
        self._change(ticket, "status", new_status)
        return ticket

    def get_work_queue(self):
        """Open tickets only: priority order, then ascending ticket number."""
        open_tickets = [t for t in self.tickets if t["status"] == "open"]
        return sorted(
            open_tickets,
            key=lambda t: (self.PRIORITY_ORDER[t["priority"]], int(t["id"][1:])),
        )

    def generate_report(self):
        """Return ticket totals grouped by status and priority."""
        report = {
            "total_tickets": len(self.tickets),
            "by_status": dict.fromkeys(sorted(self.VALID_STATUSES), 0),
            "by_priority": dict.fromkeys(self.PRIORITY_ORDER, 0),
        }
        for ticket in self.tickets:
            report["by_status"][ticket["status"]] += 1
            report["by_priority"][ticket["priority"]] += 1
        return report

    # ----- notes -------------------------------------------------------

    def add_note(self, ticket_id, author, message):
        """Add a follow-up note and return it.

        Valid when the ticket is open or in_progress. Raises ValueError for
        a blank author, a message outside 5-300 characters (after trimming),
        an unknown ticket, or a resolved ticket. A rejected note changes
        nothing, so it never uses up a note ID.
        """
        author = v.validate_label(author, "Note author")
        message = v.validate_message(message)
        ticket = self._get_ticket(ticket_id)
        if ticket["status"] == "resolved":
            raise ValueError("Reopen the resolved ticket before adding notes.")

        note = {
            "note_id": next_note_id(ticket),
            "author": author,
            "message": message,
        }
        ticket["notes"].append(note)
        try:
            self.save_tickets()
        except OSError:
            ticket["notes"].pop()
            raise
        return note

    def get_notes(self, ticket_id):
        """All notes of a ticket (any status), in note-ID order."""
        notes = self._get_ticket(ticket_id)["notes"]
        return [dict(n) for n in sorted(notes, key=lambda n: int(n["note_id"][1:]))]

    # ----- persistence -------------------------------------------------

    def save_tickets(self):
        """Write all tickets (including notes) via a temporary file."""
        temporary = self.file_path.with_name(self.file_path.name + ".tmp")
        try:
            with temporary.open("w", encoding="utf-8") as file:
                json.dump(self.tickets, file, indent=4)
                file.write("\n")
            temporary.replace(self.file_path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise

    def load_tickets(self):
        """Replace memory with the file's tickets, but only if ALL are valid.

        The whole file is decoded and validated into a new list first; the
        manager's own list is swapped in at the very end. Any problem raises
        ValueError and leaves the current tickets exactly as they were.
        """
        if not self.file_path.exists():
            return

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("The ticket data file contains invalid JSON.") from error

        if not isinstance(data, list):
            raise ValueError("The ticket data file must contain a list of tickets.")

        loaded, seen = [], set()
        for record in data:
            ticket = v.validate_ticket_record(record)
            if ticket["id"] in seen:
                raise ValueError(f"Duplicate ticket ID: {ticket['id']}")
            seen.add(ticket["id"])
            loaded.append(ticket)

        self.tickets = loaded
