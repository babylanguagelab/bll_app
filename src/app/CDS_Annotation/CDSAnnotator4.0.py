#Written by Sarah MacEwan on June 27, 2017
#Last updated July 5, 2017
#Adapted from convolabel.py by Roman Belenya


import Tkinter as tk
import tkFileDialog
from tkMessageBox import showwarning, askyesno, showinfo
import os
import pyaudio
import wave
import re
# import cPickle
import csv
from numpy import fromstring, arange
import time

from matplotlib import lines, animation, style
style.use('ggplot')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import utils
import makeblocks


class MainWindow:

    def __init__(self, master):

        self.root = master
        self.root.resizable(width = False, height = False)
        self.root.title('Convolabel - IDS Conversation Labelling')
        self.root.protocol('WM_DELETE_WINDOW', self.check_before_exit) # register pressing the x button as event and call the corresponding function
        self.root.bind('<Control-s>', self.submit)

        self.labelled_data = None
        self.data_is_saved = True
        self.audio_data_path = os.path.join(os.getcwd(), 'output')
        self.labelled_data_path = os.path.join(os.getcwd(), 'labelled_data')
        self.current_subject = None
        self.current_block_index = None
        self.current_block_name = None
        self.current_segment_index = None
        self.current_segment_name = None
        self.current_clips = None
        self.block_length = None
        self.segment_length = None
        self.time_of_label = None

        self.frame = tk.Frame(root)
        self.frame.grid(row = 0, column = 0, sticky = 'wns', padx = (30, 0), pady = 30)


        # Menu window
        self.menu = tk.Menu(self.root)
        self.root.config(menu = self.menu)
        self.submenu = tk.Menu(self.menu, tearoff = 0)
        self.menu.add_cascade(label = 'Menu', menu = self.submenu)
        self.submenu.add_command(label = 'Make blocks', command = self.make_blocks)
        self.submenu.add_command(label = 'Save the data', command = self.save)
        self.submenu.add_command(label= 'Export as csv', command = self.export)
       

        # Recordings list box
        tk.Label(self.frame, text = 'Recordings:').grid(row = 2, column = 0, padx = 0, pady = 0, sticky = 'W')
        self.subjects_list = tk.Listbox(self.frame, width = 25, height = 15, exportselection = False, relief = tk.FLAT)
        self.subjects_list.bind('<<ListboxSelect>>', self.update_current_subject)
        self.subjects_scrollbar = tk.Scrollbar(self.frame, orient = 'vertical', command = self.subjects_list.yview)
        self.subjects_list.config(yscrollcommand = self.subjects_scrollbar.set)
        self.subjects_scrollbar.grid(row = 3, column = 0, rowspan = 10, sticky = 'NSE')
        self.subjects_list.grid(row = 3, column = 0, rowspan = 10, padx = (0, 10), pady = 0, sticky = 'W')

        # Blocks list box
        tk.Label(self.frame, text = 'Blocks:').grid(row = 2, column = 1, padx = 5, pady = 0, sticky = 'W')
        self.blocks_list = tk.Listbox(self.frame, width = 25, height = 15, exportselection = False, relief = 'flat')
        self.blocks_list.bind('<<ListboxSelect>>', self.update_current_block)
        #self.blocks_list.bind('<space>', self.play)
        self.blocks_scrollbar = tk.Scrollbar(self.frame, orient = 'vertical', command = self.blocks_list.yview)
        self.blocks_list.config(yscrollcommand = self.blocks_scrollbar.set)
        self.blocks_scrollbar.grid(row = 3, column = 1, rowspan = 10, sticky = 'NSE')
        self.blocks_list.grid(row = 3, column = 1, rowspan = 10, padx = 5, pady = 0, sticky = 'W')
        
        # Segments list box
        tk.Label(self.frame, text = 'Segments:').grid(row = 2, column = 2, padx = 0, pady = 0, sticky = 'W')
        self.segments_list = tk.Listbox(self.frame, width = 25, height = 15, exportselection = False, relief = tk.FLAT)
        self.segments_list.bind('<<ListboxSelect>>', self.update_current_segment)
        self.segments_scrollbar = tk.Scrollbar(self.frame, orient = 'vertical', command = self.segments_list.yview)
        self.segments_list.config(yscrollcommand = self.segments_scrollbar.set)
        self.segments_scrollbar.grid(row = 3, column = 2, rowspan = 10, sticky = 'NSE')
        self.segments_list.grid(row = 3, column = 2, rowspan = 10, padx = 5, pady = 0, sticky = 'W')

        # Coder name entry
        self.coder_name = tk.StringVar()
        self.coder_name.set('--> Coder\'s name <--')
        self.coder_name_entry = tk.Entry(self.frame, justify = tk.CENTER, textvariable = self.coder_name, relief = tk.FLAT)
        self.coder_name_entry.grid(row = 0, column = 0, padx = 0, pady = (0, 20))

        # Buttons
        self.load_data_button = tk.Button(self.frame,
                                        text = 'Load',
                                        command = self.load_subjects,
                                        height = 1,
                                        width = 12,
                                        relief = tk.GROOVE).grid(row = 4, column = 3, padx = 20)

        self.play_block_button = tk.Button(self.frame,
                                        text = 'Play Block',
                                        command = self.play_block,
                                        height = 1,
                                        width = 12,
                                        relief = tk.GROOVE)
        self.play_block_button.bind('<Enter>', self.show_block_length)
        self.play_block_button.bind('<Leave>', lambda event, self = self: self.play_block_button.configure(text = 'Play Block'))
        self.play_block_button.grid(row = 5, column = 3, padx = 0)
        
        
        self.play_segment_button = tk.Button(self.frame,
                                        text = 'Play Segment',
                                        command = self.play_segment,
                                        height = 1,
                                        width = 12,
                                        relief = tk.GROOVE)
        self.play_segment_button.bind('<Enter>', self.show_segment_length)
        self.play_segment_button.bind('<Leave>', lambda event, self = self: self.play_segment_button.configure(text = 'Play Segment'))
        self.play_segment_button.grid(row = 6, column = 3, padx = 0)

        self.submit_button = tk.Button(self.frame,
                                        text = 'Submit',
                                        command = self.submit,
                                        height = 1,
                                        width = 12,
                                        relief = tk.GROOVE).grid(row = 7, column = 3, padx = 0)

        


