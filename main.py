from managers.io_manager import IOManager
from managers.ai_manager import AIManager

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
        
        print(f"AI Analysis Output: {ai_analysis.get('category')} - {ai_analysis.get('priority')}")

    except ValueError as error:
        print(f"ERROR: {error}")

if __name__ == "__main__":
    io_mgr = IOManager()
    ai_mgr = AIManager()
    submit_ticket(io_mgr, ai_mgr)