"""Pure validation helpers for CampusFlow.

Nothing here reads input, prints, saves files or touches ticket state.
Every function either returns a clean value or raises ValueError, so callers
can validate *before* they mutate anything.
"""

import re

CATEGORIES = {
    "network": "Network",
    "hardware": "Hardware",
    "software": "Software",
    "other": "Other",
}
URGENCIES = ("low", "medium", "high")
PRIORITIES = ("critical", "high", "medium", "low")  # most important first
STATUSES = ("open", "in_progress", "resolved")

# Workflow: open -> in_progress -> resolved -> (reopen) open
ALLOWED_TRANSITIONS = {
    "open": {"in_progress"},
    "in_progress": {"resolved"},
    "resolved": {"open"},
}

TICKET_ID = re.compile(r"T\d{3,}")
NOTE_ID = re.compile(r"N\d{3,}")
MESSAGE_MIN, MESSAGE_MAX = 5, 300

TICKET_FIELDS = (
    "id", "title", "category", "urgency",
    "affected_users", "priority", "status", "assigned_to",
)


def _clean_text(value, error):
    """Return value stripped, or raise ValueError(error) if blank/not text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error)
    return value.strip()


def validate_title(title):
    return _clean_text(title, "Ticket title is required.")


def validate_label(value, what):
    """Validate a person label such as a staff name or note author."""
    return _clean_text(value, f"{what} cannot be empty.")


def validate_category(category):
    """Return the canonical category name (e.g. ' network ' -> 'Network')."""
    error = "Category must be Network, Hardware, Software, or Other."
    key = _clean_text(category, error).casefold()
    if key not in CATEGORIES:
        raise ValueError(error)
    return CATEGORIES[key]


def validate_urgency(urgency):
    error = "Urgency must be low, medium, or high."
    value = _clean_text(urgency, error).lower()
    if value not in URGENCIES:
        raise ValueError(error)
    return value


def validate_status(status):
    error = "Status must be open, in_progress, or resolved."
    value = _clean_text(status, error).lower()
    if value not in STATUSES:
        raise ValueError(error)
    return value


def validate_priority(priority):
    error = "Priority must be critical, high, medium, or low."
    value = _clean_text(priority, error).lower()
    if value not in PRIORITIES:
        raise ValueError(error)
    return value


def validate_affected_users(count):
    """Strictly positive int. bool is a subclass of int, so reject it."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("Affected users must be a positive whole number.")
    return count


def validate_message(message):
    text = _clean_text(
        message, f"Note message must be {MESSAGE_MIN}-{MESSAGE_MAX} characters."
    )
    if not MESSAGE_MIN <= len(text) <= MESSAGE_MAX:
        raise ValueError(
            f"Note message must be {MESSAGE_MIN}-{MESSAGE_MAX} characters."
        )
    return text


def calculate_priority(urgency, affected_users):
    """Priority rules, checked in this order (first match wins)."""
    urgency = validate_urgency(urgency)
    affected_users = validate_affected_users(affected_users)

    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def check_transition(current, new, assigned_to):
    """Raise ValueError unless current -> new is a legal workflow step.

    Pure: only looks at its arguments, never changes anything.
    """
    if new == current:
        raise ValueError(f"The ticket is already {current}.")
    if new not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"A {current} ticket cannot move to {new}.")
    if new == "in_progress" and not assigned_to:
        raise ValueError("Assign the ticket before moving it to in_progress.")


def validate_note_record(note, seen_ids):
    """Check one stored note; return a clean copy."""
    if not isinstance(note, dict) or set(note) != {"note_id", "author", "message"}:
        raise ValueError("Each note needs exactly note_id, author and message.")
    note_id = note["note_id"]
    if not isinstance(note_id, str) or not NOTE_ID.fullmatch(note_id):
        raise ValueError("Note IDs must follow the format N001, N002, etc.")
    if note_id in seen_ids:
        raise ValueError(f"Duplicate note ID: {note_id}")
    seen_ids.add(note_id)
    return {
        "note_id": note_id,
        "author": validate_label(note["author"], "Note author"),
        "message": validate_message(note["message"]),
    }


def validate_ticket_record(record):
    """Check one ticket loaded from JSON; return a clean, normalised copy.

    Tickets saved before notes existed have no "notes" key; they get [].
    """
    if not isinstance(record, dict):
        raise ValueError("Every ticket must be a JSON object.")
    missing = [name for name in TICKET_FIELDS if name not in record]
    if missing:
        raise ValueError(f"A ticket is missing fields: {', '.join(missing)}.")

    ticket_id = record["id"]
    if not isinstance(ticket_id, str) or not TICKET_ID.fullmatch(ticket_id):
        raise ValueError("Ticket IDs must follow the format T001, T002, etc.")

    try:
        urgency = record["urgency"]
        if urgency not in URGENCIES:
            raise ValueError("Urgency must be low, medium, or high.")
        affected = validate_affected_users(record["affected_users"])
        if record["priority"] != calculate_priority(urgency, affected):
            raise ValueError("Priority does not match urgency and affected users.")
        if record["status"] not in STATUSES:
            raise ValueError("Status must be open, in_progress, or resolved.")

        assignee = record["assigned_to"]
        if assignee is not None:
            assignee = validate_label(assignee, "Assignee")

        notes = record.get("notes", [])
        if not isinstance(notes, list):
            raise ValueError("Notes must be a list.")
        seen_note_ids = set()

        return {
            "id": ticket_id,
            "title": validate_title(record["title"]),
            "category": validate_category(record["category"]),
            "urgency": urgency,
            "affected_users": affected,
            "priority": record["priority"],
            "status": record["status"],
            "assigned_to": assignee,
            "notes": [validate_note_record(n, seen_note_ids) for n in notes],
        }
    except ValueError as error:
        raise ValueError(f"Ticket {ticket_id}: {error}") from error
