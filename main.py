from dotenv import load_dotenv

# load the api key frm .env file
load_dotenv()

# import the managers
from managers.io_manager import IOManager
from managers.ai_manager import AIManager
from managers.logic_manager import process_ticket
from managers import data_manager
from models.ticket import create_ticket


def submit_ticket(io_manager: IOManager, ai_manager: AIManager, tickets: list):
    try:
        user_input = io_manager.collect_ticket_input()

        # make the ticket with the next free id
        ticket = create_ticket(
            ticket_id=data_manager.generate_ticket_id(tickets),
            username=user_input["username"],
            device=user_input["device"],
            title=user_input["title"],
            description=user_input["description"],
            steps_attempted=user_input["steps_attempted"],
            user_priority=user_input["user_priority"],
            error_message=user_input["error_message"],
        )

        print("\nAnalyzing ticket with AI...")

        # Pass along the fields frm the tix to the AI manager
        ai_analysis = ai_manager.analyze_ticket(
            title=ticket["title"],
            description=ticket["description"],
            device=ticket["device"],
            error_message=ticket["error_message"],
            steps_attempted=ticket["steps_attempted"]
        )

        # Apply business logic rules frm logic_manager
        processed_result = process_ticket(ai_analysis)

        if processed_result.get("action") == "REJECT":
            print("ERROR: AI response failed validation rules.")
            return

        # save the ticket together with the ai result
        data_manager.attach_ai_result(ticket, processed_result)
        if data_manager.add_ticket(tickets, ticket):
            print(f"\nTicket {ticket['ticket_id']} successfully processed and saved!")
            print(f"Category: {processed_result['category']} | Priority: {ticket['final_priority']}")

    except ValueError as error:
        print(f"ERROR: {error}")


def show_menu():
    print("\n----------- MENU -----------")
    print("1. Submit New Ticket")
    print("2. View All Tickets")
    print("3. Search Ticket by ID")
    print("4. Close Ticket")
    print("5. Reopen Ticket")
    print("6. Export Tickets to CSV")
    print("7. Exit")
    print("----------------------------")


def main():
    print("========================================")
    print("AI SIT HELPDESK TICKET TRIAGE SYSTEM")
    print("========================================\n")

    io_mgr = IOManager()
    ai_mgr = AIManager()
    tickets = data_manager.load_tickets()
    show_menu()

    while True:
        option = input("\nEnter option: ")
        if option == "1":
            submit_ticket(io_mgr, ai_mgr, tickets)
        elif option == "2":
            data_manager.display_all(tickets)
        elif option == "3":
            ticket_id = input("Enter ticket ID: ")
            ticket = data_manager.find_ticket(tickets, ticket_id)
            if ticket == None:
                print("Ticket", ticket_id, "not found.")
            else:
                data_manager.display_ticket(ticket)
        elif option == "4":
            ticket_id = input("Enter ticket ID to close: ")
            data_manager.close_ticket(tickets, ticket_id)
        elif option == "5":
            ticket_id = input("Enter ticket ID to reopen: ")
            data_manager.reopen_ticket(tickets, ticket_id)
        elif option == "6":
            data_manager.export_tickets_csv(tickets)
        elif option == "7":
            print("\nThank you for using the Helpdesk Ticket Triage System.")
            break
        else:
            print("Invalid option, please pick 1 to 7.")
            show_menu()


if __name__ == "__main__":
    main()
