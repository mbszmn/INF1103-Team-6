class IOManager:
    VALID_USER_PRIORITIES = {"Low", "Medium", "High", "Critical"}

    @staticmethod # means the function can be used without needing self or creating an object first
    def _required_input(prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("This field cannot be empty.")
