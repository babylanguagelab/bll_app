import Tkinter as tk
import tkFileDialog
from tkMessageBox import showwarning, askyesno, showinfo
import os
import pyaudio
import wave
import re
import cPickle
import csv
import numpy as np
import time

import matplotlib
import matplotlib.style as style
style.use('ggplot')
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure


class MainWindow:

	def __init__(self, master):

		self.root = master
		self.root.protocol('WM_DELETE_WINDOW', self.check_before_exit)
		self.root.bind('<Control-s>', self.submit)

		# self.root.configure(bg = 'white')
		self.root.geometry('750x585')
		self.root.title('Convolabel - beta')

		try:
			with open('ExperimentData.pkl', 'rb') as f:
				self.data = cPickle.load(f)
		except IOError:
			ans = askyesno('Data file', 'Could not find the data file (ExperimentData.pkl). It was either misplaced, or you open the program for the first time. Create a new data file?')
			if ans == 1:
				self.data = {}
			else:
				self.root.quit()
				self.root.destroy()
				return

		self.frame = tk.Frame(root)#, bd = 1, relief = 'sunken')
		self.frame.grid(row = 0, column = 0, sticky = 'wns', padx = (30, 0), pady = 30)

		self.current_subject = ''
		self.current_block_index = ''
		self.current_block_name = ''
		self.block_length = None
		self.time_of_label = ''
		self.audio_data = ''
		self.n_channels = None
		self.sample_width = None
		self.sample_rate = None

		self.menu = tk.Menu(self.root)
		self.root.config(menu = self.menu)
		self.submenu = tk.Menu(self.menu, tearoff = 0)
		self.menu.add_cascade(label = 'Menu', menu = self.submenu)
		self.submenu.add_command(label = 'Set path to the data', command = self.set_data_path)
		self.submenu.add_command(label = 'Save the data', command = self.save)
		self.submenu.add_command(label= 'Export as csv', command = self.export)
		self.submenu.add_command(label = 'Set ADS sample', command = lambda self = self, kind = 'ads': self.set_sample(kind))
		self.submenu.add_command(label = 'Set CDS sample', command = lambda self = self, kind = 'cds': self.set_sample(kind))


		tk.Label(self.frame, text = 'Recordings:').grid(row = 2, column = 0, padx = (0, 50), pady = 0, sticky = 'W')
		self.subjects_list = tk.Listbox(self.frame, width = 20, height = 15, exportselection = False, relief = tk.FLAT)
		self.subjects_list.bind('<<ListboxSelect>>', self.update_current_subject)
		# self.root.bind('<Right>', self.subjects_list.focus_set())
		self.subjects_list.grid(row = 3, column = 0, rowspan = 10, padx = 0, pady = 0, sticky = 'W')

		tk.Label(self.frame, text = 'Blocks:').grid(row = 2, column = 1, padx = 0, pady = 0, sticky = 'W')
		self.blocks_list = tk.Listbox(self.frame, width = 20, height = 15, exportselection = False, relief = tk.FLAT)
		self.blocks_list.bind('<<ListboxSelect>>', self.update_current_block)
		self.blocks_list.bind('<space>', self.play)
		self.blocks_list.grid(row = 3, column = 1, rowspan = 10, padx = 0, pady = 0, sticky = 'W')

		self.coder_name = tk.StringVar()
		self.coder_name.set('--> Coder\'s name <--')
		self.coder_name_entry = tk.Entry(self.frame, textvariable = self.coder_name, justify = tk.CENTER, relief = tk.FLAT)
		self.coder_name_entry.grid(row = 0, column = 0, padx = 0, pady = 0)

		self.subject = tk.StringVar()
		self.subject_label = tk.Label(self.frame, textvariable = self.subject)
		self.subject_label.grid(row = 1, column = 0, padx = 0, pady = 5, sticky = 'WNS')

		self.load_data_button = tk.Button(self.frame,
										text = 'Load',
										command = self.load_subjects,
										height = 1,
										width = 10,
										relief = tk.GROOVE).grid(row = 4, column = 2, padx = 20)

		self.play_button = tk.Button(self.frame,
										text = 'Play',
										command = self.play,
										height = 1,
										width = 10,
										relief = tk.GROOVE)
		self.play_button.bind('<Enter>', self.show_block_length)
		self.play_button.bind('<Leave>', lambda event, self = self: self.play_button.configure(text = 'Play'))
		self.play_button.grid(row = 5, column = 2, padx = 20)

		self.submit_button = tk.Button(self.frame,
										text = 'Submit',
										command = self.submit,
										height = 1,
										width = 10,
										relief = tk.GROOVE).grid(row = 6, column = 2, padx = 20)

		self.ads_sample_button = tk.Button(self.frame,
										text= 'ADS sample',
										command = lambda self = self, kind = 'ads': self.play_sample(kind),
										height = 1,
										width = 10,
										relief = tk.GROOVE,
										state = 'disabled')
		self.ads_sample_button.grid(row = 10, column = 2, padx = 20)

		self.cds_sample_button = tk.Button(self.frame,
										text = 'CDS sample',
										command = lambda self = self, kind = 'cds': self.play_sample(kind),
										height = 1,
										width = 10,
										relief = tk.GROOVE,
										state = 'disabled')
		self.cds_sample_button.grid(row = 11, column = 2, padx = 20)


		# self.export_button = tk.Button(self.frame,
		# 								text= 'Export',
		# 								command = self.export,
		# 								height = 1,
		# 								width = 10,
		# 								relief = tk.GROOVE).grid(row = 10, column = 2, padx = 20)

		# self.save_and_exit_button = tk.Button(self.frame,
		# 								text = 'Save and Exit',
		# 								command = self.save_and_exit,
		# 								height = 1,
		# 								width = 10,
		# 								relief = tk.GROOVE).grid(row = 11, column = 2, padx = 20)


