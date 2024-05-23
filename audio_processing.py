from pedalboard import Pedalboard, Reverb, time_stretch
from pedalboard.io import AudioFile
import io
import pedalboard


def slow_and_reverb(audio_bytes, slow_factor=5, reverb_level=5):
    # TODO: actully change params wrt provided ones

    board = Pedalboard([Reverb(room_size=0.25)])

    input_buffer = io.BytesIO()  # TODO: rename io.BytesIO-related stuff
    input_buffer.write(audio_bytes)
    input_buffer.seek(0)  # now f is feedable to Pedalboard's AudioFile
    output_buffer = io.BytesIO()

    with AudioFile(input_buffer, "r") as ain:
        with AudioFile(output_buffer, "w", ain.samplerate, ain.num_channels, format="mp3") as aout:
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
    input_buffer.close()    
    output_buffer.seek(0)
    return output_buffer