################################### Labels ###########################################

        self.labels = {
            'ads': tk.IntVar(),
            'cds': tk.IntVar(),
            'ocs': tk.IntVar(),
            'sensitive': tk.IntVar(),
            'other_langue': tk.IntVar(),
            'descriptive': tk.StringVar(),
            'target_child': tk.IntVar()
        }
        self.junk = tk.IntVar()

        # Default parameters for the entries
        entry_params = {'width': 3, 'state': 'disabled', 'justify': 'center', 'relief': 'flat'}
        entry_grid_params = {'sticky': tk.E, 'padx': (2, 20), 'pady': 3}
        label_grid_params = {'sticky': tk.E, 'padx': 0, 'pady': 2}


        self.labels_frame = tk.Frame(self.root)
        self.labels_frame.grid(row = 1, column = 0, padx = 30, columnspan = 2, sticky = tk.W)

        #Whole block is junk checkbutton
        self.whole_block_junk = tk.Checkbutton(self.frame, text = 'Block is Junk', variable = self.junk, command = self.whole_block_junk_selected, state = 'disabled')
        self.whole_block_junk.grid(row = 8, column = 3, padx = (2, 10), pady = (3, 1))
        
        # Junk checkbutton
        self.junk_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Junk', variable = self.junk, command = self.junk_selected, state = 'disabled')
        self.junk_checkbutton.grid(row = 0, column = 0, sticky = tk.W, padx = (2, 10), pady = (3, 1))

        # Sesitive checkbutton
        self.sensitive_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Sensitive', variable = self.labels['sensitive'], state = 'disabled')
        self.sensitive_checkbutton.grid(row = 0, column = 1, sticky = tk.W, padx = (2, 10), pady = (0, 0))

        # Other language checkbutton
        self.other_langue_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Other language', variable = self.labels['other_langue'], state = 'disabled')
        self.other_langue_checkbutton.grid(row = 0, column = 2, sticky = tk.W, padx = (2, 10), pady = (1, 0))
        
        
        # Adult-directed speech
        self.ads = tk.Checkbutton(self.labels_frame, text = 'Adult-directed speech', variable = self.labels['ads'], state = 'disabled')
        self.ads.grid(label_grid_params, row = 1, column = 0)
        
        # Child-directed speech
        self.cds = tk.Checkbutton(self.labels_frame, text = 'Child-directed speech', variable = self.labels['cds'], state = 'disabled')
        self.cds.grid(label_grid_params, row = 1, column = 1)

        # Other child speech
        self.ocs = tk.Checkbutton(self.labels_frame, text = 'Other child speech', variable = self.labels['ocs'], state = 'disabled')
        self.ocs.grid(label_grid_params, row = 1, column = 2)
       
        # Speech is directed at target child
        self.target_child = tk.Checkbutton(self.labels_frame, text = 'At target child', variable = self.labels['target_child'], state = 'disabled')
        self.target_child.grid(label_grid_params, row = 2, column = 1)

        #self.BUTTON_NAMES = ['speaker_action', 'speaker_emotion', 'speaker_ps_state', 'speaker_wantsneeds', 'speaker_thots', 'baby_action', 'baby_emotion', 'baby_ps_state', 'baby_wantsneeds', 'baby_thots', 'external_world_action', 'external_world_emotion', 'external_world_ps_state', 'external_world_wantsneeds', 'external_world_thots', 'obj_labelling', 'obj_description', 'events']
        
        
        # speaker label
        self.speaker_label = tk.Label(self.labels_frame, text = 'Speaker:').grid(label_grid_params, row = 3, column = 0, sticky = 'W')
        
        #Change the variables to strings :)
        #create speaker Radiobuttons
        self.speaker_action = tk.Radiobutton(self.labels_frame, text = "Action", variable = self.labels['descriptive'], value = 'Speaker Action', state = 'disabled')
        self.speaker_action.grid(label_grid_params, row = 4, column = 0, sticky = 'W')
        self.speaker_emotion = tk.Radiobutton(self.labels_frame, text = "Emotion", variable = self.labels['descriptive'], value = 'Speaker Emotion', state = 'disabled')
        self.speaker_emotion.grid(label_grid_params, row = 5, column = 0, sticky = 'W')
        self.speaker_ps_state = tk.Radiobutton(self.labels_frame, text = "Physical State", variable = self.labels['descriptive'], value = 'Speaker Physical State', state = 'disabled')
        self.speaker_ps_state.grid(label_grid_params, row = 6, column = 0, sticky = 'W')
        self.speaker_wantsneeds = tk.Radiobutton(self.labels_frame, text = "Want / Need", variable = self.labels['descriptive'], value = 'Speaker Want / Need', state = 'disabled')
        self.speaker_wantsneeds.grid(label_grid_params, row = 7, column = 0, sticky = 'W')
        self.speaker_thots = tk.Radiobutton(self.labels_frame, text = "Thoughts", variable = self.labels['descriptive'], value = 'Speaker Thoughts', state = 'disabled')
        self.speaker_thots.grid(label_grid_params, row = 8, column = 0, sticky = 'W')
        
        # baby label
        self.baby_label = tk.Label(self.labels_frame, text = 'Baby:').grid(label_grid_params, row = 3, column = 1, sticky = 'W')
        
        #create baby Radiobuttons
        self.baby_action = tk.Radiobutton(self.labels_frame, text = "Action", variable = self.labels['descriptive'], value = 'Baby Action', state = 'disabled')
        self.baby_action.grid(label_grid_params, row = 4, column = 1, sticky = 'W')
        self.baby_emotion = tk.Radiobutton(self.labels_frame, text = "Emotion", variable = self.labels['descriptive'], value = 'Baby Emotion', state = 'disabled')
        self.baby_emotion.grid(label_grid_params, row = 5, column = 1, sticky = 'W')
        self.baby_ps_state = tk.Radiobutton(self.labels_frame, text = "Physical State", variable = self.labels['descriptive'], value = 'Baby Physical State', state = 'disabled')
        self.baby_ps_state.grid(label_grid_params, row = 6, column = 1, sticky = 'W')
        self.baby_wantsneeds = tk.Radiobutton(self.labels_frame, text = "Want / Need", variable = self.labels['descriptive'], value = 'Baby Want / Need', state = 'disabled')
        self.baby_wantsneeds.grid(label_grid_params, row = 7, column = 1, sticky = 'W')
        self.baby_thots = tk.Radiobutton(self.labels_frame, text = "Thoughts", variable = self.labels['descriptive'], value = 'Baby Thoughts', state = 'disabled')
        self.baby_thots.grid(label_grid_params, row = 8, column = 1, sticky = 'W')
        
        # external world label
        self.external_world_label = tk.Label(self.labels_frame, text = 'External World:').grid(label_grid_params, row = 3, column = 2, sticky = 'W')
        
        #external world radiobuttons
        self.external_world_action = tk.Radiobutton(self.labels_frame, text = "Action", variable = self.labels['descriptive'], value = "Other's Action", state = 'disabled')
        self.external_world_action.grid(label_grid_params, row = 4, column = 2, sticky = 'W')
        self.external_world_emotion = tk.Radiobutton(self.labels_frame, text = "Emotion", variable = self.labels['descriptive'], value = "Other's Emotion", state = 'disabled')
        self.external_world_emotion.grid(label_grid_params, row = 5, column = 2, sticky = 'W')
        self.external_world_ps_state = tk.Radiobutton(self.labels_frame, text = "Physical State", variable = self.labels['descriptive'], value = "Other's Physical State", state = 'disabled')
        self.external_world_ps_state.grid(label_grid_params, row = 6, column = 2, sticky = 'W')
        self.external_world_wantsneeds = tk.Radiobutton(self.labels_frame, text = "Want / Need", variable = self.labels['descriptive'], value = "Other's Want / Need", state = 'disabled')
        self.external_world_wantsneeds.grid(label_grid_params, row = 7, column = 2, sticky = 'W')
        self.external_world_thots = tk.Radiobutton(self.labels_frame, text = "Thoughts", variable = self.labels['descriptive'], value = "Other's Thoughts", state = 'disabled')
        self.external_world_thots.grid(label_grid_params, row = 8, column = 2, sticky = 'W')
        self.obj_labelling = tk.Radiobutton(self.labels_frame, text = "Object Labelling", variable = self.labels['descriptive'], value = 'Object Labelling', state = 'disabled')
        self.obj_labelling.grid(label_grid_params, row = 9, column = 2, sticky = 'W')
        self.obj_description = tk.Radiobutton(self.labels_frame, text = "Object Description", variable = self.labels['descriptive'], value = 'Object Description', state = 'disabled')
        self.obj_description.grid(label_grid_params, row = 10, column = 2, sticky = 'W')
        self.events = tk.Radiobutton(self.labels_frame, text = "Events", variable = self.labels['descriptive'], value = 'Events', state = 'disabled')
        self.events.grid(label_grid_params, row = 11, column = 2, sticky = 'W')
        
        #Other category of speech button
        self.other_category = tk.Radiobutton(self.labels_frame, text = 'Other Category', variable = self.labels['descriptive'], value = 'Other Speech Category', state = 'disabled')
        self.other_category.grid(label_grid_params, row = 10, column = 0, sticky = 'W')
        
        
        
        # Trace command passes three arguments (x, y, z) to the labmda function.
        self.labels['cds'].trace('w', self.check_cds)
        self.labels['target_child'].trace('w', self.check_target_child)        
        self.entries_handles = filter(lambda x: isinstance(x, tk.Entry), self.labels_frame.children.itervalues())

        # Comments box
        self.comments_label = tk.Label(self.labels_frame, text = 'Comments:').grid(row = 0, column = 3, padx = 5, sticky = 'W')
        self.comments = tk.Text(self.labels_frame, height = 20, width = 50, state = 'disabled', relief = tk.FLAT)
        self.comments.grid(row = 1, column = 3, rowspan = 10, padx = 5, pady = 0)

        # Status bar
        self.status_bar_frame = tk.Frame(self.root)
        self.status_bar_frame.grid(row = 2, column = 0, sticky = 'we', padx = 20, pady = 10)
        self.bar = tk.StringVar()
        self.status_bar = tk.Label(self.status_bar_frame, textvariable = self.bar)
        self.status_bar.grid(row = 0, column = 0)

        # Waveform graph
        self.graph_frame = tk.Frame(self.root)#, bd = 1, relief = 'sunken')
        self.graph_frame.grid(row = 0, column = 1, sticky = 'wns', pady = 30)
        self.fig = Figure(figsize = (5, 5), dpi = 60)
        self.ax = self.fig.add_subplot(111)
        self.wave_line, = self.ax.plot([], [], color = [0.2, 0.2, 0.2])
        self.ax.set_ylim(-1, 1)
        self.fig.patch.set_visible(False)
        self.ax.set_xlabel('Time (s)')
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.graph_frame)
        self.canvas.get_tk_widget().grid(row = 1, column = 0)


    def show_block_length(self, event):
        ''' Executes when hover over the play block button '''
        if self.block_length != None:
            self.play_block_button.configure(text = '%.2f s' % self.block_length)
            
            
    def show_segment_length(self, event):
        '''Executes when you hover over the play segment button '''
        if self.segment_length != None:
            self.play_segment_button.configure(text = '%.2f s' % self.segment_length)


    def check_cds(self, *args):
        if self.labels['cds'].get() == 1:
            self.target_child.configure(state = 'normal')
        else:
            self.target_child.configure(state = 'disabled')

    def check_target_child(self, *args):
        if self.labels['target_child'].get() == 0:
            self.speaker_action.configure(state = 'disabled')
            self.speaker_emotion.configure(state = 'disabled')
            self.speaker_ps_state.configure(state = 'disabled')
            self.speaker_wantsneeds.configure(state = 'disabled')
            self.speaker_wantsneeds.configure(state = 'disabled')
            self.speaker_thots.configure(state = 'disabled')
            self.baby_action.configure(state = 'disabled')
            self.baby_emotion.configure(state = 'disabled')
            self.baby_ps_state.configure(state = 'disabled')
            self.baby_wantsneeds.configure(state = 'disabled')
            self.baby_thots.configure(state = 'disabled')
            self.external_world_action.configure(state = 'disabled')
            self.external_world_emotion.configure(state = 'disabled')
            self.external_world_ps_state.configure(state = 'disabled')
            self.external_world_wantsneeds.configure(state = 'disabled')
            self.external_world_thots.configure(state = 'disabled')
            self.obj_labelling.configure(state = 'disabled')
            self.obj_description.configure(state = 'disabled')
            self.events.configure(state = 'disabled')
            self.other_category.configure(state = 'disabled')
        else:
            self.speaker_action.configure(state = 'normal')
            self.speaker_emotion.configure(state = 'normal')
            self.speaker_ps_state.configure(state = 'normal')
            self.speaker_wantsneeds.configure(state = 'normal')
            self.speaker_wantsneeds.configure(state = 'normal')
            self.speaker_thots.configure(state = 'normal')
            self.baby_action.configure(state = 'normal')
            self.baby_emotion.configure(state = 'normal')
            self.baby_ps_state.configure(state = 'normal')
            self.baby_wantsneeds.configure(state = 'normal')
            self.baby_thots.configure(state = 'normal')
            self.external_world_action.configure(state = 'normal')
            self.external_world_emotion.configure(state = 'normal')
            self.external_world_ps_state.configure(state = 'normal')
            self.external_world_wantsneeds.configure(state = 'normal')
            self.external_world_thots.configure(state = 'normal')
            self.obj_labelling.configure(state = 'normal')
            self.obj_description.configure(state = 'normal')
            self.events.configure(state = 'normal')
            self.other_category.configure(state = 'normal')


    def whole_block_junk_selected(self):
        if self.junk.get() == 1:
            self.entry_initial_state()
            self.sensitive_checkbutton.configure(state = 'disabled')
            self.other_langue_checkbutton.configure(state = 'disabled')
            self.ads.configure(state = 'disabled')
            self.cds.configure(state = 'disabled')
            self.ocs.configure(state = 'disabled')
            clips_path = os.path.abspath(os.path.join(self.audio_data_path, self.current_subject, self.current_block_name))
            clips = [ name for name in os.listdir(clips_path) if name.endswith('.wav') ]
            count = 0
            for seg in clips:
                self.segments_list.selection_clear(0, tk.END)
                self.segments_list.select_set(count)
                #self.junk.set(1)
                self.segments_list.event_generate("<<ListboxSelect>>")
                self.junk_checkbutton.select()
                self.submit()
                count += 1
        else:
            self.entry_initial_state()
            self.sensitive_checkbutton.configure(state = 'normal')
            self.other_langue_checkbutton.configure(state = 'normal')
            self.ads.configure(state = 'normal')
            self.cds.configure(state = 'normal')
            self.ocs.configure(state = 'normal')
            self.whole_block_junk.configure(state = 'normal')
    
    def junk_selected(self):
        if self.junk.get() == 1:
            self.entry_initial_state()
            self.sensitive_checkbutton.configure(state = 'disabled')
            self.other_langue_checkbutton.configure(state = 'disabled')
            self.ads.configure(state = 'disabled')
            self.cds.configure(state = 'disabled')
            self.ocs.configure(state = 'disabled')
        else:
            self.entry_initial_state()
            self.sensitive_checkbutton.configure(state = 'normal')
            self.other_langue_checkbutton.configure(state = 'normal')
            self.ads.configure(state = 'normal')
            self.cds.configure(state = 'normal')
            self.ocs.configure(state = 'normal')
            self.junk_checkbutton.configure(state = 'normal')


    def make_blocks(self):

        ans = askyesno('Making blocks', 'Click yes to start processing blocks, no to cancel')
        if ans == 0:
            return

        to_input_data = os.path.join(os.getcwd(), 'input')
        folders = os.listdir(to_input_data)

        if folders == []:
            showwarning('No blocks are found', 'The input directory is empty!')
            return

        for folder in folders:
            if folder.startswith('.'):
                continue
            files = os.listdir(os.path.join(to_input_data, folder))
            if not any(file.endswith('.cha') for file in files):
                showwarning('Files missing', 'No .cha file for {}'.format(folder))
                return
            elif not any(file.endswith('.wav') for file in files):
                showwarning('Files missing', 'No .wav file for {}'.format(folder))
                return

            wavfile = [file for file in files if file.endswith('.wav')]
            chafile = [file for file in files if file.endswith('.cha')]

            if wavfile[0].strip('.wav') != chafile[0].strip('.cha'):
                showwarning('Files issue', 'cha and wav file names do not match for {}'.format(folder))
                return

        t0 = time.time()
        makeblocks.main('input', 'output')
        t = round((time.time() - t0) / 60, 2)

        showinfo('All done!', 'Processing has finished\n\nProcessed recordings: {}\nTotal time: {} min'.format(len(folders), t))

        self.load_subjects()



    def load_subjects(self):

        coder = self.coder_name.get()
        coders = [name.strip('.pkl') for name in os.listdir(self.labelled_data_path) if name.endswith('.pkl')]

        # Check if coder's name is entered. If so, check if it exists in the data
        if coder == '--> Coder\'s name <--':
            showwarning('Coder\'s name', 'Please enter your name')
            return
        elif coder not in coders:
            ans = askyesno('Coder\'s name', 'Didn\'t recognise the coder\'s name. Create new?')
            if ans == 1:
                self.labelled_data = {}
            else:
                return
        else:
            self.labelled_data = utils.load_data( os.path.join(self.labelled_data_path, coder + '.pkl') )

        # Remove all recordings and blocks from the list boxes
        if self.subjects_list.get(0, tk.END) != ():
            self.subjects_list.delete(0, tk.END)
        if self.blocks_list.get(0, tk.END) != ():
            self.blocks_list.delete(0, tk.END)

        # Subjects are the recordings (e.g C208_20150101). Every folder in the data path is considered a subject
        names = [name for name in os.listdir(self.audio_data_path) if os.path.isdir(os.path.join( self.audio_data_path, name ))]
        try:
            regexp = re.compile('\d+')
            names_sorted = sorted(names, key = lambda x: int(regexp.search(x).group()))
        except:
            names_sorted = sorted(names, key = str)

        for name in names_sorted:
            self.subjects_list.insert(tk.END, name)


    def update_current_subject(self, event):
        ''' Executes on selection from the recording list box. Recording = subject here '''

        coder = self.coder_name.get()
        if self.subjects_list.get(0, tk.END) == (): # this is to prevent an error which pops up if user clicks on an empty list
            return

        w = event.widget
        self.current_subject = w.get(int(w.curselection()[0]))
        
        if self.current_subject not in self.labelled_data.keys():
            self.labelled_data[self.current_subject] = {}

        
        self.current_block_index = None
        self.current_block_name = None
        self.current_segment_index = None
        self.current_segment_name = None
        self.current_clips = None
        self.block_length = None
        self.segment_length = None
        self.time_of_label = None

        # Plot the empty line = clear the graph
        self.wave_line.set_data([], [])
        self.canvas.show()

        # The entries, checkbuttons and comments box stay disabled until a block is selected
        self.entry_initial_state()
        self.whole_block_junk.configure(state = 'disabled')
        self.junk.set(0)
        self.junk_checkbutton.configure(state = 'disabled')
        self.sensitive_checkbutton.configure(state = 'disabled')
        self.other_langue_checkbutton.configure(state = 'disabled')
        self.comments.delete(1.0, tk.END)
        self.comments.configure(state = 'disabled')

        

        # If there are some blocks in the listbox, delete them
        if self.blocks_list.get(0, tk.END) != ():
            self.blocks_list.delete(0, tk.END)

        path = os.path.join( self.audio_data_path, self.current_subject ) # path to the folder containing blocks for the selected subject
        names = [ name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name)) ] # creates a generator with paths to the individual block names

        # Sort the names of the blocks in ascending order. This block of code takes a lot of time
        regexp = re.compile('\d+')
        try:
            names_sorted = sorted(names, key = lambda x: int( regexp.search(x).group() )) # look for an integer in the name of a block and sort according to this integer
        except:
            names_sorted = sorted(names, key = str) # if all else fails, sort alphabetically


        for name in names_sorted:
            self.blocks_list.insert(tk.END, name)
            
        
    def update_current_block(self, event):
        ''' Executes on block selection from the list box '''
        
        self.bar.set('')

        coder = self.coder_name.get()
        if self.blocks_list.get(0, tk.END) == (): # this is to prevent an error which pops up if user clicks on an empty list
            return
            
        

        w = event.widget
        self.current_block_index = int(w.curselection()[0])
        self.current_block_name = w.get(self.current_block_index)
        self.string_block_name = str(self.current_block_name)
        
        if self.current_block_name not in self.labelled_data[self.current_subject].keys():
            self.labelled_data[self.current_subject][self.current_block_name] = {}
        
        self.current_segment_index = None
        self.current_segment_name = None
        self.current_clips = None
        self.segment_length = None
        self.time_of_label = None

        # The entries, checkbuttons and comments box stay disabled until a segment is selected
        self.entry_initial_state()
        self.whole_block_junk.configure(state = 'normal')
        self.junk.set(0)
        self.junk_checkbutton.configure(state = 'disabled')
        self.sensitive_checkbutton.configure(state = 'disabled')
        self.other_langue_checkbutton.configure(state = 'disabled')
        self.ads.configure(state = 'disabled')
        self.cds.configure(state = 'disabled')
        self.ocs.configure(state = 'disabled')
        self.comments.delete(1.0, tk.END)
        self.comments.configure(state = 'disabled')

        

        # If there are some segments in the listbox, delete them
        if self.segments_list.get(0, tk.END) != ():
            self.segments_list.delete(0, tk.END)

        path = os.path.join( self.audio_data_path, self.current_subject, self.string_block_name ) # path to the folder containing blocks for the selected subject
        names = [ name for name in os.listdir(path) if name.endswith('.wav') ] # creates a generator with paths to the individual block names

        # Sort the names of the blocks in ascending order. This block of code takes a lot of time
        regexp = re.compile('\d+')
        try:
            names_sorted = sorted(names, key = lambda x: int( regexp.search(x).group() )) # look for an integer in the name of a block and sort according to this integer
        except:
            names_sorted = sorted(names, key = str) # if all else fails, sort alphabetically


        for name in names_sorted:
            self.segments_list.insert(tk.END, name)
            if name in self.labelled_data[self.current_subject][self.current_block_name].keys():
                self.segments_list.itemconfig(tk.END, foreground = 'gray')
        
        #This is so that the blocks are playable
        clips_path = os.path.abspath(os.path.join(self.audio_data_path, self.current_subject, self.current_block_name))
        clips = [ name for name in os.listdir(clips_path) if name.endswith('.wav') ]

        # Make sure that the clips are in the right order
        try:
            clips_sorted = sorted(clips, key = lambda x: int(x[:-4])) # [:-4] removes the .wav from the clip's name
        except:
            clips_sorted = sorted(clips, key = str)
        self.current_clips = [ os.path.join(clips_path, name) for name in clips_sorted ]

        data, n_channels, sample_width, sample_rate = utils.merge_clips(self.current_clips)
        
        # Convert the audio string to float vector
        bits = sample_width * 8 # each sample in the audio is represented by sample_width bytes. 1 byte = 8 bits
        d_type = 'int{}'.format(bits)
        norm = (2 ** bits) / 2.0 - 1 # norm is the maximum integer above zero available in a dtype. eg 32767 for int16. OR np.iinfo(d_type).max
        if n_channels == 1:
            data = fromstring(data, dtype = d_type) / norm # numpy function
        elif n_channels == 2:
            data = fromstring(data, dtype = d_type)[0::2] / norm # if n_channels is 2, [0::2] accesses every second frame, e.g. only from one channel
        else:
            self.bar.set('Unable to show the graph :(')
            return

        # Calculate the block duration
        self.block_length = len(data) / float(sample_rate)
        times = arange( 0, self.block_length, self.block_length / float(len(data)) ) # numpy function

        # Plot the audio waveform
        try:
            self.wave_line.set_data(times, data)
            self.ax.set_xlim(0 - self.block_length/20.0, self.block_length + self.block_length/20.0)
            self.canvas.show()
        except:
            self.wave_line.set_data([], [])
            self.canvas.show()
            self.bar.set('Unable to show the graph :(')
            
       # if self.whole_block_junk_selected == True:
        #    for seg in clips:
         #       self.segmetn_list.select_set(seg)
          #      self.update_current_segment(self, self.segments_list.generate("<<ListboxSelect>>"))
           #     self.submit()
            
    def update_current_segment(self, event):
        ''' Executes on segment selection from the list box '''

        self.bar.set('')

        if self.segments_list.get(0, tk.END) == (): # this is supposed to prevent an error which pops up if user clicks on an empty segments list
            return
        
        w = event.widget
        self.current_segment_index = int(w.curselection()[0])
        self.current_segment_name = w.get(self.current_segment_index)
        self.string_segment_name = str(self.current_segment_name)
       
        
        coder = self.coder_name.get()
        subject = self.current_subject
        block = self.current_block_name
        segment = self.current_segment_name
        
        if self.whole_block_junk_selected == True:
            self.entry_initial_state() # if the block was not previously labelled, reset the entries
            self.junk.set(1)
            self.comments.configure(state = 'normal')
            self.comments.delete(1.0, tk.END)
            self.ads.configure(state = 'disabled')
            self.cds.configure(state = 'disabled')
            self.ocs.configure(state = 'disabled')
            self.junk_checkbutton.configure(state = 'disabled')
            self.sensitive_checkbutton.configure(state = 'disabled')
            self.other_langue_checkbutton.configure(state = 'disabled')

        if segment in self.labelled_data[subject][block].keys(): # if the segment was already labelled, load the labels
            for label in self.labels.keys():
                self.labels[label].set(self.labelled_data[subject][block][segment][label])
            self.junk.set(self.labelled_data[subject][block][segment]['junk'])
            self.ads.configure(state = 'normal')
            self.cds.configure(state = 'normal')
            self.ocs.configure(state = 'normal')
            self.junk_checkbutton.configure(state = 'normal')
            self.sensitive_checkbutton.configure(state = 'normal')
            self.other_langue_checkbutton.configure(state = 'normal')
            self.comments.configure(state = 'normal')
            self.comments.delete(1.0, tk.END)
            self.comments.insert(tk.END, self.labelled_data[subject][block][segment]['comments'])

            if self.junk.get() == 1:
                self.entry_initial_state()

            self.bar.set('Labeled at {}'.format(self.labelled_data[subject][block][segment]['time']))

            
        else:
            self.entry_initial_state() # if the block was not previously labelled, reset the entries
            self.junk.set(0)
            self.comments.configure(state = 'normal')
            self.comments.delete(1.0, tk.END)
            self.ads.configure(state = 'normal')
            self.cds.configure(state = 'normal')
            self.ocs.configure(state = 'normal')
            self.junk_checkbutton.configure(state = 'normal')
            self.sensitive_checkbutton.configure(state = 'normal')
            self.other_langue_checkbutton.configure(state = 'normal')

        clips_path = os.path.abspath(os.path.join(self.audio_data_path, self.current_subject, self.current_block_name))
        clips = [ name for name in os.listdir(clips_path) if name.endswith('.wav') ]

        # Make sure that the clips are in the right order
        try:
            clips_sorted = sorted(clips, key = lambda x: int(x[:-4])) # [:-4] removes the .wav from the clip's name
        except:
            clips_sorted = sorted(clips, key = str)
        self.current_clips = [ os.path.join(clips_path, name) for name in clips_sorted ]

        f = wave.open(os.path.join(os.getcwd(), 'output', self.current_subject, self.current_block_name, self.current_segment_name), 'rb')
        data = f.readframes(-1)
        
        n_channels, sample_width, sample_rate, _, _, _ = f.getparams()

        # Convert the audio string to float vector
        bits = sample_width * 8 # each sample in the audio is represented by sample_width bytes. 1 byte = 8 bits
        d_type = 'int{}'.format(bits)
        norm = (2 ** bits) / 2.0 - 1 # norm is the maximum integer above zero available in a dtype. eg 32767 for int16. OR np.iinfo(d_type).max
        if n_channels == 1:
            data = fromstring(data, dtype = d_type) / norm # numpy function
        elif n_channels == 2:
            data = fromstring(data, dtype = d_type)[0::2] / norm # if n_channels is 2, [0::2] accesses every second frame, e.g. only from one channel
        else:
            self.bar.set('Unable to show the graph :(')
            return

        # Calculate the segment duration
        self.segment_length = len(data) / float(sample_rate)
        times = arange( 0, self.segment_length, self.segment_length / float(len(data)) ) # numpy function

        # Plot the audio waveform
        try:
            self.wave_line.set_data(times, data)
            self.ax.set_xlim(0 - self.segment_length/20.0, self.segment_length + self.segment_length/20.0)
            self.canvas.show()
        except:
            self.wave_line.set_data([], [])
            self.canvas.show()
            self.bar.set('Unable to show the graph :(')



    def entry_initial_state(self):
        ''' Resets and clears the entries '''

        for entry in self.entries_handles:
            entry.configure(state = 'disabled')
        for label in self.labels.values():
            label.set(0)
        if self.junk.get() == 0:
            self.junk_checkbutton.configure(state = 'disabled')
        else:
            self.junk_checkbutton.configure(state = 'normal')


    def play_block(self, *event):
        ''' Plays selected block '''

        if self.current_block_name == '':
            showwarning('Block error','Choose the block')
            return

        data, n_channels, sample_width, sample_rate = utils.merge_clips(self.current_clips)

        lf = len(data) # number of frames in the data. if sample width is 4, every sample contains 4 frames
        background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        line = self.ax.add_line(lines.Line2D([0, 0], [-0.95, 0.95], alpha = 0.8, color = '#FFA9A5')) # the sliding bar

        chunk = 1024 # frames to access on every iteration
        x0 = 0 # start index
        x1 = chunk # end index

        p = pyaudio.PyAudio()
        stream = p.open(format = p.get_format_from_width(sample_width),
                        channels = n_channels,
                        rate = sample_rate,
                        output = True)


        # http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
        while x0 + chunk < lf:
            stream.write(data[x0:x1])
            self.fig.canvas.restore_region(background)
            line.set_xdata((x1 / n_channels / sample_width) / float(sample_rate)) # offset by 1024 frames; convert to seconds
            self.ax.draw_artist(line)
            self.fig.canvas.blit(self.ax.bbox)
            self.fig.canvas.flush_events()

            x0 += chunk
            x1 += chunk
        else:
            stream.write(data[x0:]) # play the rest of the audio
            self.fig.canvas.restore_region(background)
            line.set_xdata((len(data) / sample_width) / float(sample_rate))
            self.ax.draw_artist(line)
            self.fig.canvas.blit(self.ax.bbox)
            self.fig.canvas.flush_events()

        line.remove()
        self.canvas.show()

        stream.stop_stream()
        stream.close()
        p.terminate()

    def play_segment(self):
        ''' Plays selected segment '''

        if self.current_segment_name == '':
            showwarning('Block error','Choose the block')
            return
        #store in a variable s.path_to_segment, path_to_block... etc?
        f = wave.open(os.path.join(os.getcwd(), 'output', self.current_subject, self.current_block_name, self.current_segment_name), 'rb')
        data = f.readframes(-1)
        
        n_channels, sample_width, sample_rate, _, _, _ = f.getparams()

        lf = len(data) # number of frames in the data. if sample width is 4, every sample contains 4 frames
        background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        line = self.ax.add_line(lines.Line2D([0, 0], [-0.95, 0.95], alpha = 0.8, color = '#FFA9A5')) # the sliding bar

        chunk = 1024 # frames to access on every iteration
        x0 = 0 # start index
        x1 = chunk # end index

        p = pyaudio.PyAudio()
        stream = p.open(format = p.get_format_from_width(sample_width),
                        channels = n_channels,
                        rate = sample_rate,
                        output = True)


        # http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
        while x0 + chunk < lf:
            stream.write(data[x0:x1])
            self.fig.canvas.restore_region(background)
            line.set_xdata((x1 / n_channels / sample_width) / float(sample_rate)) # offset by 1024 frames; convert to seconds
            self.ax.draw_artist(line)
            self.fig.canvas.blit(self.ax.bbox)
            self.fig.canvas.flush_events()

            x0 += chunk
            x1 += chunk
        else:
            stream.write(data[x0:]) # play the rest of the audio
            self.fig.canvas.restore_region(background)
            line.set_xdata((len(data) / sample_width) / float(sample_rate))
            self.ax.draw_artist(line)
            self.fig.canvas.blit(self.ax.bbox)
            self.fig.canvas.flush_events()

        line.remove()
        self.canvas.show()

        stream.stop_stream()
        stream.close()
        p.terminate()
        pass

    def submit(self, *event):
        ''' Appends the labels to self.labelled_data '''

        if self.current_segment_name == '' or None:
            showwarning('Segment error','Choose the segment')
            return

        coder = self.coder_name.get()
        subject = self.current_subject
        block = self.current_block_name
        segment = self.current_segment_name


        # Fetch the labels
        current_labels = {}
        for label in self.labels.keys():
            current_labels[label] = self.labels[label].get()
        current_labels['junk'] = self.junk.get()
        current_labels['time'] = time.strftime('%H:%M, %d %B %Y') # this is the time at which the segment was labelled
        current_labels['length'] = self.segment_length
        current_labels['comments'] = self.comments.get(1.0, tk.END).strip() # the .strip() removes a new line that tkinter inserts
        logfile = os.path.join('./backups', coder + '.log')
        with open(logfile, 'ab') as f:
            # f.write(coder + ' ' + subject + ' ' + block + ' ' + str(current_labels) + '\n')
            f.write( '-'.join([coder, subject, block, segment, str(current_labels)]) + '\n' )

        # # Save the labels from the entries to the memory (self.labelled_data)
        self.labelled_data[subject][block][segment] = current_labels

        self.bar.set('Labels submitted!')
        self.segments_list.itemconfig(self.current_segment_index, foreground = 'gray')
        self.segments_list.focus_set()
        self.data_is_saved = False
        self.root.title('Convolabel - IDS Conversation Labelling  *')


    def save(self):
        ''' Loads the data file, updates the current data, saves the file on the hard drive '''

        coder = self.coder_name.get()

        logfile = os.path.join('./backups', coder + '.log')
        with open(logfile, 'a') as f:
            f.write('saved_at' + time.strftime('%H:%M:%S_%d%B%Y') + '\n')

        # Save the data and overwrite the data file
        utils.save_data(self.labelled_data, os.path.join(self.labelled_data_path, coder + '.pkl'))

        # Make a backup
        name = coder + '_' + time.strftime('%H%M%S_%d%B%Y') + '.pkl'
        utils.save_data(self.labelled_data, os.path.join('./backups', name))

        self.bar.set('Data is saved!')
        self.data_is_saved = True
        self.root.title('Convolabel - IDS Conversation Labelling')


    def export(self):
        ''' Exports the current state of data to csv file. All coders are included '''

        output = tkFileDialog.asksaveasfilename(filetypes = [('Comma-separated file', '.csv')], initialfile = 'data.csv' )
        if output == '':
            return

        coders_data = [d for d in os.listdir(self.labelled_data_path) if d.endswith('.pkl')]
        d = utils.merge_coders_data(self.labelled_data_path, coders_data)

        with open(output, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Date coded', 'Coder', 'Recording', 'Block', 'Segment', 'Segment length', 'Junk', 'Sensitive',
                            'Other language', 'Adult-directed speech', 'Child-directed speech', 'Other child speech', 'Directed at Target Child',
                            'Directive Speech Type', 
                             'Comments'])
        
        
            for coder, coderDict in d.items():
                for subject, subjectDict in coderDict.items():
                    for block, blockDict in subjectDict.items():
                        if block.startswith('_'): continue # skip the sample clips
                        for segment, segmentDict in blockDict.items():
                            writer.writerow([
                                segmentDict['time'],
                                coder,
                                subject,
                                block,
                                segment,
                                segmentDict['length'],
                                segmentDict['junk'],
                                segmentDict['sensitive'],
                                segmentDict['other_langue'],
                                segmentDict['ads'],
                                segmentDict['cds'],
                                segmentDict['ocs'],
                                segmentDict['target_child'],
                                segmentDict['descriptive'],
                                segmentDict['comments'],
                                        ])
        self.bar.set('All done!')


    def check_before_exit(self):
        ''' Executes on pressing the 'x' button '''

        if not self.data_is_saved:
            ans = askyesno('Data is not saved', 'Save the data before leaving?')
            if ans == 1:
                self.save()
                self.root.quit()
                self.root.destroy()
            else:
                self.root.quit()
                self.root.destroy()
        else:
            self.root.quit()
            self.root.destroy()




if __name__ == '__main__':
    root = tk.Tk()
    x = MainWindow(root)
    root.mainloop()
