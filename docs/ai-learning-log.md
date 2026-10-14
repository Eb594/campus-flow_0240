# Campus Flow — AI Learning Log

## Project Overview

Campus Flow is a command-line ticket management application.
It helps users create and manage tickets, assign tickets to staff,
track ticket progress, prioritize issues, and generate reports.

## Purpose of Using AI

AI was used as a learning assistant during development. It helped me
understand Python concepts, identify errors, improve code organization,
and develop automated tests.

AI suggestions were reviewed and tested before being accepted.

## Development Activities

### 1. Ticket Creation

AI helped me understand how to:

- Collect ticket information from users.
- Validate required fields.
- Store tickets using Python dictionaries.
- Generate unique ticket IDs.
- Calculate ticket priority from urgency and affected users.
- Reject invalid input without creating incomplete tickets.

**What I learned:**

I learned how functions, dictionaries, conditional statements, and
exceptions can work together to create and validate tickets.

### 2. Ticket Assignment

AI helped me understand how to assign tickets to staff members and
reject invalid ticket IDs or empty staff names.

**What I learned:**

I learned how to find a ticket by its ID, update its fields, and validate
user input before changing application data.

### 3. Ticket Workflow

AI helped me implement and test ticket status transitions.

The workflow uses these statuses:

- open
- in_progress
- resolved

**What I learned:**

I learned why applications need rules that control state changes.
For example, an unassigned ticket must not move to in_progress, and an
open ticket must not be resolved directly.

### 4. Work Queue

AI helped me implement a queue that sorts open tickets by priority.

**What I learned:**

I learned how sorting functions and priority mappings can be used to
order tickets consistently. Tickets with equal priority are ordered by
their numeric ticket IDs.

### 5. JSON Persistence

AI helped me understand how to save tickets to a JSON file and reload
them when the application starts.

**What I learned:**

I learned how to use Python's json module, handle missing files, detect
malformed JSON, and preserve ticket IDs between application sessions.

### 6. Automated Testing

AI helped me write and improve unit tests using Python's unittest module.

The tests cover ticket creation, validation, priority calculation,
assignment, workflow rules, queue ordering, reporting, and persistence.

**What I learned:**

I learned how automated tests detect errors and verify that application
features behave as expected.

The test suite passed 31 tests during development.

## Challenges Encountered

Some challenges included:

- Updating tests when the ticket data structure changed.
- Correcting function calls that used outdated arguments.
- Handling JSON files and invalid saved data.
- Maintaining ticket ID uniqueness after reloading.
- Debugging Python errors using terminal output.

## How I Used AI Responsibly

- I used AI explanations to improve my understanding of Python.
- I reviewed suggested code instead of accepting every suggestion
  without testing it.
- I ran automated tests after making changes.
- I used error messages to identify and correct problems.
- I remained responsible for understanding and verifying the final
  implementation.

## Reflection

This project helped me understand how individual Python functions
combine to form a complete application.

It also improved my understanding of validation, exception handling,
file operations, JSON persistence, application workflows, and automated
testing.

My next goal is to become more confident implementing features
independently and explaining the decisions behind my code.