################################### Labels ###########################################


		self.labels = {
			'ads': tk.IntVar(),
			'cds': tk.IntVar(),
			'ocs': tk.IntVar(),
			'sensitive': tk.IntVar(),
			'other_langue': tk.IntVar(),
			'mother': tk.IntVar(),
			'other_fem': tk.IntVar(),
			'male': tk.IntVar(),
			'unsure': tk.IntVar(),
			'target_child': tk.IntVar(),
			'other_child': tk.IntVar(),
			'directive': tk.IntVar(),
			'nondirective': tk.IntVar()
		}
		self.junk = tk.IntVar()


		entry_params = {'width': 3, 'state': 'disabled', 'justify': 'center', 'relief': 'flat'} #, 'validate': 'key', 'validatecommand': vcommand, 'state': 'disabled'}
		entry_grid_params = {'sticky': tk.E, 'padx': (2, 20), 'pady': 3}
		label_grid_params = {'sticky': tk.E, 'padx': 0, 'pady': 2}


		self.labels_frame = tk.Frame(self.root)#, bd = 1, relief = 'sunken')
		self.labels_frame.grid(row = 1, column = 0, padx = 30, columnspan = 2, sticky = tk.W)# columnspan = 20, sticky = tk.W, padx = 10, pady = 20)

		# Adult-directed speech
		ads_label = tk.Label(self.labels_frame, text = 'Adult-directed speech:').grid(label_grid_params, row = 0, column = 0)

		self.ads_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['ads'])
		self.ads_entry.grid(entry_grid_params, row = 0, column = 1)

		# Child-directed speech
		cds_label = tk.Label(self.labels_frame, text = 'Child-directed speech:').grid(label_grid_params, row = 1, column = 0)
		self.cds_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['cds'])
		self.cds_entry.grid(entry_grid_params, row = 1, column = 1)

		# Other child speech
		ocs_label = tk.Label(self.labels_frame, text = 'Other child speech:').grid(label_grid_params, row = 2, column = 0)
		self.ocs_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['ocs'])
		self.ocs_entry.grid(entry_grid_params, row = 2, column = 1)

		# Junk checkbutton
		self.junk_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Junk', variable = self.junk, command = self.junk_selected, state = 'disabled')
		self.junk_checkbutton.grid(row = 3, column = 0, sticky = tk.W, padx = (2, 10), pady = (3, 1))

		# Sesitive checkbutton
		self.sensitive_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Sensitive', variable = self.labels['sensitive'], state = 'disabled')
		self.sensitive_checkbutton.grid(row = 4, column = 0, sticky = tk.W, padx = (2, 10), pady = (0, 0))

		# Other language checkbutton
		self.other_langue_checkbutton = tk.Checkbutton(self.labels_frame, text = 'Not English', variable = self.labels['other_langue'], state = 'disabled')
		self.other_langue_checkbutton.grid(row = 5, column = 0, sticky = tk.W, padx = (2, 10), pady = (1, 0))

		# Mother
		mother_label = tk.Label(self.labels_frame, text = 'Mother:').grid(label_grid_params, row = 0, column = 2)
		self.mother_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['mother'])
		self.mother_entry.grid(entry_grid_params, row = 0, column = 3)

		# Other females
		other_fem_label = tk.Label(self.labels_frame, text = 'Other female(s):').grid(label_grid_params, row = 1, column = 2)
		self.other_fem_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['other_fem'])
		self.other_fem_entry.grid(entry_grid_params, row = 1, column = 3)

		# Males
		male_label = tk.Label(self.labels_frame, text = 'Male(s):').grid(label_grid_params, row = 2, column = 2)
		self.male_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['male'])
		self.male_entry.grid(entry_grid_params, row = 2, column = 3)

		# Unsure
		unsure_label = tk.Label(self.labels_frame, text = 'Unsure:').grid(label_grid_params, row = 3, column = 2)
		self.unsure_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['unsure'])
		self.unsure_entry.grid(entry_grid_params, row = 3, column = 3)

		# Target child
		target_child_label = tk.Label(self.labels_frame, text = 'At target child:').grid(label_grid_params, row = 0, column = 4)
		self.target_child_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['target_child'])
		self.target_child_entry.grid(entry_grid_params, row = 0, column = 5)

		# Other child
		other_child_label = tk.Label(self.labels_frame, text = 'At other child:').grid(label_grid_params, row = 1, column = 4)
		self.other_child_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['other_child'])
		self.other_child_entry.grid(entry_grid_params, row = 1, column = 5)

		# Directive
		directive_label = tk.Label(self.labels_frame, text = 'Directive:').grid(label_grid_params, row = 0, column = 6)
		self.directive_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['directive'])
		self.directive_entry.grid(entry_grid_params, row = 0, column = 7)

		# Nondirective
		nondirective_label = tk.Label(self.labels_frame, text = 'Nondirective:').grid(label_grid_params, row = 1, column = 6)
		self.nondirective_entry = tk.Entry(self.labels_frame, entry_params, textvariable = self.labels['nondirective'])
		self.nondirective_entry.grid(entry_grid_params, row = 1, column = 7)


		# trace command passes three arguments (x, y, z) to the labmda function. Lambda calls self.check_entry and passes specific label and entry handles.
		self.labels['ads'].trace('w', lambda x, y, z, label=self.labels['ads'], entry=self.ads_entry: self.check_entry(label, entry))
		self.labels['cds'].trace('w', self.check_cds)
		self.labels['ocs'].trace('w', lambda x, y, z, label=self.labels['ocs'], entry=self.ocs_entry: self.check_entry(label, entry))
		self.labels['mother'].trace('w', self.check_mother)
		self.labels['other_fem'].trace('w', lambda x, y, z, label=self.labels['other_fem'], entry=self.other_fem_entry: self.check_entry(label, entry))
		self.labels['male'].trace('w', lambda x, y, z, label=self.labels['male'], entry=self.male_entry: self.check_entry(label, entry))
		self.labels['unsure'].trace('w', lambda x, y, z, label=self.labels['unsure'], entry=self.unsure_entry: self.check_entry(label, entry))
		self.labels['target_child'].trace('w', self.check_target_child)
		self.labels['other_child'].trace('w', lambda x, y, z, label=self.labels['other_child'], entry=self.other_child_entry: self.check_entry(label, entry))
		self.labels['directive'].trace('w', lambda x, y, z, label=self.labels['directive'], entry=self.directive_entry: self.check_entry(label, entry))
		self.labels['nondirective'].trace('w', lambda x, y, z, label=self.labels['nondirective'], entry=self.nondirective_entry: self.check_entry(label, entry))

		self.entries_handles = filter(lambda x: isinstance(x, tk.Entry), self.labels_frame.children.itervalues())

		self.comments = tk.Text(self.labels_frame, height = 10, width = 15, state = 'disabled', relief = tk.FLAT)
		self.comments.grid(row = 0, column = 8, rowspan = 6, padx = 0, pady = 0)

		self.status_bar_frame = tk.Frame(self.root)
		self.status_bar_frame.grid(row = 2, column = 0, sticky = 'we', padx = 20, pady = (10, 0))
		self.bar = tk.StringVar()
		self.status_bar = tk.Label(self.status_bar_frame, textvariable = self.bar)
		self.status_bar.grid(row = 0, column = 0)


		self.graph_frame = tk.Frame(self.root)#, bd = 1, relief = 'sunken')
		self.graph_frame.grid(row = 0, column = 1, sticky = 'wns', pady = 30)

		self.fig = Figure(figsize = (5, 5), dpi = 60)
		self.ax = self.fig.add_subplot(111)
		# self.ax1 = self.fig.add_subplot(212, sharex = self.ax)
		# self.ax.get_yaxis().set_visible(False)
		# self.ax1.get_yaxis().set_visible(False)
		self.fig.patch.set_visible(False)
		# self.fig.tight_layout()
		self.ax.set_xlabel('Time (s)')
		self.ax.set_ylabel('Amplitude')
		# self.ax1.set_ylabel('Frequency')
		# self.fig.subplots_adjust(left = 0.11, bottom = 0.09, right = 0.98, top = 0.98, wspace = 0, hspace = 0.2)

		# self.ax.set_yticklabels(self.ax.yaxis.get_majorticklabels(), rotation=45)

		self.canvas = FigureCanvasTkAgg(self.fig, master = self.graph_frame)
		self.canvas.get_tk_widget().grid(row = 1, column = 0)


	def show_block_length(self, event):
		if self.block_length != None:
			self.play_button.configure(text = '%.2f s' % self.block_length)


	def set_sample(self, kind):
		if self.current_subject == '':
			showwarning('No recording selected', 'Select a recording from the list first. The sample will be attached to that recording')
			return
		file = tkFileDialog.askopenfilename(filetypes = [('wave files', '.wav')])
		if file == '':
			return
		file = os.path.abspath(file)
		coder = self.coder_name.get()
		subject = self.current_subject

		if kind == 'ads':
			self.data[coder][subject]['_ads_sample'] = file
		elif kind == 'cds':
			self.data[coder][subject]['_cds_sample'] = file


	def play_sample(self, kind):

		coder = self.coder_name.get()
		subject = self.current_subject

		if kind == 'ads':
			f = wave.open(self.data[coder][subject]['_ads_sample'])
		elif kind == 'cds':
			f = wave.open(self.data[coder][subject]['_cds_sample'])

		audio = f.readframes(-1)
		n_channels, sample_width, sample_rate, _, _, _ = f.getparams()
		f.close()

		p = pyaudio.PyAudio()
		stream = p.open(format = p.get_format_from_width(sample_width),
			channels= n_channels,
			rate = sample_rate,
			output = True)

		stream.write(audio)
		stream.stop_stream()
		stream.close()
		p.terminate()


	def check_entry(self, label, entry):
		try:
			if label.get() in range(0, 101):
				entry.configure(background = 'white')
			else:
				entry.configure(background = '#FFA9A5')
		except ValueError:
			entry.configure(background = '#FFA9A5')


	def check_cds(self, *args):
		try:
			if self.labels['cds'].get() in range(0, 101):
				self.cds_entry.configure(background = 'white')
			else:
				self.cds_entry.configure(background = '#FFA9A5')

			if self.labels['cds'].get() in range(1, 101):
				self.mother_entry.configure(state = 'normal')
				self.other_fem_entry.configure(state = 'normal')
				self.male_entry.configure(state = 'normal')
				self.unsure_entry.configure(state = 'normal')
			else:
				self.mother_entry.configure(state = 'disabled')
				self.other_fem_entry.configure(state = 'disabled')
				self.male_entry.configure(state = 'disabled')
				self.unsure_entry.configure(state = 'disabled')

		except ValueError:
			self.cds_entry.configure(background = '#FFA9A5')



	def check_mother(self, *args):
		try:
			if self.labels['mother'].get() in range(0, 101):
				self.mother_entry.configure(background = 'white')
			else:
				self.mother_entry.configure(background = '#FFA9A5')

			if self.labels['mother'].get() in range(1, 101):
				self.target_child_entry.configure(state = 'normal')
				self.other_child_entry.configure(state = 'normal')
			else:
				self.target_child_entry.configure(state = 'disabled')
				self.other_child_entry.configure(state = 'disabled')

		except ValueError:
			self.mother_entry.configure(background = '#FFA9A5')

	def check_target_child(self, *args):
		try:
			if self.labels['target_child'].get() in range(0, 101):
				self.target_child_entry.configure(background = 'white')
			else:
				self.target_child_entry.configure(background = '#FFA9A5')

			if self.labels['target_child'].get() in range(1, 101):
				self.directive_entry.configure(state = 'normal')
				self.nondirective_entry.configure(state = 'normal')
			else:
				self.directive_entry.configure(state = 'disabled')
				self.nondirective_entry.configure(state = 'disabled')

		except ValueError:
			self.target_child_entry.configure(background = '#FFA9A5')

	def junk_selected(self):
		if self.junk.get() == 1:
			self.entry_initial_state()
		else:
			self.entry_initial_state()
			self.ads_entry.configure(state = 'normal')
			self.cds_entry.configure(state = 'normal')
			self.ocs_entry.configure(state = 'normal')
			self.junk_checkbutton.configure(state = 'normal')


	def set_data_path(self):

		coder = self.coder_name.get()
		if coder == '--> Coder\'s name <--':
			showwarning('Coder\'s name', 'Please enter your name')
			return

		path = tkFileDialog.askdirectory(title = 'Choose the data folder')
		if path == '':
			return
		path = os.path.abspath(path)
		self.data[coder]['_path_to_data'] = path



	def load_subjects(self):

		coder = self.coder_name.get()

		if coder == '--> Coder\'s name <--':
			showwarning('Coder\'s name', 'Please enter your name')
			return
		elif coder not in self.data.keys():
			ans = askyesno('Coder\'s name', 'Didn\'t recognise the coder\'s name. Create new?')
			if ans == 1:
				self.data[coder] = {'_path_to_data': ''}
			else:
				return

		if self.subjects_list.get(0, tk.END) != ():
			self.subjects_list.delete(0, tk.END)
		if self.blocks_list.get(0, tk.END) != ():
			self.blocks_list.delete(0, tk.END)


		if self.data[coder]['_path_to_data'] != '' and os.path.isdir(self.data[coder]['_path_to_data']):
			self.data_path = self.data[coder]['_path_to_data']

		else:
			self.data_path = tkFileDialog.askdirectory(title = 'Choose the data folder')
			if self.data_path == '':
				return
			self.data_path = os.path.abspath(self.data_path)

		subjects_names = []
		for name in os.listdir(self.data_path):
			if os.path.isdir(os.path.join(self.data_path, name)):
				subjects_names.append(name)

		for name in subjects_names:
			self.subjects_list.insert(tk.END, name)


	def update_current_subject(self, event):

		coder = self.coder_name.get()
		if self.subjects_list.get(0, tk.END) == (): # this is to prevent an error which pops up if user clicks on an empty list
			return

		w = event.widget
		self.current_subject = w.get(int(w.curselection()[0]))

		if self.current_subject not in self.data[coder].keys():
			self.data[coder][self.current_subject] = {'_ads_sample': '', '_cds_sample': ''}

		self.current_block_index = ''
		self.current_block_name = ''
		self.block_length = None
		self.time_of_label = ''
		self.audio_data = ''
		self.n_channels = None
		self.sample_width = None
		self.sample_rate = None

		self.ax.clear()
		# self.ax1.clear()
		self.canvas.show()

		self.entry_initial_state()
		self.junk.set(0)
		self.junk_checkbutton.configure(state = 'disabled')
		self.junk_checkbutton.configure(state = 'disabled')
		self.sensitive_checkbutton.configure(state = 'disabled')
		self.other_langue_checkbutton.configure(state = 'disabled')
		self.comments.delete(1.0, tk.END)
		self.comments.configure(state = 'disabled')

		if self.data[coder][self.current_subject]['_ads_sample'] != '':
			self.ads_sample_button.configure(state = 'normal')
		else:
			self.ads_sample_button.configure(state = 'disabled')

		if self.data[coder][self.current_subject]['_cds_sample'] != '':
			self.cds_sample_button.configure(state = 'normal')
		else:
			self.cds_sample_button.configure(state = 'disabled')


		if self.blocks_list.get(0, tk.END) != (): # if there are some blocks in the listbox, delete them
			self.blocks_list.delete(0, tk.END)


		path = os.path.abspath(os.path.join(self.data_path, self.current_subject)) # path to the folder containing blocks for the selected subject
		names = []
		for name in os.listdir(path):
			if os.path.isdir(os.path.join(path, name)): # creates paths to the individual block names
				names.append(name)

		try:
			# names_sorted = sorted(names, key = int) # if the block names are numeric, sort in ascending order
			names_split = [ re.match(r'(\D*)(\d+)', name).groups() for name in names ] # if the blocks are like 'block_1', this will result in ('block_', '1')
			names_split_sorted = sorted(names_split, key = lambda tupl: int(tupl[1])) # this will sort the tuples in ascending order
			names_sorted = [name[0] + name[1] for name in names_split_sorted] # this will join the strings in tuples back together
		except:
			names_sorted = sorted(names, key = str) # if all else fails, sort alphabetically

		for name in names_sorted:
			self.blocks_list.insert(tk.END, name)
			if name in self.data[coder][self.current_subject].keys():
				self.blocks_list.itemconfig(tk.END, foreground = 'gray')


		labelled = len([x for x in self.data[coder][self.current_subject].keys() if not x.startswith('_')])
		total = len(names)
		self.bar.set('{}% of blocks are labelled for this recording'.format(100 * labelled / total))



	def update_current_block(self, event):

		self.bar.set('')

		if self.blocks_list.get(0, tk.END) == (): # this is to prevent an error which pops up if user clicks on an empty blocks list
			return

		w = event.widget
		self.current_block_index = int(w.curselection()[0])
		self.current_block_name = w.get(self.current_block_index)

		coder = self.coder_name.get()
		subject = self.current_subject
		block = self.current_block_name

		if block in self.data[coder][subject].keys(): # if the blocks was already labelled, load the labels

			for label in self.labels.keys():
				self.labels[label].set(self.data[coder][subject][block][label])
			self.junk.set(self.data[coder][subject][block]['junk'])
			self.ads_entry.configure(state = 'normal')
			self.cds_entry.configure(state = 'normal')
			self.ocs_entry.configure(state = 'normal')
			self.junk_checkbutton.configure(state = 'normal')
			self.sensitive_checkbutton.configure(state = 'normal')
			self.other_langue_checkbutton.configure(state = 'normal')
			self.comments.configure(state = 'normal')
			self.comments.delete(1.0, tk.END)
			self.comments.insert(tk.END, self.data[coder][subject][block]['comments'])

			if self.junk.get() == 1:
				self.entry_initial_state()

			self.bar.set('Labeled at {}'.format(self.data[coder][subject][block]['time']))

		else:

			self.entry_initial_state() # if the block was not previously labelled, reset the entries
			self.junk.set(0)
			self.comments.configure(state = 'normal')
			self.comments.delete(1.0, tk.END)

			self.ads_entry.configure(state = 'normal')
			self.cds_entry.configure(state = 'normal')
			self.ocs_entry.configure(state = 'normal')
			self.junk_checkbutton.configure(state = 'normal')
			self.sensitive_checkbutton.configure(state = 'normal')
			self.other_langue_checkbutton.configure(state = 'normal')

		clips_path = os.path.abspath(os.path.join(self.data_path, self.current_subject, self.current_block_name))
		clips_names = [ os.path.join(clips_path, name) for name in os.listdir(clips_path) if name.endswith('.wav') ]

		self.audio_data = ''
		for name in clips_names:
			f = wave.open(name, 'rb')
			self.audio_data += f.readframes(-1)
			if name == clips_names[0]: # get the parameters from the first clip
				self.n_channels, self.sample_width, self.sample_rate, _, _, _ = f.getparams()
			f.close()

		dtype = 'Int{}'.format(self.sample_width * 8) # convert bytes to bits: 1 byte = 8 bits
		if self.n_channels == 1:
			data = np.fromstring(self.audio_data, dtype)
		elif self.n_channels == 2:
			data = np.fromstring(self.audio_data, dtype)[0::2] # get every second value just for one channel
		else:
			self.bar.set('Unable to show the graph :(')
			return

		self.block_length = len(data) / float(self.sample_rate)
		times = np.arange(0, self.block_length, self.block_length / float(len(data)))

		self.ax.clear()
		# self.ax1.clear()
		try:
			self.ax.plot(times, data, color = [0.2, 0.2, 0.2])
			# self.ax1.specgram(data, Fs = self.sample_rate, mode = 'psd', scale = 'dB', cmap = 'inferno')
		except:
			self.bar.set('Unable to show the graph :(')
		self.canvas.show()

	def entry_initial_state(self):

		for entry in self.entries_handles:
			entry.configure(state = 'disabled')
		for label in self.labels.values():
			label.set(0)
		if self.junk.get() == 0:
			self.junk_checkbutton.configure(state = 'disabled')
		else:
			self.junk_checkbutton.configure(state = 'normal')


	def play(self, *event):

		if self.current_block_name == '':
			showwarning('Block error','Choose the block')
			return

		p = pyaudio.PyAudio()
		stream = p.open(format = p.get_format_from_width(self.sample_width),
	                    channels = self.n_channels,
	                    rate = self.sample_rate,
	                    output = True)

		stream.write(self.audio_data)
		stream.stop_stream()
		stream.close()
		p.terminate()


	def submit(self, *event):

		if self.current_block_name == '':
			showwarning('Block error','Choose the block')
			return

		try:
			for label in self.labels.values():
				if label.get() not in range(0, 101):
					showwarning('Labels', 'Check the labels')
					return
		except ValueError:
			showwarning('Labels', 'Check the labels')
			return


		if self.labels['cds'].get() != 0 and \
			self.labels['mother'].get() + self.labels['other_fem'].get() + \
			self.labels['male'].get() + self.labels['unsure'].get() != 100:

			showwarning('Percentages', 'Percentages in the second column don\'t add up to 100')
			return

		elif self.labels['mother'].get() != 0 and \
			self.labels['target_child'].get() + self.labels['other_child'].get() != 100:

			showwarning('Percentages', 'Percentages in the third column don\'t add up to 100')
			return


		elif self.labels['target_child'].get() != 0 and \
			self.labels['directive'].get() + self.labels['nondirective'].get() != 100:

			showwarning('Percentages', 'Percentages in the fourth column don\'t add up to 100')
			return

		coder = self.coder_name.get()
		subject = self.current_subject
		block = self.current_block_name

		self.data[coder][subject][block] = {}
		for label in self.labels.keys():
			self.data[coder][subject][block][label] = self.labels[label].get()
		self.data[coder][subject][block]['junk'] = self.junk.get()
		self.data[coder][subject][block]['time'] = time.strftime('%H:%M, %d %B %Y') # this is the time at which the block was labelled
		self.data[coder][subject][block]['length'] = self.block_length
		self.data[coder][subject][block]['comments'] = self.comments.get(1.0, tk.END).strip() # the .strip() removes a new line that tkinter inserts by default

		self.bar.set('Labels submitted!')
		self.blocks_list.itemconfig(self.current_block_index, foreground = 'gray')
		self.blocks_list.focus_set()

	def save(self):

		with open('ExperimentData.pkl', 'wb') as f:
			cPickle.dump(self.data, f, cPickle.HIGHEST_PROTOCOL)


	# def save_and_exit(self):

	# 	with open('ExperimentData.pkl', 'wb') as f:
	# 		cPickle.dump(self.data, f, cPickle.HIGHEST_PROTOCOL)
	# 	self.root.quit()
	# 	self.root.destroy()

	def export(self):

		output = tkFileDialog.asksaveasfilename(filetypes = [('Comma-separated file', '.csv')], initialfile = 'data.csv' )
		if output == '':
			return

		with open(output, 'wb') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(['Date coded', 'Coder', 'Recording', 'Block', 'Block length (s)', 'Junk', 'Sensitive',
							'Other language', 'Adult-directed speech', 'Child-directed speech', 'Other child speech',
							'Mother', 'Other female(s)', 'Male(s)', 'Unsure', 'Directed at target child',
							'Directed at other child', 'Directive', 'Nondirective', 'Comments'])
			for coder in self.data.keys():
				for subject in self.data[coder].keys():
					if subject.startswith('_'): continue # skip the path to data fieldS
					for block in self.data[coder][subject].keys():
						if block.startswith('_'): continue # skip the sample clips
						writer.writerow([
										self.data[coder][subject][block]['time'],
										coder,
										subject,
										block,
										self.data[coder][subject][block]['length'],
										self.data[coder][subject][block]['junk'],
										self.data[coder][subject][block]['sensitive'],
										self.data[coder][subject][block]['other_langue'],
										self.data[coder][subject][block]['ads'],
										self.data[coder][subject][block]['cds'],
										self.data[coder][subject][block]['ocs'],
										self.data[coder][subject][block]['mother'],
										self.data[coder][subject][block]['other_fem'],
										self.data[coder][subject][block]['male'],
										self.data[coder][subject][block]['unsure'],
										self.data[coder][subject][block]['target_child'],
										self.data[coder][subject][block]['other_child'],
										self.data[coder][subject][block]['directive'],
										self.data[coder][subject][block]['nondirective'],
										self.data[coder][subject][block]['comments'],
										])
		self.bar.set('All done!')


	def check_before_exit(self):

		ans = askyesno('Data might be lost', 'Save the data before leaving?')
		if ans == 1:
			self.save()
			self.root.quit()
			self.root.destroy()
		else:
			self.root.quit()
			self.root.destroy()




if __name__ == '__main__':
	root = tk.Tk()
	x = MainWindow(root)
	root.mainloop()
