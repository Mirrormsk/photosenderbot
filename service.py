import os
import time

import telebot
from dotenv import load_dotenv


class FileManager:
    def __init__(self, working_dir: str, bot: telebot.TeleBot) -> None:
        self.working_dir = working_dir
        self.stash_dir = "stash"
        self.bot = bot

        if not os.path.exists(self.stash_dir):
            os.makedirs(self.stash_dir)

    @staticmethod
    def send_file(bot: telebot.TeleBot, file_path, user_id):
        with open(file_path, "rb") as doc_obj:
            bot.send_document(chat_id=user_id, document=doc_obj)

    def check_files(self, bot) -> None:
        load_dotenv()
        user_id = os.getenv('USER_ID')
        user_name = os.getenv('USER_NAME')
        user_id = int(user_id) if user_id else None

        if not user_id:
            return
        print(f"\rCurrent receiver chat_id: {user_id}", end='')

        user_sent_folder_name = f'sent/{user_name}_{user_id}'
        if not os.path.exists(user_sent_folder_name):
            os.mkdir(user_sent_folder_name)

        files = os.listdir(self.working_dir)
        for filename in files:
            filepath = f'{self.working_dir}/{filename}'
            self.send_file(bot, filepath, user_id=user_id)
            os.replace(filepath, os.path.join(user_sent_folder_name, filename))

    def handle_events(self, bot) -> None:
        while True:
            self.check_files(bot)
            time.sleep(5)

    def count_existing_files(self):
        files = [file for file in os.listdir(self.working_dir) if not file.startswith('.')]
        return len(files)

    def stash_files(self):
        files = [file for file in os.listdir(self.working_dir) if not file.startswith('.')]
        for filename in files:
            filepath = f'{self.working_dir}/{filename}'
            os.replace(filepath, os.path.join(self.stash_dir, filename))
