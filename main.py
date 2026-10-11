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
        print(f"\nCould not start Campus Flow: {error}")
        return

    while True:
        print("\n===== CAMPUS FLOW =====")
        print("1. Create a ticket")
        print("2. View all tickets")
        print("3. Search tickets")
        print("4. Assign a ticket")
        print("5. View work queue")
        print("6. Exit")

        choice = input("Choose an option: ").strip()

        # F1: Create a ticket
        if choice == "1":
            title = input("Enter ticket title: ")
            description = input("Enter ticket description: ")

            try:
                ticket = manager.create_ticket(title, description)

                print("\nTicket created successfully!")
                display_ticket(ticket)

            except ValueError as error:
                print(f"\nError: {error}")

            except OSError:
                print("\nError: Could not save the ticket.")

        # F2: View all tickets
        elif choice == "2":
            if not manager.tickets:
                print("\nNo tickets have been created yet.")
            else:
                print("\n===== ALL TICKETS =====")

                for ticket in manager.tickets:
                    display_ticket(ticket)

        # Search tickets by ID or title
        elif choice == "3":
            query = input("Enter ticket ID or title: ")

            try:
                matches = manager.search_tickets(query)

                if not matches:
                    print("\nNo matching tickets found.")
                else:
                    print(f"\nFound {len(matches)} matching ticket(s):")

                    for ticket in matches:
                        display_ticket(ticket)

            except ValueError as error:
                print(f"\nError: {error}")

        # F3: Assign a ticket to a staff member
        elif choice == "4":
            ticket_id = input("Enter ticket ID: ").strip()
            staff_name = input("Enter staff member's name: ")

            try:
                ticket = manager.assign_ticket(ticket_id, staff_name)

                print("\nTicket assigned successfully!")
                display_ticket(ticket)

            except ValueError as error:
                print(f"\nError: {error}")

            except OSError:
                print("\nError: Could not save the assignment.")

        # F5: View the work queue
        elif choice == "5":
            queue = manager.get_work_queue()

            if not queue:
                print("\nThe work queue is empty.")
            else:
                print("\n===== OPEN TICKET WORK QUEUE =====")

                for position, ticket in enumerate(queue, start=1):
                    print(f"\nQueue position: {position}")
                    display_ticket(ticket)

        # Exit
        elif choice == "6":
            print("\nThank you for using Campus Flow.")
            break

        else:
            print("\nInvalid option. Please choose from 1 to 6.")


if __name__ == "__main__":
    main()