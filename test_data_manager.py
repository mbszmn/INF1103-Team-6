# quick checks for the data manager, run with: python test_data_manager.py
import os
from managers import data_manager
from managers.logic_manager import fallback_classification, process_ticket
from models.ticket import create_ticket

# point data_manager at test files so the real tickets.json is not touched
data_manager.TICKET_FILE = "data/test_tickets.json"
data_manager.CSV_FILE = "data/test_tickets.csv"
if os.path.exists(data_manager.TICKET_FILE):
    os.remove(data_manager.TICKET_FILE)

results = []


def check(name: str, result: bool) -> None:
    if result:
        print("PASS", name)
    else:
        print("FAIL", name)
    results.append(result)


# damaged file
with open(data_manager.TICKET_FILE, "w") as file:
    file.write("not json")
check("damaged file gives empty list", data_manager.load_tickets() == [])
check("damaged file kept as backup", os.path.exists(data_manager.TICKET_FILE + ".bak"))
os.remove(data_manager.TICKET_FILE + ".bak")

# saving to a folder name must fail without crashing
data_manager.TICKET_FILE = "data"
check("failed save returns False", data_manager.save_tickets([]) == False)
data_manager.TICKET_FILE = "data/test_tickets.json"

# add a ticket with its ai result, same order as main.py
tickets = data_manager.load_tickets()
check("no file gives empty list", tickets == [])
check("first id is 0001", data_manager.generate_ticket_id(tickets) == "0001")

ticket = create_ticket("0001", "tester", "2600001", "Windows", "Wifi down", "cannot connect to the school wifi")
ai_result = process_ticket(fallback_classification("cannot connect to the school wifi"))
data_manager.attach_ai_result(ticket, ai_result)
check("add ticket", data_manager.add_ticket(tickets, ticket) == True)
saved = data_manager.load_tickets()
check("ticket saved", saved[0]["ticket_id"] == "0001")
check("ai result saved with it", saved[0]["ai_analysis"]["category"] == "Network")
check("manual review flag saved", saved[0]["requires_manual_review"] == True)

# unique id
check("next id is 0002", data_manager.generate_ticket_id(tickets) == "0002")
copy = create_ticket("0001", "tester", "2600001", "Mac", "Copy", "same id as the first one")
check("duplicate id refused", data_manager.add_ticket(tickets, copy) == False)
check("only one ticket stored", len(tickets) == 1)
check("id cannot be changed", data_manager.update_ticket(tickets, "0001", "ticket_id", "0009") == False)

# ai result without the manual review key
good = {"category": "Software", "priority": "High", "confidence": 0.95,
        "summary": "App crashes", "affected_system": "Excel",
        "security_related": False, "requires_escalation": False,
        "troubleshooting": ["Restart Excel"]}
second = create_ticket("0002", "tester", "2600002", "Windows", "Excel crash", "excel closes every time I open it")
data_manager.attach_ai_result(second, process_ticket(good))
check("no error when manual review key is missing", second["requires_manual_review"] == False)
check("second ticket added", data_manager.add_ticket(tickets, second) == True)

# find and update
check("find ticket", data_manager.find_ticket(tickets, "0002") == second)
check("find missing ticket", data_manager.find_ticket(tickets, "9999") == None)
check("update ticket", data_manager.update_ticket(tickets, "0001", "device", "Mac") == True)
check("update saved", data_manager.load_tickets()[0]["device"] == "Mac")

# closed tickets cannot be changed unless reopened
check("close ticket", data_manager.close_ticket(tickets, "0001") == True)
check("closed ticket cannot be updated", data_manager.update_ticket(tickets, "0001", "device", "Linux") == False)
check("closed ticket cannot be closed again", data_manager.close_ticket(tickets, "0001") == False)
check("open ticket cannot be reopened", data_manager.reopen_ticket(tickets, "0002") == False)
check("reopen ticket", data_manager.reopen_ticket(tickets, "0001") == True)
check("reopened ticket can be updated", data_manager.update_ticket(tickets, "0001", "device", "Linux") == True)
check("reopened ticket can be closed again", data_manager.close_ticket(tickets, "0001") == True)
check("missing ticket cannot be closed", data_manager.close_ticket(tickets, "9999") == False)

# csv export
check("csv export", data_manager.export_tickets_csv(tickets) == True)
with open(data_manager.CSV_FILE, "r") as file:
    lines = file.readlines()
check("csv has header and one row per ticket", len(lines) == len(tickets) + 1)
check("csv first row is ticket 0001", lines[1][:5] == "0001,")

os.remove(data_manager.TICKET_FILE)
os.remove(data_manager.CSV_FILE)

failed = 0
for result in results:
    if result == False:
        failed = failed + 1
print()
print(len(results) - failed, "passed,", failed, "failed")
