import telebot
from PRIVACY import TG_TOKEN
from pedalboard import Pedalboard, Reverb, time_stretch
from pedalboard.io import AudioFile
import io
import pedalboard


bot = telebot.TeleBot(TG_TOKEN, parse_mode=None)


@bot.message_handler(commands=["start"])
def welcome(message):
    bot.reply_to(message, "Welcome to the Slowed and Reverbed world!\nSend an .mp3 file to get an improved version ;)")

@bot.message_handler(content_types=["audio"])
def process_audio(message):

    # Make a Pedalboard object, containing multiple audio plugins:
    board = Pedalboard([Reverb(room_size=0.25)])

    file_info = bot.get_file(message.audio.file_id)
    bytes = bot.download_file(file_info.file_path)
    file_alike = io.BytesIO()  # TODO: rename io.BytesIO-related stuff
    file_alike.write(bytes)
    file_alike.seek(0)  # now f is feedable to Pedalboard's AudioFile

    with AudioFile(file_alike, "r") as ain:

        # original_sample_rate = ain.samplerate

        # # stretch
        # stretch_factor = 1.20
        # new_sample_rate = original_sample_rate / stretch_factor
        # ain = ain.resampled_to(new_sample_rate)

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
