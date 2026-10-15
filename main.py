from campus_flow.quiz import run_quiz, save_explanations
from campus_flow.tickets import TicketManager


def display_ticket(ticket):
    """Display the details of one ticket."""

    print(f"\nID: {ticket['id']}")
    print(f"Title: {ticket['title']}")
    print(f"Category: {ticket['category']}")
    print(f"Urgency: {ticket['urgency']}")
    print(f"Affected users: {ticket['affected_users']}")
    print(f"Priority: {ticket['priority']}")
    print(f"Status: {ticket['status']}")
    print(f"Assigned to: {ticket['assigned_to'] or 'Unassigned'}")


def display_search_result(ticket):
    """Display the fields required for search results."""

    print(
        f"{ticket['id']} | {ticket['title']} | {ticket['category']} | "
        f"{ticket['priority']} | {ticket['status']} | "
        f"{ticket['assigned_to'] or 'Unassigned'}"
    )


def prompt_filter(label, normalizer):
    """Ask for an optional filter, re-prompting until valid or blank."""

    while True:
        value = input(f"{label} (press Enter to skip): ")

        try:
            return normalizer(value)
        except ValueError as error:
            print(f"Error: {error}")


def prompt_affected_users():
    """Read a whole number, with a friendly message if invalid."""

    raw = input("Enter number of affected users: ").strip()

    try:
        return int(raw)
    except ValueError:
        raise ValueError(
            "Affected users must be a whole number, e.g. 5."
        ) from None


def search_menu(manager):
    """Search tickets with optional filters."""

    title = input("Title contains (press Enter to skip): ")

    category = prompt_filter(
        "Category (Network/Hardware/Software/Other)",
        manager.normalize_category_filter,
    )

    status = prompt_filter(
        "Status (open/in_progress/resolved)",
        manager.normalize_status_filter,
    )

    priority = prompt_filter(
        "Priority (critical/high/medium/low)",
        manager.normalize_priority_filter,
    )

    results = manager.search_filtered(
        title, category, status, priority
    )

    if not results:
        print("No matching tickets found.")
        return

    print("\n===== SEARCH RESULTS =====")
    print("ID | Title | Category | Priority | Status | Assigned to")

    for ticket in results:
        display_search_result(ticket)

    view = input(
        "\nShow results sorted by priority? (y/n): "
    ).strip().lower()

    if view == "y":
        print("\n===== SEARCH RESULTS (BY PRIORITY) =====")

        for ticket in manager.sort_by_priority(results):
            display_search_result(ticket)


def show_report(manager):
    """Display the ticket report."""

    report = manager.generate_report()

    print("\n===== TICKET REPORT =====")
    print(f"Total tickets: {report['total_tickets']}")

    print("\nTickets by status:")
    for status, count in report["by_status"].items():
        print(f"  {status}: {count}")

    print("\nTickets by priority:")
    for priority, count in report["by_priority"].items():
        print(f"  {priority}: {count}")

    print("\nTickets by category:")
    for category, count in report["by_category"].items():
        print(f"  {category}: {count}")

    print(
        f"\nUnresolved (open + in_progress): "
        f"{report['unresolved']}"
    )

    print(f"Resolved: {report['resolved']}")
    print(f"Resolution rate: {report['resolution_percentage']}%")


def quiz_menu():
    """Run the engineering understanding quiz."""

    result = run_quiz()

    if result.explanations:
        print(
            "\n===== YOUR EXPLANATIONS "
            "(for mentor discussion) ====="
        )

        for item in result.explanations:
            print(
                f"Q{item['question']} ({item['scenario']}): "
                f"{item['explanation']}"
            )

        path = save_explanations(result)
        print(f"\nExplanations saved to {path}.")


def main():
    """Run the Campus Flow application."""

    try:
        manager = TicketManager()
    except (ValueError, OSError) as error:
        print(f"Could not load tickets: {error}")
        return

    while True:
        print("\n===== CAMPUS FLOW =====")
        print("1. Create ticket")
        print("2. View all tickets")
        print("3. Search tickets (title + filters)")
        print("4. Assign a ticket")
        print("5. View work queue")
        print("6. Update ticket status")
        print("7. Generate ticket report")
        print("8. Add follow-up note")
        print("9. View ticket notes")
        print("10. Engineering understanding check")
        print("11. Exit")

        choice = input(
            "Choose an option (1-11): "
        ).strip()

        try:
            if choice == "1":
                title = input("Enter ticket title: ")

                category = input(
                    "Enter category "
                    "(Network/Hardware/Software/Other): "
                )

                urgency = input(
                    "Enter urgency (low/medium/high): "
                )

                affected_users = prompt_affected_users()

                ticket = manager.create_ticket(
                    title,
                    category,
                    urgency,
                    affected_users,
                )

                print("\nTicket created successfully!")
                display_ticket(ticket)

            elif choice == "2":
                if not manager.tickets:
                    print("No tickets found.")
                    continue

                for ticket in manager.tickets:
                    display_ticket(ticket)

            elif choice == "3":
                search_menu(manager)

            elif choice == "4":
                ticket_id = input(
                    "Enter ticket ID (e.g. T001): "
                )

                staff_name = input(
                    "Enter staff member's name: "
                )

                ticket = manager.assign_ticket(
                    ticket_id, staff_name
                )

                print("\nTicket assigned successfully!")
                display_ticket(ticket)

            elif choice == "5":
                queue = manager.get_work_queue()

                if not queue:
                    print(
                        "There are no open tickets "
                        "in the work queue."
                    )
                    continue

                print("\n===== WORK QUEUE =====")

                for ticket in queue:
                    display_ticket(ticket)

            elif choice == "6":
                ticket_id = input(
                    "Enter ticket ID (e.g. T001): "
                )

                print(
                    "Available statuses: "
                    "open, in_progress, resolved"
                )

                new_status = input(
                    "Enter the new status: "
                )

                ticket = manager.update_status(
                    ticket_id, new_status
                )

                print(
                    "\nTicket status updated successfully!"
                )

                display_ticket(ticket)

            elif choice == "7":
                show_report(manager)

            elif choice == "8":
                ticket_id = input("Enter ticket ID (e.g. T001): ")
                message = input("Enter your follow-up note: ")

                try:
                    note = manager.add_note(
                        ticket_id,
                        "Campus Flow user",
                        message
                    )
                    note_number = int(note["note_id"][1:])
                    print(f"\\nNote {note_number} added successfully!")
                except (ValueError, OSError) as error:
                    print(f"Error: {error}")

            elif choice == "9":
                ticket_id = input("Enter ticket ID (e.g. T001): ")

                try:
                    notes = manager.get_notes(ticket_id)

                    if not notes:
                        print("This ticket has no notes yet.")
                        continue

                    print(f"\\n===== NOTES FOR {ticket_id.strip().upper()} =====")

                    for note in notes:
                        note_number = int(note["note_id"][1:])
                        print(f"[{note_number}] {note['message']}")

                except ValueError as error:
                    print(f"Error: {error}")

            elif choice == "10":
                quiz_menu()

            elif choice == "11":
                print("Thank you for using Campus Flow!")
                break

            else:
                print(
                    "Invalid choice. "
                    "Please select an option from 1 to 11."
                )

        except ValueError as error:
            print(f"Error: {error}")

        except OSError as error:
            print(f"File operation failed: {error}")


if __name__ == "__main__":
    main()