## @package utils.praat_interop

import subprocess
import time
import os
import platform
import socket
import select

from db.bll_database import DBConstants

## This class contains static methods that can be used to perform some basic operations in Praat.
#  To do this, it uses the sendpraat program, available <a href="http://www.fon.hum.uva.nl/praat/sendpraat.html" target="_blank">here</a>. The location of this program on the current machine should be available in the constant DBConstants.SETTINGS.SENDPRAAT_PATH (which is defined in the DB settings table).
class PraatInterop(object):

    ## Opens a Praat instance.
    # Note: Things won't work if you open more than one at a time.
    @staticmethod
    def open_praat():
        praat = subprocess.Popen([DBConstants.SETTINGS.PRAAT_PATH])

        #wait for praat to start up before sending it commands
        time.sleep(0.5)

    ## Closes an open Praat instance.
    @staticmethod
    def close_praat():
        PraatInterop.send_commands(['Quit'])

    ## Sends a list of commands to Praat.
    # These commands are just Strings that manipulate the Praat UI. You can access anything clickable in the UI by its name.
    # If you need to use Praat variables to store stuff, or other Praat scripting language functions, you'll need to open an editor window.
    # See get_sel_bounds_script() for an example of how to do that.
    # This idea is to generate a Praat scripts for a specific task using the get_..._script() methods below. These methods return a list of strings that can be then be passed to this method for execution.
    # This allows us to dynamically generate Praat scripts, using values or other information from our Python scripts.
    # @param cmds (list) list of Praat commands (String). Eg. ['Open long sound file... "mysound.wav"', 'Extract part... 0.0 10.0']
    # @returns (int) 0 on success, nonzero on issue (see subprocess module in Python API for details)
    @staticmethod
    def send_commands(cmds):
        sendpraat_args = [
            DBConstants.SETTINGS.SENDPRAAT_PATH,
                #'0', #the unix version of sendpraat requires an extra 'timeout' argument. This is auto-added below if this is a non-windows system.
                'praat',
            ] + cmds
        if platform.system().lower() != 'windows':
            sendpraat_args.insert(1, '0')

        return subprocess.call(sendpraat_args,
                        shell=False,
                        ) #returns 0 on success

    ## This method returns a script that opens praat and displays a spectrograph of a given section of a given wave file.
    #  The intention is that the user can select a portion with the mouse, and then the selection boundaries
    #  can be retreived with the close_praat() method (below).
    #  @param start_time (float) absolute start time of the clip to display
    #  @param end_time (float) absolute end time of the clip to display
    #  @param wav_filename (string) full path to the wave file to open
    #  @param open_spec_win (boolean=True) set to False if you don't want to open a spectrogram window (this will just extract the sound clip)
    @staticmethod
    def get_open_clip_script(start_time, end_time, wav_filename, open_spec_win=True):
        #open the sound in praat, extract the correct portion, and open a soundEditor window (spectrogram) so the user can select a chunk.
        script = [
            'Open long sound file... %s' % (wav_filename),
            'Extract part... %f %f yes' % (start_time, end_time),
            ]

        if open_spec_win:
            script += ['View & Edit']

        return script

    ## Used in custom_scripts
    @staticmethod
    def get_sel_bounds_script(wav_filename):
        port = int(DBConstants.SETTINGS.PRAAT_IPC_PORT)
        sound_ed_name = os.path.basename(wav_filename)[:-4]

        script = [
            'editor Sound %s' % (sound_ed_name),
            'start = Get start of selection',
            'end = Get end of selection',
            # this causes praat to send a message on a socket created on the specified port
            "sendsocket localhost:%d 'start' 'end'" % (port), #msg format is "<start_time> <end_time>"
            'Close',
            ]

        return script

    ## Used in Melissa's thesis project (see custom_scripts directory)
    @staticmethod
    def get_octave_corrected_pitch_script():
        script = [
            'snd = selected("Sound")',
            'To Pitch... 0.01 60 700',
            'q1 = Get quantile... 0 0 0.25 Hertz',
            'q3 = Get quantile... 0 0 0.75 Hertz',
            'Remove',
            'select snd',
            'floor = 60',
            'ceiling = 700',
            'if q1 != undefined',
            '  floor = q1 * 0.75',
            'endif',
            'if q3 != undefined',
            '  ceiling = q3 * 2.0',
            'endif',
            'pitch = To Pitch... 0.001 floor ceiling',
            ]

        return script

    ## This low-pass filters a clip from a wav file, and saves the clip as a new wav file.
    # Used in relaibility project project (see custom_scripts directory)
    @staticmethod
    def get_low_pass_filter_script(wav_filename, clip_filename, file_code, start_time, stop_time, filter_from, filter_to, filter_smoothing):
        script = [
            "Extract part... %f %f yes" % (start_time, stop_time),
            "Filter (pass Hann band)... %d %d %d" % (filter_from, filter_to, filter_smoothing),
            "max = Get maximum... 0 0 Sinc70",
            "min = Get minimum... 0 0 Sinc70",
            "max_intensity = max(abs(min), abs(max))",
            "scale_factor = 0.999 / max_intensity",
            "Multiply... scale_factor",
            'Save as WAV file... %s' % (clip_filename),
            'select Sound %s' % (file_code + '_band'),
            'Remove',
            'select Sound %s' % (file_code),
            'Remove',
            'select LongSound %s' % (file_code),
        ]

        return script

    ## Used in Melissa's thesis project (see custom_scripts directory)
    @staticmethod
    def get_pitch_sample_vals_script(clip_start, clip_end, wav_filename, step=0.01):
        port = int(DBConstants.SETTINGS.PRAAT_IPC_PORT)
        pitch_ed_name = os.path.basename(wav_filename)[:-4]
        
        script = [
            "View & Edit",
            "editor Pitch %s" % (pitch_ed_name),
            "start = %f" % (clip_start),
            "end = %f" % (clip_end),
            "start_pitch = undefined",
            "start_time = undefined",
            "end_pitch = undefined",
            "end_time = undefined",
            "sample_time = start",
            "while start_pitch == undefined and sample_time <= end",
            "  Move cursor to... 'sample_time'",
            "  pitch = Get pitch",
            "  if pitch != undefined",
            "    start_pitch = pitch",
            "    start_time = sample_time",
            "  endif",
            "  sample_time = sample_time + %f" % (step),
            "endwhile",
            "sample_time = end",
            "while end_pitch == undefined and sample_time >= start",
            "  Move cursor to... 'sample_time'",
            "  pitch = Get pitch",
            "  if pitch != undefined",
            "    end_pitch = pitch",
            "    end_time = sample_time",
            "  endif",
            "  sample_time = sample_time - %f" % (step),
            "endwhile",
            
            "sendsocket localhost:%d 'start_time' 'start_pitch' 'end_time' 'end_pitch'" % (port),
            "Close",
            ]

        return script

    ## Used in Melissa's thesis project (see custom_scripts directory)
    @staticmethod
    def get_pitch_extrema():
        port = int(DBConstants.SETTINGS.PRAAT_IPC_PORT)
        
        script = [
            'min_pitch = Get minimum... 0.0 0.0 Hertz Parabolic',
            'max_pitch = Get maximum... 0.0 0.0 Hertz Parabolic',
            'mean_pitch = Get mean... 0.0 0.0 Hertz',
            "sendsocket localhost:%d 'min_pitch' 'max_pitch' 'mean_pitch'" % (port),
            ]

        return script

    ## Creates a socket to listen for info that Praat is instructed to send.
    #  To see how praat can be intructed to send info, see the get_sel_bounds_script() method.
    #  @param port (int) the port to listen on
    #  @returns (socket) a socket object from the Python socket library. This socket is set up and listening on the specified port.
    @staticmethod
    def create_serversocket():
        port = int(DBConstants.SETTINGS.PRAAT_IPC_PORT)
        
        #create an INET, STREAMing socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.setblocking(0)
        #bind the socket to a public host and a well-known port
        serversocket.bind(('localhost', port))
        #fire up
        serversocket.listen(1)
        
        return serversocket

    ## Receives a message containing the selected boundary information from Praat.
    #  @param serversocket (socket) Python socket library socket object to receive the message on
    #  @returns (list) returns a list of values sent back by Praat. Values should be separated by a space character.
    @staticmethod
    def socket_receive(serversocket, delim=' '):
        #block until we get a connection on the specified port (20 second timeout)
        select.select([serversocket], [], [], 20)
        #now grab the message
        (clientsocket, address) = serversocket.accept()
        c = clientsocket.recv(1)
        msg = ''
        while c != '\x00': #end byte is marked with a zero
            msg += c
            c = clientsocket.recv(1)

        #message is in format '<start_time> <end_time>'
        return msg.split(delim)
