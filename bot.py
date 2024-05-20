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


MESSAGE_PICKLES_DIR = Path(r"message_pickles")
LOG_PATH = Path(r"message_log.csv")


telebot.apihelper.ENABLE_MIDDLEWARE = True


bot = telebot.TeleBot(TG_TOKEN, parse_mode=None)


# read the log file
# columns are: message_id,user_id,timestamp,pickle_path
message_log = open(LOG_PATH, "a")


@bot.middleware_handler(update_types=['message'])
def pickle_message(bot_instance, message):
    path = MESSAGE_PICKLES_DIR / f"id{message.id}_userid{message.from_user.id}_date{message.date}.pickle"
    with open(path, "wb") as f:
        pickle.dump(message, f)
    
    # log a subset of message attributes to a .csv file
    message_log.write(f"{message.id},{message.from_user.id},{message.date},{path}\n")
    message_log.flush()  # moves (flushes) the runtime file buffer to OS
    os.fsync(message_log.fileno())


@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "Welcome to the Slowed and Reverbed world!\nSend an .mp3 file to get its improved version ;)")


@bot.message_handler(content_types=["audio"])
def process_audio(message):

    # Make a Pedalboard object, containing multiple audio plugins:
    board = Pedalboard([Reverb(room_size=0.25)])

    file_info = bot.get_file(message.audio.file_id)
    bytes = bot.download_file(file_info.file_path)
    file_alike = io.BytesIO()  # TODO: rename io.BytesIO-related stuff
    file_alike.write(bytes)
    file_alike.seek(0)  # now f is feedable to Pedalboard's AudioFile

    # TODO: check if the file is valid (e.g. if the maximum sendable filesize
    # is not exceeded)


    # set slowing and reverberation parameters


    with AudioFile(file_alike, "r") as ain:
        buffer = io.BytesIO()
        with AudioFile(buffer, "w", ain.samplerate, ain.num_channels, format="mp3") as aout:
            # read one second of audio at a time, until the file is empty:
            while ain.tell() < ain.frames:
                chunk = ain.read(ain.samplerate)

                # slow down
                # TODO: research on a time stretching which doesn't compesnate
                # pitch implicitly
                chunk = pedalboard.time_stretch(chunk, ain.samplerate, 0.8)
                
                # reverberate
                effected = board(chunk, ain.samplerate, reset=False)
                
                # write the output to our output file:
                aout.write(effected)
        pedalboard.io.StreamResampler
        
        buffer.seek(0)
        bot.send_audio(message.chat.id, telebot.types.InputFile(buffer))

    file_alike.close()   


bot.infinity_polling()
message_log.close()