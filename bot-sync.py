import os
import threading

import dotenv
import telebot
from telebot import custom_filters
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot.custom_filters import AdvancedCustomFilter, types

import config
from db_connect import DBManager
from lexicon import LEXICON
from service import FileManager
from session import Session

dotenv.load_dotenv()

BOT_TOKEN = config.BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

ADMIN_ID = config.ADMIN_ID

base_dir = os.path.dirname(os.path.abspath(__file__))

file_manager = FileManager(working_dir=config.WORKING_DIR,
                           bot=bot,
                           sent_dir=str(os.path.join(base_dir, config.SENT_DIR)),
                           stash_dir=str(os.path.join(base_dir, config.STASH_DIR)))
db_manager = DBManager(os.path.join(base_dir, 'data', 'db.json'))

session = Session(db_manager)

session_callback_factory = CallbackData("action", "user_id", "user_name", prefix="session")
stash_files_callback_factory = CallbackData("action", "user_id", "user_name", prefix="stash")


class SessionCallbackFilter(AdvancedCustomFilter):
    key = 'config'

    def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


@bot.message_handler(commands=['start'], chat_id=[ADMIN_ID])
def send_welcome_admin(message):
    bot.reply_to(message, text=LEXICON['greeting_admin'].format(file_manager.working_dir))


@bot.message_handler(commands=['help'], chat_id=[ADMIN_ID])
def send_welcome_admin(message):
    bot.reply_to(message, text=LEXICON['help_text'])


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, text=LEXICON['greeting_user'])


@bot.message_handler(commands=['open'])
def session_open_request(message: telebot.types.Message):
    bot.send_message(message.chat.id, text=LEXICON['session_open_request'])

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    approve_btn = telebot.types.InlineKeyboardButton(text="Открыть сессию",
                                                     callback_data=session_callback_factory.new(action='approve',
                                                                                                user_id=message.from_user.id,
                                                                                                user_name=message.from_user.first_name))
    keyboard.add(approve_btn)
    bot.send_message(ADMIN_ID, text=LEXICON['admin_request_confirm'].format(message.from_user.first_name),
                     reply_markup=keyboard)


@bot.callback_query_handler(func=None, config=session_callback_factory.filter())
def handle_open_session_callback_button(query: telebot.types.CallbackQuery):
    callback_data = session_callback_factory.parse(callback_data=query.data)

    close_all_keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    close_all_btn = telebot.types.KeyboardButton(text='/close_all')
    close_all_keyboard.add(close_all_btn)

    if session.is_locked:

        bot.send_message(ADMIN_ID, text=LEXICON['session_is_closed_now'].format(session.active_chat_id))
    else:
        files_exist = file_manager.count_existing_files()
        user_id = int(callback_data['user_id'])
        user_name = callback_data['user_name']

        if not files_exist:

            session.lock(user_id, user_name)
            bot.send_message(user_id, text=LEXICON['to_user_session_is_open'])
            bot.send_message(ADMIN_ID, text=LEXICON['admin_session_is_opened'].format(user_name))
        else:
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
            send_btn = telebot.types.InlineKeyboardButton(text="Отправить клиенту",
                                                          callback_data=stash_files_callback_factory.new(
                                                              action='send',
                                                              user_id=user_id,
                                                              user_name=user_name)
                                                          )
            stash_btn = telebot.types.InlineKeyboardButton(text="В архив",
                                                           callback_data=stash_files_callback_factory.new(
                                                               action='stash',
                                                               user_id=user_id,
                                                               user_name=user_name)
                                                           )
            keyboard.add(send_btn, stash_btn)
            bot.send_message(ADMIN_ID, text=LEXICON['files_exist_in_working_dir'].format(files_exist),
                             reply_markup=keyboard)
    bot.send_message(chat_id=ADMIN_ID, reply_markup=close_all_keyboard,
                     text='Вызовете команду /close_all для закрытия всех сессий')
    print(f"\nSession status: {session.data['status']}")


@bot.callback_query_handler(func=None, config=stash_files_callback_factory.filter())
def handle_send_or_stash_button(query: telebot.types.CallbackQuery):
    callback_data = stash_files_callback_factory.parse(callback_data=query.data)

    if callback_data['action'] == 'stash':
        file_manager.stash_files()
        bot.send_message(ADMIN_ID, text=LEXICON['files_was_moved_to_stash'])

    user_id = int(callback_data['user_id'])
    user_name = callback_data['user_name']
    session.lock(user_id, user_name)
    bot.send_message(user_id, text=LEXICON['to_user_session_is_open'])


@bot.message_handler(chat_id=[ADMIN_ID], commands=['close_all'])
def session_unlock_handler(message: telebot.types.Message):
    session.unlock()
    bot.send_message(ADMIN_ID, text=LEXICON['session_was_been_unlocked'])
    print(f"\nSession status: {session.data['status']}")


if __name__ == '__main__':
    watchdog_thread = threading.Thread(target=file_manager.handle_events, args=(bot,))
    watchdog_thread.start()

    bot.add_custom_filter(SessionCallbackFilter())
    bot.add_custom_filter(custom_filters.ChatFilter())

    bot.infinity_polling()
