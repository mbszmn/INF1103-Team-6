class TicketError(Exception):
    # a ticket rule was broken, like closing a ticket twice or asking for an id that does not exist
    pass
