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
