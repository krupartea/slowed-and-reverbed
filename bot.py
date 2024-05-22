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



MESSAGE_PICKLES_DIR = Path(r"messages")
LOG_PATH = Path(r"message_log.csv")


telebot.apihelper.ENABLE_MIDDLEWARE = True


bot = telebot.TeleBot(TG_TOKEN, parse_mode=None)


# read the log file
# columns are: message_id,user_id,timestamp,pickle_path
message_log = open(LOG_PATH, "a")


@bot.middleware_handler(update_types=['message'])
def pickle_message(bot_instance, message):
    # create a user's directory if it doesn't exist (new user case)
    user_dir = MESSAGE_PICKLES_DIR / str(message.from_user.id)
    if not user_dir.exists():
        user_dir.mkdir()
    # store the message to the users directory
    path = user_dir / f"{message.id}.pickle"
    with open(path, "wb") as f:
        pickle.dump(message, f)


@bot.message_handler(commands=["start", "help"])
def welcome(message):
    bot.reply_to(message, "Welcome to the Slowed and Reverbed world!\nSend an .mp3 file to get its improved version ;)")


@bot.message_handler(commands=["default", "advanced"])
def set_mode(message):
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
