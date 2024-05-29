import telebot
import pickle
from pathlib import Path
import os
from audio_processing import slow_and_reverb
import json
import argparse


# set up the working directory
DATA_DIR = Path(r"data")
MESSAGES_DIR = DATA_DIR / r"messages"
USER_INFO_PATH = DATA_DIR / r"user_info.json"

# create the `data` folder if it isn't there already
if DATA_DIR.exists():
    print("`data` folder already exists")
else:
    DATA_DIR.mkdir()
    print("`data` folder created")

# same for `messages`...
if MESSAGES_DIR.exists():
    print("`messages` folder already exists")
else:
    MESSAGES_DIR.mkdir()
    print("`messages` folder created")

# ... and for `user_info.json`
if USER_INFO_PATH.exists():
    print("`user_info.json` file already exists")
else:
    USER_INFO_PATH.touch()
    # write "{}" to, so it is of a proper .json format
    with USER_INFO_PATH.open("w") as f:
        f.write(r"{}")
        f.flush()
        os.fsync(f.fileno())
    print("`user_info.json` file created")


# to run this script from the command line, a TOKEN from https://t.me/BotFather
# must be provided as an agrument
# parse it
parser = argparse.ArgumentParser()
parser.add_argument("token")

args = parser.parse_args()


# enable middleware handlers (funcs to process messages before handlers)
telebot.apihelper.ENABLE_MIDDLEWARE = True

# create a bot instance
bot = telebot.TeleBot(args.token, parse_mode=None)


# load users info
with USER_INFO_PATH.open() as f:
    user_info = json.load(f)


@bot.middleware_handler(update_types=['message'])
def pickle_message(bot_instance, message):
    # create a user's directory if it doesn't exist (new user case)
    user_dir = MESSAGES_DIR / str(message.from_user.id)
    if not user_dir.exists():
        user_dir.mkdir()
    # store the message to the users directory
    path = user_dir / f"{message.id}.pickle"
    with open(path, "wb") as f:
        pickle.dump(message, f)


@bot.middleware_handler(update_types=['message'])
def new_user(bot_instance, message):
    if message.from_user.id not in user_info:  # new user case
        user_info[message.from_user.id] = {
            "stage": "home",
            "slowing": 0.9,
            "reverb": 0.25,
        }
    # update user_info.json on the drive
    with USER_INFO_PATH.open("w") as f:
        json.dump(user_info, f)
        os.fsync(f.fileno())


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
    bot.send_audio(message.chat.id, telebot.telebot.types.InputFile(output_buffer))


@bot.message_handler(commands=["set_slowing"])
def prompt_slowing_change(message):
    user_info[message.from_user.id]["stage"] = "selecting_slowing"

    # construct the keyboard with valid slowing options
    markup = telebot.types.ReplyKeyboardMarkup()
    markup.add(
        telebot.types.KeyboardButton(r'10%'),
        telebot.types.KeyboardButton(r'25%'),
        telebot.types.KeyboardButton(r'50%'),
    )
    bot.send_message(message.chat.id, "Select how much to slow down the audio",
                        reply_markup=markup)
@bot.message_handler(
        content_types=["text"],
        func=lambda m: user_info[m.from_user.id]["stage"] == "selecting_slowing"
)
def set_slowing(message):
    user_info[message.from_user.id]["slowing"] = (100 - int(message.text[:-1])) / 100
    user_info[message.from_user.id]["stage"] = "home"

    # update user_info.json on the drive
    with USER_INFO_PATH.open("w") as f:
        json.dump(user_info, f)
        os.fsync(f.fileno())

    markup = telebot.types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, "Slowing rate was updated",
                     reply_markup=markup)


@bot.message_handler(commands=["set_slowing"])
def prompt_reverb_change(message):
    user_info[message.from_user.id]["stage"] = "selecting_slowing"

    # construct the keyboard with valid slowing options
    markup = telebot.types.ReplyKeyboardMarkup()
    markup.add(
        telebot.types.KeyboardButton(r'15%'),
        telebot.types.KeyboardButton(r'20%'),
        telebot.types.KeyboardButton(r'90%'),
    )
    bot.send_message(message.chat.id, "Select how much reverb do you want?",
                        reply_markup=markup)
@bot.message_handler(
        content_types=["text"],
        func=lambda m: user_info[m.from_user.id]["stage"] == "selecting_slowing"
)
def set_reverb(message):
    user_info[message.from_user.id]["reverb"] = (100 - int(message.text[:-1])) / 100
    user_info[message.from_user.id]["stage"] = "home"

    # update user_info.json on the drive
    with USER_INFO_PATH.open("w") as f:
        json.dump(user_info, f)
        os.fsync(f.fileno())

    markup = telebot.types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, "Reverb amount was updated",
                     reply_markup=markup)
    

bot.infinity_polling()
