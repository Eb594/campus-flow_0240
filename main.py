from campus_flow.tickets import TicketManager


def main():
    manager = TicketManager()

    while True:
        print("\n===== CAMPUS FLOW =====")
        print("1. Create a ticket")
        print("2. View all tickets")
        print("3. Search tickets")
        print("4. Exit")

        choice = input("Choose an option: ").strip()

        # Create a ticket
        if choice == "1":
            title = input("Enter ticket title: ")
            description = input("Enter ticket description: ")

            try:
                ticket = manager.create_ticket(title, description)

                print("\nTicket created successfully!")
                print(f"Ticket ID: {ticket['id']}")
                print(f"Title: {ticket['title']}")
                print(f"Priority: {ticket['priority']}")
                print(f"Status: {ticket['status']}")

            except ValueError as error:
                print(f"\nError: {error}")

            except OSError:
                print("\nError: Could not save the ticket.")

        # View all tickets
        elif choice == "2":
            if not manager.tickets:
                print("\nNo tickets have been created yet.")
            else:
                print("\n===== ALL TICKETS =====")

                for ticket in manager.tickets:
                    print(f"\nID: {ticket['id']}")
                    print(f"Title: {ticket['title']}")
                    print(f"Description: {ticket['description']}")
                    print(f"Priority: {ticket['priority']}")
                    print(f"Status: {ticket['status']}")
                    print(f"Assignee: {ticket['assignee']}")

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
                        print(f"\nID: {ticket['id']}")
                        print(f"Title: {ticket['title']}")
                        print(f"Description: {ticket['description']}")
                        print(f"Priority: {ticket['priority']}")
                        print(f"Status: {ticket['status']}")
                        print(f"Assignee: {ticket['assignee']}")

            except ValueError as error:
                print(f"\nError: {error}")

        # Exit the application
        elif choice == "4":
            print("Thank you for using Campus Flow.")
            break

        else:
            print("Invalid option. Please choose 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()


