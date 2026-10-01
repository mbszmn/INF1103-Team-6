from managers.io_manager import IOManager
from managers.ai_manager import AIManager
from managers.logic_manager import process_ticket

def submit_ticket(io_manager: IOManager, ai_manager: AIManager):
    try: 
        user_input = io_manager.collect_ticket_input()
        ticket = io_manager.create_ticket(user_input)
        
        print("\nAnalyzing ticket with AI...")

        # Pass along the fields frm the tix to the AI manager
        ai_analysis = ai_manager.analyze_ticket(
            title=ticket.title,
            description=ticket.description,
            device=ticket.device,
            error_message=ticket.error_message,
            steps_attempted=ticket.steps_attempted
        )
        
        # Apply business logic rules frm logic_manager
        processed_result = process_ticket(ai_analysis)
        
        if processed_result.get("action") == "REJECT":
            print("ERROR: AI response failed validation rules.")
            return

        # Attach outcomes to the tix object
        ticket.ai_analysis = ai_analysis
        ticket.final_priority = ai_analysis.get("priority", ticket.user_priority)
        ticket.escalated = ai_analysis.get("requires_escalation", False)
        ticket.requires_manual_review = ai_analysis.get("requires_manual_review", False)

        # Save and confirm
        io_manager.save_new_ticket(ticket)
        print(f"\nTicket {ticket.ticket_id} successfully processed and saved!")
        print(f"Category: {ai_analysis.get('category')} | Priority: {ticket.final_priority}")

    except ValueError as error:
        print(f"ERROR: {error}")

if __name__ == "__main__":
    io_mgr = IOManager()
    ai_mgr = AIManager()
    submit_ticket(io_mgr, ai_mgr)