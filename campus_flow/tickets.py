import json
from pathlib import Path


class TicketManager:
    """Manage ticket creation, storage, and persistence."""

    def __init__(self, file_path="tickets.json"):
        self.file_path = Path(file_path)
        self.tickets = []
        self.next_id = 1
        self.load_tickets()

    def calculate_priority(self, title, description):
        """Calculate priority using keyword rules."""

        text = f"{title} {description}".lower()

        high_priority_words = ["urgent", "critical", "emergency", "danger"]
        medium_priority_words = ["broken", "failure", "error", "problem"]

        if any(word in text for word in high_priority_words):
            return "high"

        if any(word in text for word in medium_priority_words):
            return "medium"

        return "low"

    def create_ticket(self, title, description):
        """Validate and create a ticket."""

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
        matches = []

        for ticket in self.tickets:
            if (
                str(ticket["id"]) == query
                or query.casefold() in ticket["title"].casefold()
            ):
                matches.append(ticket)

        return matches
        
    def save_tickets(self):
        """Save tickets to a JSON file."""

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(self.tickets, file, indent=4)  

    def load_tickets(self):
        """Load previously saved tickets."""

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
            raise ValueError("The ticket data file must contain a list.")

        self.tickets = loaded_tickets

        if self.tickets:
            self.next_id = max(ticket["id"] for ticket in self.tickets) + 1

