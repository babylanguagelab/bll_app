## @package parsers.wav_parser

import pyaudio
import wave
import logging
import traceback

## This class manipulates and plays WAV audio files.
#  This class requires the PyAudio library.
class WavParser(object):
    ## Constructor
    #  @param self
    #  @param filename (string) full path to a WAV file
    def __init__(self, filename):
        self.logger = logging.getLogger(__name__)
        self.total_sec = -1

        #attempt to open the wav file and determine its length in seconds
        try:
            self.wav_in = wave.open(filename, 'rb')
        except Exception as e:
            logging.error("Unable to open WAV file. Exception: %s" % e)
            traceback.print_exc()

    ## Returns a sound's length, in seconds.
    #  @param self
    #  @returns (float) The length of the sound in seconds, or zero if there was an error opening the WAV file.
    def get_sound_len(self):
        if self.total_sec < 0:
            self.total_sec = self.wav_in.getnframes() / float(self.wav_in.getframerate())
            
        return self.total_sec

    ## Plays a segment's corresponding audio clip.
    #  Audio is played from (seg.start - context_len) to (seg.end + context_len).
    #  @param self
    #  @param seg (Segment) The Segment object for which to play a clip
    #  @param context_len (int=0) the padding length, in seconds, to be applied to both sides.  
    def play_seg(self, seg, context_len=0):
        start = max(0, seg.start - context_len)
        end = min(self.get_sound_len(), seg.end + context_len)
        
        self.play_clip(start, end)

    ## Plays an utterance's corresponding audio clip.
    #  Audio is played from (utter.start - context_len) to (utter.end + context_len).
    #  @param self
    #  @param utter (Utterance) The Utterance object for which to play a clip
    #  @param context_len (int=0) the padding length, in seconds, to be applied to both sides
    #  @param play_linked (boolean=False) If true, the entire Utterance chain will be played. Otherwise only a single utternace will be played.
    def play_utter(self, utter, context_len=0, play_linked=False):
        start_utter = utter
        end_utter = utter

        if play_linked:
            while start_utter.prev:
                start_utter = start_utter.prev
            while end_utter.next:
                end_utter = end_utter.next

        start = max(0, start_utter.start - context_len)
        end = min(end_utter.end + context_len, self.get_sound_len())

        self.play_clip(start, end)

    def extract_clip(self, start_time, end_time, filename):
        #initialize the audio library
        audio = pyaudio.PyAudio()
        wav_out = wave.open(filename, 'wb')
        wav_out.setnchannels(self.wav_in.getnchannels())
        wav_out.setsampwidth(self.wav_in.getsampwidth())
        wav_out.setframerate(self.wav_in.getframerate())

        #extract the chunk of the sound that we want to save
        start_frame = int(start_time * self.wav_in.getframerate())
        end_frame = int(end_time * self.wav_in.getframerate())
        num_frames = end_frame - start_frame + 1

        self.wav_in.setpos(start_frame)
        data = self.wav_in.readframes(num_frames)
        wav_out.writeframes(data)
        wav_out.close()
        audio.terminate()

    ## Extracts a specified chunk of audio from the wav file and plays it through the default audio device.
    #  @param self
    #  @param start_time (float) absolute start time of the clip to play, in seconds
    #  @param end_time (float) absolute end time of the clip to play, in seconds
    def play_clip(self, start_time, end_time):
        self.logger.info("Playing clip: [%f, %f]\n" % (start_time, end_time))

        #initialize the audio library
        audio = pyaudio.PyAudio()

        #extract the chunk of the sound that we want to play
        start_frame = int(start_time * self.wav_in.getframerate())
        end_frame = int(end_time * self.wav_in.getframerate())
        num_frames = end_frame - start_frame + 1

        #construct and audio stream and write the sound chunk to it
        stream = audio.open(format=audio.get_format_from_width(self.wav_in.getsampwidth()),
                            channels=self.wav_in.getnchannels(),
                            rate=self.wav_in.getframerate(),
                            output=True,
                            )
        self.wav_in.setpos(start_frame)
        data = self.wav_in.readframes(num_frames)
        stream.write(data)

        #clean up
        stream.stop_stream()
        stream.close()
        audio.terminate()

    ## Closes any files or other resources used by this parser.
    #  This should always be called after you're done with the parser!
    #  @param self
    def close(self):
        self.wav_in.close()
