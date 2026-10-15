# Campus Flow Next

Campus Flow is a Python command-line ticket manager for campus support staff.
It uses only the Python standard library and stores tickets in a JSON file.

## Run it

```bash
python main.py                              # start the app (creates tickets.json)
python -m unittest discover -s tests -v     # run all tests (works from a fresh clone)
```

Requires Python 3.8 or newer. No packages to install.

## Features

- **Create tickets** with title, category, urgency and affected users.
  Priority is calculated (first matching rule wins): `critical` = high urgency
  and 10+ users; `high` = high urgency or 10+ users; `medium` = medium urgency
  or 3+ users; otherwise `low`.
- **Assign** tickets and move them through the workflow
  `open -> in_progress -> resolved`, and `resolved -> open` (reopen).
  An unassigned ticket cannot start work. Resolved tickets cannot be assigned
  or given notes until reopened.
- **Follow-up notes**: add and view notes (`N001`, `N002`, ...) on open or
  in-progress tickets. Author must not be blank; message must be 5-300
  characters after trimming. Notes are kept when a ticket is resolved or reopened.
- **Search**: case-insensitive title substring plus optional category, status
  and priority filters. All supplied filters must match (AND). Blank = no filter.
  A second menu option shows the same results sorted by priority, then ticket number.
- **Open work queue**: open tickets only, critical first, ties by ticket number.
- **Report**: total, unresolved (open + in_progress), resolved, resolution
  percentage (0% when empty), and counts by status, priority and category.
- **Engineering Understanding Check**: six multiple-choice questions about this
  app, scored 0-6, with two written explanations saved to `learning_notes.txt`.
- **Safe JSON**: a rejected action never changes data; a bad file never
  replaces what is in memory.

## Menu

`1` Create - `2` View all - `3` Search - `4` Search sorted by priority -
`5` Assign - `6` Open work queue - `7` Update status - `8` Add note -
`9` View notes - `10` Report - `11` Understanding check - `12` Exit

## Data file format (`tickets.json`)

A JSON **list** of ticket objects:

```json
[
    {
        "id": "T001",
        "title": "Wi-Fi down in library",
        "category": "Network",
        "urgency": "high",
        "affected_users": 12,
        "priority": "critical",
        "status": "in_progress",
        "assigned_to": "Operator A",
        "notes": [
            {"note_id": "N001", "author": "Mentor A", "message": "Router reboot attempted"}
        ]
    }
]
```

- Version 1 files (no `"notes"` key) still load; each ticket gets `"notes": []`.
  No migration is needed and the old file is not rewritten until you save a change.
- On load the **whole file is validated first**: JSON syntax, list shape, required
  keys, ticket ID format and uniqueness, category/urgency, positive integer
  `affected_users`, priority matching the rules, legal status, and note shape,
  ID format, uniqueness per ticket, author and message length.
  If anything is wrong the load is rejected with a clear message and memory is unchanged.
- Next ticket/note IDs are the highest existing number + 1 (numeric, so `T10` follows `T9`).

## Project structure

```text
campus_flow/
    validation.py          pure validation, priority rules, workflow table
    tickets.py             TicketManager: tickets, notes, save/load
    search.py              read-only combined-filter search and priority sort
    reports.py             report statistics
    understanding_check.py question bank, scoring, quiz runner
    cli.py                 menus (input/output injected, so it is testable)
main.py                    entry point
tests/                     unittest suites (run with discover -s tests)
docs/                      baseline-check, design decisions, AI learning log
```

## Error convention

Invalid input raises `ValueError` (message is shown to the user by the CLI).
File problems raise `OSError`. A failed save undoes the in-memory change.