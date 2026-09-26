from managers.io_manager import IOManager

def submit_ticket(io_manager: IOManager):

    try: 
        user_input = io_manager.collect_ticket_input()
        ticket = io_manager.create_ticket(user_input)
        io_manager.save_new_ticket(ticket)

        print(f"\nTicket {ticket.ticket_id} created.")

    except ValueError as error:
        print("ERROR")

submit_ticket(IOManager())