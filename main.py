from campus_flow.tickets import TicketManager


def display_ticket(ticket):
    """Display the details of one ticket."""

    print(f"\nID: {ticket['id']}")
    print(f"Title: {ticket['title']}")
    print(f"Description: {ticket['description']}")
    print(f"Priority: {ticket['priority']}")
    print(f"Status: {ticket['status']}")
    print(f"Assignee: {ticket['assignee'] or 'Unassigned'}")


def main():
    """Run the Campus Flow ticket management application."""

    try:
        manager = TicketManager()
    except (ValueError, OSError) as error:
        print(f"Could not load tickets: {error}")
        return

    while True:
        print("\n===== CAMPUS FLOW =====")
        print("1. Create ticket")
        print("2. View all tickets")
        print("3. Search tickets")
        print("4. Assign a ticket")
        print("5. View work queue")
        print("6. Update ticket status")
        print("7. Generate ticket report")
        print("8. Exit")

        choice = input("Choose an option (1-8): ").strip()

        try:
            if choice == "1":
                title = input("Enter ticket title: ")
                description = input("Enter ticket description: ")

                ticket = manager.create_ticket(title, description)

                print("\nTicket created successfully!")
                display_ticket(ticket)

            elif choice == "2":
                if not manager.tickets:
                    print("No tickets found.")
                    continue

                for ticket in manager.tickets:
                    display_ticket(ticket)

            elif choice == "3":
                query = input("Enter ticket ID or title: ")
                results = manager.search_tickets(query)

                if results:
                    for ticket in results:
                        display_ticket(ticket)
                else:
                    print("No matching tickets found.")

            elif choice == "4":
                ticket_id = input("Enter ticket ID: ")
                staff_name = input("Enter staff member's name: ")

                ticket = manager.assign_ticket(ticket_id, staff_name)

                print("\nTicket assigned successfully!")
                display_ticket(ticket)

            elif choice == "5":
                queue = manager.get_work_queue()

                if not queue:
                    print("There are no open tickets in the work queue.")
                    continue

                print("\n===== WORK QUEUE =====")

                for ticket in queue:
                    display_ticket(ticket)

            elif choice == "6":
                ticket_id = input("Enter ticket ID: ")
                print("Available statuses: open, in_progress, resolved")
                new_status = input("Enter the new status: ")

                ticket = manager.update_status(ticket_id, new_status)

                print("\nTicket status updated successfully!")
                display_ticket(ticket)

            elif choice == "7":
                report = manager.generate_report()

                print("\n===== TICKET REPORT =====")
                print(f"Total tickets: {report['total_tickets']}")

                print("\nTickets by status:")
                for status, count in report["by_status"].items():
                    print(f"  {status}: {count}")

                print("\nTickets by priority:")
                for priority, count in report["by_priority"].items():
                    print(f"  {priority}: {count}")

            elif choice == "8":
                print("Thank you for using Campus Flow!")
                break

            else:
                print("Invalid choice. Please select an option from 1 to 8.")

        except (ValueError, OSError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()