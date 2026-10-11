import json
from pathlib import Path


class TicketManager:
    """Manage ticket creation, assignment, searching, queues, and storage."""

    PRIORITY_ORDER = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    VALID_STATUSES = {"open", "in_progress", "resolved"}

    def __init__(self, file_path="tickets.json"):
        self.file_path = Path(file_path)
        self.tickets = []
        self.next_id = 1
        self.load_tickets()

    def calculate_priority(self, title, description):
        """Calculate ticket priority using keyword rules."""

        text = f"{title} {description}".lower()

        if "critical" in text:
            return "critical"

        high_priority_words = ["urgent", "emergency", "danger"]
        medium_priority_words = ["broken", "failure", "error", "problem"]

        if any(word in text for word in high_priority_words):
            return "high"

        if any(word in text for word in medium_priority_words):
            return "medium"

        return "low"

    def create_ticket(self, title, description):
        """Validate and create a new ticket."""

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Ticket title is required.")

        if not isinstance(description, str) or not description.strip():
            raise ValueError("Ticket description is required.")

        ticket = {
            "id": self.next_id,
            "title": title.strip(),
            "description": description.strip(),
            "priority": self.calculate_priority(title, description),
            "status": "open",
            "assignee": None,
        }

        self.tickets.append(ticket)
        self.next_id += 1

        try:
            self.save_tickets()
        except OSError:
            self.tickets.pop()
            self.next_id -= 1
            raise

        return ticket

    def search_tickets(self, query):
        """Search tickets by ID or title."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty.")

        query = query.strip()

        return [
            ticket
            for ticket in self.tickets
            if str(ticket["id"]) == query
            or query.casefold() in ticket["title"].casefold()
        ]

    def assign_ticket(self, ticket_id, staff_name):
        """Assign an existing ticket to a staff member."""

        if not isinstance(staff_name, str) or not staff_name.strip():
            raise ValueError("Staff name cannot be empty.")

        ticket = self._find_ticket(ticket_id)

        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found.")

        previous_assignee = ticket["assignee"]
        ticket["assignee"] = staff_name.strip()

        try:
            self.save_tickets()
        except OSError:
            ticket["assignee"] = previous_assignee
            raise

        return ticket

    def _find_ticket(self, ticket_id):
        """Find a ticket using its numeric ID."""

        try:
            numeric_id = int(ticket_id)
        except (TypeError, ValueError):
            return None

        for ticket in self.tickets:
            if ticket["id"] == numeric_id:
                return ticket

        return None

    def get_work_queue(self):
        """Return open tickets by priority, then ascending ticket ID."""

        open_tickets = [
            ticket
            for ticket in self.tickets
            if ticket["status"] == "open"
        ]

        return sorted(
            open_tickets,
            key=lambda ticket: (
                self.PRIORITY_ORDER[ticket["priority"]],
                ticket["id"],
            ),
        )

    def save_tickets(self):
        """Save tickets to JSON without partially overwriting the data file."""

        temporary_path = self.file_path.with_name(
            self.file_path.name + ".tmp"
        )

        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(self.tickets, file, indent=4)
                file.write("\n")

            temporary_path.replace(self.file_path)

        except OSError:
            if temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass
            raise

    def load_tickets(self):
        """Load and validate previously saved tickets."""

        if not self.file_path.exists():
            return

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                loaded_tickets = json.load(file)

        except json.JSONDecodeError as error:
            raise ValueError(
                "The ticket data file contains invalid JSON."
            ) from error

        if not isinstance(loaded_tickets, list):
            raise ValueError(
                "The ticket data file must contain a list of tickets."
            )

        seen_ids = set()

        for ticket in loaded_tickets:
            if not isinstance(ticket, dict):
                raise ValueError("Every ticket must be a JSON object.")

            required_fields = {
                "id",
                "title",
                "description",
                "priority",
                "status",
                "assignee",
            }

            if not required_fields.issubset(ticket):
                raise ValueError(
                    "A ticket is missing one or more required fields."
                )

            ticket_id = ticket["id"]

            if (
                isinstance(ticket_id, bool)
                or not isinstance(ticket_id, int)
                or ticket_id < 1
            ):
                raise ValueError("Ticket IDs must be positive integers.")

            if ticket_id in seen_ids:
                raise ValueError(f"Duplicate ticket ID: {ticket_id}")

            seen_ids.add(ticket_id)

            if not isinstance(ticket["title"], str) or not ticket["title"].strip():
                raise ValueError("Every ticket must have a title.")

            if (
                not isinstance(ticket["description"], str)
                or not ticket["description"].strip()
            ):
                raise ValueError("Every ticket must have a description.")

            if ticket["priority"] not in self.PRIORITY_ORDER:
                raise ValueError(
                    f"Invalid priority for ticket {ticket_id}."
                )

            if ticket["status"] not in self.VALID_STATUSES:
                raise ValueError(
                    f"Invalid status for ticket {ticket_id}."
                )

            assignee = ticket["assignee"]

            if assignee is not None and (
                not isinstance(assignee, str) or not assignee.strip()
            ):
                raise ValueError(
                    f"Invalid assignee for ticket {ticket_id}."
                )

        self.tickets = loaded_tickets

        if self.tickets:
            self.next_id = max(ticket["id"] for ticket in self.tickets) + 1