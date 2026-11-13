class StatusChange:
    # one line of a ticket's history, only the Ticket class makes these

    def __init__(self, old_status: str, new_status: str, changed_at: str):
        self.__old_status: str = old_status
        self.__new_status: str = new_status
        self.__changed_at: str = changed_at

    @property
    def old_status(self) -> str:
        return self.__old_status

    @property
    def new_status(self) -> str:
        return self.__new_status

    @property
    def changed_at(self) -> str:
        return self.__changed_at

    def describe(self) -> str:
        if self.__old_status == "":
            return f"{self.__changed_at}  created as {self.__new_status}"
        return f"{self.__changed_at}  {self.__old_status} -> {self.__new_status}"

    def to_dict(self) -> dict[str, str]:
        return {
            "old_status": self.__old_status,
            "new_status": self.__new_status,
            "changed_at": self.__changed_at,
        }
