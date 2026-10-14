import json
import re
from pathlib import Path


class TicketManager:
    """Manage Campus Flow tickets and JSON persistence."""

    CATEGORIES = {
        "network": "Network",
        "hardware": "Hardware",
        "software": "Software",
        "other": "Other",
    }

    URGENCIES = {"low", "medium", "high"}

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

    def calculate_priority(self, urgency, affected_users):
        """Calculate priority using the assignment's rules."""

        if urgency not in self.URGENCIES:
            raise ValueError("Urgency must be low, medium, or high.")

        if (
            isinstance(affected_users, bool)
            or not isinstance(affected_users, int)
            or affected_users < 1
        ):
            raise ValueError("Affected users must be a positive integer.")

        if urgency == "high" and affected_users >= 10:
            return "critical"

        if urgency == "high" or affected_users >= 10:
            return "high"

        if urgency == "medium" or affected_users >= 3:
            return "medium"

        return "low"

    def create_ticket(
        self, title, category, urgency, affected_users
    ):
        """Validate and create a ticket."""

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Ticket title is required.")

        if not isinstance(category, str):
            raise ValueError("A valid ticket category is required.")

        category_key = category.strip().casefold()

        if category_key not in self.CATEGORIES:
            raise ValueError(
                "Category must be Network, Hardware, Software, or Other."
            )

        if not isinstance(urgency, str):
            raise ValueError("Urgency must be low, medium, or high.")

        urgency = urgency.strip().lower()

        if urgency not in self.URGENCIES:
            raise ValueError("Urgency must be low, medium, or high.")

        priority = self.calculate_priority(urgency, affected_users)

        ticket = {
            "id": f"T{self.next_id:03d}",
            "title": title.strip(),
            "category": self.CATEGORIES[category_key],
            "urgency": urgency,
            "affected_users": affected_users,
            "priority": priority,
            "status": "open",
            "assigned_to": None,
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
        """Search tickets by ID or a case-insensitive title substring."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty.")

        query = query.strip()

        return [
            ticket
            for ticket in self.tickets
            if ticket["id"].casefold() == query.casefold()
            or query.casefold() in ticket["title"].casefold()
        ]

    def _find_ticket(self, ticket_id):
        """Find a ticket by its ID."""

        if not isinstance(ticket_id, str):
            return None

        ticket_id = ticket_id.strip().upper()

        for ticket in self.tickets:
            if ticket["id"] == ticket_id:
                return ticket

        return None

    def assign_ticket(self, ticket_id, staff_name):
        """Assign an open or in-progress ticket to a staff member."""

        if not isinstance(staff_name, str) or not staff_name.strip():
            raise ValueError("Staff name cannot be empty.")

        ticket = self._find_ticket(ticket_id)

        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found.")

        if ticket["status"] == "resolved":
            raise ValueError(
                "Reopen the resolved ticket before changing its assignment."
            )

        previous_assignee = ticket["assigned_to"]
        ticket["assigned_to"] = staff_name.strip()

        try:
            self.save_tickets()
        except OSError:
            ticket["assigned_to"] = previous_assignee
            raise

        return ticket

    def update_status(self, ticket_id, new_status):
        """Enforce the required ticket workflow."""

        if not isinstance(new_status, str):
            raise ValueError("Status must be a string.")

        new_status = new_status.strip().lower()

        if new_status not in self.VALID_STATUSES:
            raise ValueError(
                "Choose open, in_progress, or resolved."
            )

        ticket = self._find_ticket(ticket_id)

        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found.")

        current_status = ticket["status"]

        if new_status == current_status:
            raise ValueError(
                f"Ticket {ticket_id} is already {current_status}."
            )

        if new_status == "in_progress":
            if current_status != "open":
                raise ValueError(
                    "Only open tickets can move to in_progress."
                )

            if not ticket["assigned_to"]:
                raise ValueError(
                    "Assign the ticket before moving it to in_progress."
                )

        elif new_status == "resolved":
            if current_status != "in_progress":
                raise ValueError(
                    "Only in_progress tickets can be resolved."
                )

        elif new_status == "open":
            if current_status != "resolved":
                raise ValueError(
                    "Only resolved tickets can be reopened."
                )

        previous_status = ticket["status"]
        ticket["status"] = new_status

        try:
            self.save_tickets()
        except OSError:
            ticket["status"] = previous_status
            raise

        return ticket

    def get_work_queue(self):
        """Return open tickets by priority and then ticket ID."""

        open_tickets = [
            ticket
            for ticket in self.tickets
            if ticket["status"] == "open"
        ]

        return sorted(
            open_tickets,
            key=lambda ticket: (
                self.PRIORITY_ORDER[ticket["priority"]],
                int(ticket["id"][1:]),
            ),
        )

    def generate_report(self):
        """Return ticket totals grouped by status and priority."""

        report = {
            "total_tickets": len(self.tickets),
            "by_status": {
                status: 0
                for status in sorted(self.VALID_STATUSES)
            },
            "by_priority": {
                priority: 0
                for priority in self.PRIORITY_ORDER
            },
        }

        for ticket in self.tickets:
            report["by_status"][ticket["status"]] += 1
            report["by_priority"][ticket["priority"]] += 1

        return report

    def save_tickets(self):
        """Save tickets safely using a temporary file."""

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
        """Load and validate all saved tickets."""

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

        required_fields = {
            "id",
            "title",
            "category",
            "urgency",
            "affected_users",
            "priority",
            "status",
            "assigned_to",
        }

        # Validate everything before changing the manager's state.
        for ticket in loaded_tickets:
            if not isinstance(ticket, dict):
                raise ValueError("Every ticket must be a JSON object.")

            if not required_fields.issubset(ticket):
                raise ValueError(
                    "A ticket is missing required fields."
                )

            ticket_id = ticket["id"]

            if (
                not isinstance(ticket_id, str)
                or not re.fullmatch(r"T\d{3,}", ticket_id)
            ):
                raise ValueError(
                    "Ticket IDs must follow the format T001, T002, etc."
                )

            if ticket_id in seen_ids:
                raise ValueError(f"Duplicate ticket ID: {ticket_id}")

            seen_ids.add(ticket_id)

            if (
                not isinstance(ticket["title"], str)
                or not ticket["title"].strip()
            ):
                raise ValueError(
                    f"Ticket {ticket_id} must have a title."
                )

            category = ticket["category"]

            if (
                not isinstance(category, str)
                or category.casefold() not in self.CATEGORIES
            ):
                raise ValueError(
                    f"Invalid category for ticket {ticket_id}."
                )

            urgency = ticket["urgency"]

            if (
                not isinstance(urgency, str)
                or urgency not in self.URGENCIES
            ):
                raise ValueError(
                    f"Invalid urgency for ticket {ticket_id}."
                )

            affected_users = ticket["affected_users"]

            if (
                isinstance(affected_users, bool)
                or not isinstance(affected_users, int)
                or affected_users < 1
            ):
                raise ValueError(
                    f"Invalid affected-user count for ticket {ticket_id}."
                )

            expected_priority = self.calculate_priority(
                urgency, affected_users
            )

            if ticket["priority"] != expected_priority:
                raise ValueError(
                    f"Incorrect priority for ticket {ticket_id}."
                )

            if ticket["status"] not in self.VALID_STATUSES:
                raise ValueError(
                    f"Invalid status for ticket {ticket_id}."
                )

            assignee = ticket["assigned_to"]

            if assignee is not None and (
                not isinstance(assignee, str) or not assignee.strip()
            ):
                raise ValueError(
                    f"Invalid assignee for ticket {ticket_id}."
                )

        self.tickets = loaded_tickets

        if self.tickets:
            self.next_id = max(
                int(ticket["id"][1:]) for ticket in self.tickets
            ) + 1