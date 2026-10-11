# Campus Flow

Campus Flow is a Python-based command-line ticket management system that helps teams create, prioritize, assign, track, and report on tickets. It stores ticket information in a JSON file so records can be restored when the application restarts.

## Features

- **Create Tickets:** Create tickets with a title and description, validate required fields, and generate unique ticket IDs.
- **Automatic Prioritization:** Automatically assign ticket priorities based on keywords in the title and description.
- **View Tickets:** Display all existing tickets.
- **Search Tickets:** Search for tickets by ID or title.
- **Assign Tickets:** Assign tickets to staff members.
- **Manage Ticket Status:** Track tickets through `open`, `in_progress`, and `resolved` statuses.
- **Prioritized Work Queue:** Display open tickets in priority order.
- **Generate Reports:** View ticket statistics grouped by status and priority.
- **Data Persistence:** Save and load ticket records using JSON.
- **Input Validation:** Handle invalid inputs, missing details, and unknown ticket IDs.

## Technologies Used

- Python 3
- JSON for data storage
- Unittest for automated testing
- Git and GitHub for version control

## Project Structure

```text
campus-flow_0240/
├── campus_flow/
│   ├── __init__.py
│   └── tickets.py
├── main.py
├── tests.py
├── test_workflow_reports.py
├── tickets.json
└── README.md