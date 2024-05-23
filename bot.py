import telebot
from PRIVACY import TG_TOKEN
from pedalboard import Pedalboard, Reverb, time_stretch
from pedalboard.io import AudioFile
import io
import pedalboard
from telebot import types
import pickle
from pathlib import Path
import os
from audio_processing import slow_and_reverb


MESSAGE_PICKLES_DIR = Path(r"message_pickles")
LOG_PATH = Path(r"message_log.csv")


telebot.apihelper.ENABLE_MIDDLEWARE = True


bot = telebot.TeleBot(TG_TOKEN, parse_mode=None)


# read the log file
# columns are: message_id,user_id,timestamp,pickle_path
message_log = open(LOG_PATH, "a")


# create the user-info dict
# TODO: store on the drive
# dictionary structure:
# {
#     "user_id":{
#         "mode": "default",
#         "stage": "home",
#     }
# }
user_info = {}
# POSSIBLE STATES: "default", "setting_stretch", "setting_reverb", "advanced"


def infer_user_state(message):
    # returns user state
    pass



@bot.middleware_handler(update_types=['message'])
def pickle_message(bot_instance, message):
    path = MESSAGE_PICKLES_DIR / f"id{message.id}_userid{message.from_user.id}_date{message.date}.pickle"
    with open(path, "wb") as f:
        pickle.dump(message, f)
    
    # log a subset of message attributes to a .csv file
    message_log.write(f"{message.id},{message.from_user.id},{message.date},{path}\n")
    message_log.flush()  # moves (flushes) the runtime file buffer to OS
    os.fsync(message_log.fileno())



@bot.middleware_handler(update_types=['message'])
def new_user(bot_instance, message):
    if message.from_user.id not in user_info:  # new user case
        user_info[message.from_user.id] = {
            "stage": "home",
            "slowing": 0.9,
            "reverb": 0.25,
        }
        welcome(message)


@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "Welcome to the Slowed and Reverbed world!\nSend an .mp3 file to get its improved version ;)")



@bot.message_handler(
        content_types=["audio"],
        func=lambda m: user_info[m.from_user.id]["stage"] == "home"
)
def process_audio(message):
    # TODO: check if the file is valid (e.g. if the maximum sendable filesize
    # is not exceeded)

    # TODO: update typing status to "Sending audio..."
    # and let the user know how long will it take
    file_info = bot.get_file(message.audio.file_id)
    audio_bytes = bot.download_file(file_info.file_path)
    output_buffer = slow_and_reverb(
        audio_bytes,
        user_info[message.from_user.id]["slowing"],
        user_info[message.from_user.id]["reverb"],
    )
    bot.send_audio(message.chat.id, telebot.types.InputFile(output_buffer))


@bot.message_handler(commands=["set_slowing"])
def prompt_slowing_change(message):
    user_info[message.from_user.id]["stage"] = "selecting_slowing"

    # construct the keyboard with valid slowing options
    markup = types.ReplyKeyboardMarkup()
    markup.add(
        types.KeyboardButton(r'10%'),
        types.KeyboardButton(r'25%'),
        types.KeyboardButton(r'50%'),
    )
    bot.send_message(message, "Select how much to slow down the audio",
                        reply_markup=markup)
@bot.message_handler(
        content_types=["text"],
        func=lambda m: user_info[m.from_user.id]["stage"] == "selecting_slowing"
)
def set_slowing(message):
    user_info[message.from_user.id]["slowing"] = (100 - int(message.text[:-1])) / 100
    bot.send_message(message, "Slowing rate was updated")
    user_info[message.from_user.id]["stage"] = "home"


@bot.message_handler(commands=["set_slowing"])
def prompt_reverb_change(message):
    user_info[message.from_user.id]["stage"] = "selecting_slowing"

    # construct the keyboard with valid slowing options
    markup = types.ReplyKeyboardMarkup()
    markup.add(
        types.KeyboardButton(r'15%'),
        types.KeyboardButton(r'20%'),
        types.KeyboardButton(r'90%'),
    )
    bot.send_message(message, "Select how much reverb do you want?",
                        reply_markup=markup)
@bot.message_handler(
        content_types=["text"],
        func=lambda m: user_info[m.from_user.id]["stage"] == "selecting_slowing"
)
def set_reverb(message):
    user_info[message.from_user.id]["reverb"] = (100 - int(message.text[:-1])) / 100
    bot.send_message(message, "Reverb amount was updated")
    user_info[message.from_user.id]["stage"] = "home"
    

bot.infinity_polling()
message_log.close()
