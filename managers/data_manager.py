import json
import os
import datetime

DATA_FOLDER = "data"
TICKET_FILE = "data/tickets.json"
CSV_FILE = "data/tickets.csv"
LINE = "------------------------------------------------"


def current_time() -> str:
    # same format as created_at in models/ticket.py
    return datetime.datetime.now().isoformat(timespec="seconds")


def load_tickets() -> list:
    if not os.path.exists(TICKET_FILE):
        print(TICKET_FILE, "not found, starting with no tickets.")
        return []

    with open(TICKET_FILE, "r", encoding="utf-8") as file:
        tickets = json.load(file)
    print(TICKET_FILE, "found,", len(tickets), "ticket(s) loaded.")
    return tickets


def save_tickets(tickets: list) -> bool:
    if not os.path.exists(DATA_FOLDER):
        os.mkdir(DATA_FOLDER)
    with open(TICKET_FILE, "w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)
    return True


def generate_ticket_id(tickets: list) -> str:
    # biggest id so far + 1
    largest = 0
    for ticket in tickets:
        if str(ticket["ticket_id"]).isdigit():
            number = int(ticket["ticket_id"])
            if number > largest:
                largest = number

    # pad to 4 digits like 0001
    new_id = str(largest + 1)
    while len(new_id) < 4:
        new_id = "0" + new_id
    return new_id


def find_ticket(tickets: list, ticket_id: str) -> dict | None:
    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            return ticket
    return None


def add_ticket(tickets: list, ticket: dict) -> bool:
    # ids must be unique
    if find_ticket(tickets, ticket["ticket_id"]) != None:
        print("Ticket ID", ticket["ticket_id"], "already exists.")
        return False
    tickets.append(ticket)
    return save_tickets(tickets)


def attach_ai_result(ticket: dict, ai_result: dict) -> None:
    # keep the ai output inside the ticket so both get saved together
    ticket["ai_analysis"] = ai_result
    ticket["final_priority"] = ai_result["priority"]
    ticket["escalated"] = ai_result["requires_escalation"]
    # logic manager only adds this one when confidence is low
    if "requires_manual_review" in ai_result.keys():
        ticket["requires_manual_review"] = ai_result["requires_manual_review"]


def update_ticket(tickets: list, ticket_id: str, field: str, new_value: str) -> bool:
    ticket = find_ticket(tickets, ticket_id)
    if ticket == None:
        print("Ticket", ticket_id, "not found.")
        return False
    if field == "ticket_id":
        print("Ticket ID cannot be changed.")
        return False
    # closed tickets cannot be changed unless reopened
    if ticket["status"] == "Closed":
        print("Ticket", ticket_id, "is closed, reopen it first.")
        return False

    ticket[field] = new_value
    ticket["updated_at"] = current_time()
    return save_tickets(tickets)


def close_ticket(tickets: list, ticket_id: str) -> bool:
    closed = update_ticket(tickets, ticket_id, "status", "Closed")
    if closed:
        print("Ticket", ticket_id, "closed.")
    return closed


def reopen_ticket(tickets: list, ticket_id: str) -> bool:
    ticket = find_ticket(tickets, ticket_id)
    if ticket == None:
        print("Ticket", ticket_id, "not found.")
        return False
    if ticket["status"] != "Closed":
        print("Ticket", ticket_id, "is not closed.")
        return False

    ticket["status"] = "Reopened"
    ticket["updated_at"] = current_time()
    saved = save_tickets(tickets)
    if saved:
        print("Ticket", ticket_id, "reopened.")
    return saved


def display_ticket(ticket: dict) -> None:
    print(LINE)
    print("Ticket ID:", ticket["ticket_id"])
    print("User:", ticket["username"], "| Device:", ticket["device"])
    print("Title:", ticket["title"])
    print("Description:", ticket["description"])
    print("Status:", ticket["status"], "| Priority:", ticket["final_priority"])
    print("Escalated:", ticket["escalated"],
          "| Manual review:", ticket["requires_manual_review"])
    if ticket["ai_analysis"] != {}:
        print("AI Category:", ticket["ai_analysis"]["category"])
        print("AI Summary:", ticket["ai_analysis"]["summary"])
    print("Created:", ticket["created_at"], "| Updated:", ticket["updated_at"])
    print(LINE)


def display_all(tickets: list) -> None:
    print("\nAll Tickets")
    print(LINE)
    if len(tickets) == 0:
        print("No tickets yet.")
    for ticket in tickets:
        print("ID: " + ticket["ticket_id"] + " | " + ticket["title"]
              + " | Priority: " + ticket["final_priority"]
              + " | Status: " + ticket["status"])
    print(LINE)


def export_tickets_csv(tickets: list) -> bool:
    # csv version for staff to open in excel, text goes in quotes in case it has commas
    with open(CSV_FILE, "w", encoding="utf-8") as file:
        file.write("ticket_id,username,device,title,category,"
                   + "final_priority,status,escalated,created_at\n")
        for ticket in tickets:
            category = ""
            if ticket["ai_analysis"] != {}:
                category = ticket["ai_analysis"]["category"]
            file.write(ticket["ticket_id"] + ","
                       + '"' + ticket["username"] + '",'
                       + '"' + ticket["device"] + '",'
                       + '"' + ticket["title"] + '",'
                       + category + ","
                       + ticket["final_priority"] + ","
                       + ticket["status"] + ","
                       + str(ticket["escalated"]) + ","
                       + ticket["created_at"] + "\n")
    print("Tickets exported to", CSV_FILE)
    return True
