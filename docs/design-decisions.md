# Campus Flow — Design Decisions

## 1. Application Type

Campus Flow is implemented as a command-line application using Python.

### Reason

A command-line interface provides a simple way to create, assign,
update, search, and report on tickets without requiring a graphical
interface or external framework.

## 2. Ticket Data Structure

Tickets are represented as Python dictionaries and stored in a list.

Each ticket contains:

- id
- title
- category
- urgency
- affected_users
- priority
- status
- assigned_to

### Reason

A dictionary makes each ticket's information easy to access and update.
A list allows the application to manage multiple tickets.

## 3. Ticket Identifiers

Ticket IDs use a readable format such as T001, T002, and T003.

### Reason

Readable identifiers make tickets easier to reference in the command-line
interface.

The application tracks the next ID and checks saved tickets when loading
data so that new tickets can continue from the highest existing ID.

## 4. Input Validation

The application validates ticket titles, categories, urgency values,
and the number of affected users.

Staff names must not be empty, and operations must reference existing
ticket IDs.

### Reason

Validation prevents incomplete or invalid information from entering
the application.

## 5. Priority Calculation

Priority is calculated from urgency and the number of affected users.

The rules are:

1. High urgency and at least 10 affected users: critical.
2. High urgency or at least 10 affected users: high.
3. Medium urgency or at least 3 affected users: medium.
4. Otherwise: low.

### Reason

The rules provide a consistent way to determine which issues need
attention first.

Higher-priority tickets appear earlier in the work queue.

## 6. Ticket Workflow

Tickets use three statuses:

- open
- in_progress
- resolved

An unassigned ticket cannot move to in_progress. A ticket cannot move
directly from open to resolved. A resolved ticket must be explicitly
reopened before it can be modified.

### Reason

These restrictions help prevent invalid workflow transitions and make
ticket progress easier to manage.

## 7. Work Queue Ordering

The work queue includes open tickets and sorts them in this order:

1. Critical
2. High
3. Medium
4. Low

Tickets with equal priority are sorted by their numeric ticket IDs
in ascending order.

### Reason

This ensures that more urgent work appears first and provides a
consistent ordering for tickets with equal priority.

## 8. JSON Persistence

Ticket data is saved in a JSON file and loaded when the application
starts.

A missing file starts the application with no saved tickets. Malformed
JSON should produce a clear error rather than silently discarding data.

### Reason

JSON is human-readable and supported by Python's standard library.
It allows ticket information to survive application restarts without
requiring a database.

## 9. Automated Testing

The project uses Python's unittest module.

Tests cover creation, validation, assignment, workflow transitions,
priority ordering, reporting, and persistence.

### Reason

Automated tests help identify regressions and verify that important
requirements continue to work after code changes.

## 10. Standard Library

The implementation uses Python standard-library modules such as
json, pathlib, and unittest.

### Reason

The project can run without installing third-party Python packages.

## 11. Known Limitations

- The application is designed for local command-line use.
- JSON persistence is suitable for a small project but does not provide
  database-level concurrency control.
- The application does not currently provide a graphical interface.
- More extensive integration and invalid-data tests may be useful as
  the project grows.
