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
