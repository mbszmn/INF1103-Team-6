from dotenv import load_dotenv

# load the api key frm .env file
load_dotenv()

# import the managers
from managers import IOManager
from managers.ai_manager import analyse_ticket  
from managers.logic_manager import process_ticket
from managers import data_manager
from models.ticket import create_ticket


def submit_ticket(tickets, io_manager):
    try:
        user_input = io_manager.collect_ticket_input()

        # make the ticket with the next free id
        ticket = create_ticket(
            ticket_id=data_manager.generate_ticket_id(tickets),
            username=user_input["username"],
            student_id=user_input["student_id"],
            device=user_input["device"],
            title=user_input["title"],
            description=user_input["description"],
            steps_attempted=user_input["steps_attempted"],
            user_priority=user_input["user_priority"],
            error_message=user_input["error_message"],
        )

        io_manager.display_message("\nAnalysing ticket with AI...")

        # function call to AI Manager
        ai_analysis = analyse_ticket(
            title=ticket["title"],
            description=ticket["description"],
            device=ticket["device"],
            error_message=ticket["error_message"],
            steps_attempted=ticket["steps_attempted"]
        )

        # Apply business logic rules frm logic_manager
        processed_result = process_ticket(ai_analysis)

        if processed_result.get("action") == "REJECT":
            io_manager.display_message("ERROR: AI response failed validation rules.")
            return

        # save the ticket together with the ai result
        data_manager.attach_ai_result(ticket, processed_result)
        if data_manager.add_ticket(tickets, ticket):
            io_manager.display_submission_result(ticket)
                    
    except ValueError as error:
        io_manager.display_message(f"ERROR: {error}")

def main():
    io_manager = IOManager()
    io_manager.show_welcome()

    tickets = data_manager.load_tickets()

    while True:
        option = io_manager.get_menu_option()
        if option == "1":
            submit_ticket(tickets, io_manager)
        elif option == "2":
            data_manager.display_all(tickets)
        elif option == "3":
            ticket_id = io_manager.get_ticket_id()
            ticket = data_manager.find_ticket(tickets, ticket_id)
            if ticket is None:
                io_manager.display_message(f"Ticket {ticket_id} not found.")
            else:
                data_manager.display_ticket(ticket)
        elif option == "4":
            ticket_id = io_manager.get_ticket_id("Enter ticket ID to close: ")
            data_manager.close_ticket(tickets, ticket_id)
        elif option == "5":
            ticket_id = io_manager.get_ticket_id("Enter ticket ID to reopen: ")
            data_manager.reopen_ticket(tickets, ticket_id)
        elif option == "6":
            data_manager.export_tickets_csv(tickets)
        elif option == "7":
            io_manager.display_message("\nThank you for using the Helpdesk Ticket Triage System.")
            break
        else:
            io_manager.display_message("Invalid option, please pick 1 to 7.")


if __name__ == "__main__":
    main()