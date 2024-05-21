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


# create the user-state dict
# TODO: store on the drive
# keys: user_id, values: user_state (control flow state)
user_state = {}
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
    if message.from_user.id not in user_state:  # new user case
        user_state[message.from_user.id] = "default"
        welcome(message)


@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "Welcome to the Slowed and Reverbed world!\nSend an .mp3 file to get its improved version ;)")


@bot.message_handler(commands=["default", "advanced"])
def set_mode(message):
    user_state[message.from_user.id] = message.text[1:]
    if message.text[1:] == "advanced":
        bot.send_message(message, "In the advanced mode you can set a custom stretching factor and the amount of reverberation.\nBut first, send the .mp3 file.")
    else:
        bot.send_message(message, "In the default mode just send the .mp3 file to get its better version ;)")



@bot.message_handler(content_types=["audio"],
                     func=lambda m: user_state[m.from_user.id] in ["default", "advanced"])
def process_audio(message):
    file_info = bot.get_file(message.audio.file_id)
    audio_bytes = bot.download_file(file_info.file_path)


    # TODO: check if the file is valid (e.g. if the maximum sendable filesize
    # is not exceeded)


    # set slowing and reverberation parameters

    if user_state[message.from_user.id] == "default":
        output_buffer = slow_and_reverb(audio_bytes)
        bot.send_audio(message.chat.id, telebot.types.InputFile(output_buffer))
    else:
        pass


bot.infinity_polling()
message_log.close()
