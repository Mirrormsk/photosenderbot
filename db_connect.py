import json
import os


class DBManager:
    def __init__(self, db_file: str) -> None:
        self.db_file = db_file
        self.data = {}

    def load(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                data = json.load(f)
                self.data = data

    def save(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    db = DBManager('data/db.json')
    db.load()
    db.save()
