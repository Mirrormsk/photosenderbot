from db_connect import DBManager
import os
import dotenv

class Session:
    def __init__(self, db_manager: DBManager) -> None:
        self.manager = db_manager
        self.data = self.manager.data
        self.active_chat_id = None
        if "session" not in self.data:
            self.data["status"] = "unlocked"

    @property
    def is_locked(self) -> tuple[bool, int | None]:
        status_locked = self.data.get("status") == "locked"
        return status_locked

    def unlock(self) -> None:
        self.data["status"] = "unlocked"
        self.active_chat_id = None
        self.manager.save()
        if os.environ.get("USER_ID"):
            os.environ.pop('USER_ID')
        if os.environ.get("USER_NAME"):
            os.environ.pop('USER_NAME')

    def lock(self, chat_id: int, user_name: str) -> None:
        self.data["status"] = "locked"
        self.active_chat_id = chat_id
        self.manager.save()
        os.environ['USER_ID'] = str(chat_id)
        os.environ['USER_NAME'] = str(user_name)
