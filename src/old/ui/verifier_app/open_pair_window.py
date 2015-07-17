import os
import difflib

from gi.repository import Gtk as gtk
from gi.repository import WebKit as webkit
from parsers.trs_parser import TRSParser
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from utils.backend_utils import BackendUtils
from ui.verifier_app.diff_win import DiffWin

class OpenPairWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Transcription Verifier')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_default_size(270, 210)
        self.window.set_resizable(True)

        vbox = gtk.VBox()
        file1_grid = gtk.Grid()
        file1_frame = gtk.Frame(label='File 1')
        
        file1_name_label = gtk.Label('Transcriber Name:')
        file1_name_entry = gtk.Entry()
        file1_name_entry.set_width_chars(20)
        file1_label = gtk.Label('Path:')
        file1_entry = gtk.Entry()
        file1_entry.set_width_chars(50)
        file1_browse_button = gtk.Button('Browse')
        file1_browse_button.connect('clicked', lambda w: UIUtils.browse_file('Select File 1', file1_entry, [UIUtils.TRS_FILE_FILTER]))
        file1_grid.attach(file1_name_label, 0, 0, 1, 1)
        file1_grid.attach(file1_name_entry, 1, 0, 1, 1)
        file1_grid.attach(file1_label, 0, 1, 1, 1)
        file1_grid.attach(file1_entry, 1, 1, 1, 1)
        file1_grid.attach(file1_browse_button, 2, 1, 1, 1)

        file1_frame.add(file1_grid)
        vbox.pack_start(file1_frame, True, True, 0)

        file2_grid = gtk.Grid()
        file2_frame = gtk.Frame(label='File 2')
        
        file2_name_label = gtk.Label('Transcriber Name:')
        file2_name_entry = gtk.Entry()
        file2_name_entry.set_width_chars(20)
        file2_label = gtk.Label('Path:')
        file2_entry = gtk.Entry()
        file2_entry.set_width_chars(50)
        file2_browse_button = gtk.Button('Browse')
        file2_browse_button.connect('clicked', lambda w: UIUtils.browse_file('Select File 2', file2_entry, [UIUtils.TRS_FILE_FILTER]))
        file2_grid.attach(file2_name_label, 0, 2, 1, 1)
        file2_grid.attach(file2_name_entry, 1, 2, 1, 1)
        file2_grid.attach(file2_label, 0, 3, 1, 1)
        file2_grid.attach(file2_entry, 1, 3, 1, 1)
        file2_grid.attach(file2_browse_button, 2, 3, 1, 1)

        file2_frame.add(file2_grid)
        vbox.pack_start(file2_frame, True, True, 0)

        #for debugging
        #file1_entry.set_text('G:\\Wayne\\baby-lab\\test-data\\trs\\C001b_20090901lFINAL.trs')
        #file2_entry.set_text('G:\\Wayne\\baby-lab\\test-data\\trs\\C001b_20090901lFINAL - Copy.trs')

        file1_name_entry.grab_focus()

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)
        
        ok_button = gtk.Button(stock=gtk.STOCK_OK, label='Ok')
        ok_button.connect('clicked', lambda w: self._check_input(
            file1_entry.get_text(),
            file2_entry.get_text(),
            file1_name_entry.get_text(),
            file2_name_entry.get_text())
        )
        button_box.add(ok_button)

        vbox.pack_start(button_box, True, True, 0)
        
        self.window.add(vbox)
        self.window.show_all()

    def _check_input(self, file1_path, file2_path, file1_name, file2_name):
        if file1_path and file2_path:
            bad_paths = []
            for path in [file1_path, file2_path]:
                if not os.path.exists(path):
                    bad_paths.append(path)
                
            if bad_paths:
                message = 'The following files could not be located.\n'
                for path in bad_paths:
                    message += '\n- %s' % (path)
                message += '\n\nPlease double-check the paths and try again.'
                UIUtils.show_message_dialog(message)
                
            else:
                self._compare(file1_path, file2_path, file1_name, file2_name)
            
        else:
            UIUtils.show_message_dialog('Please select two files.')

    def _compare(self, file1_path, file2_path, file1_name, file2_name):
        self.window.set_sensitive(False)
        paths = [file1_path, file2_path]
        segs = []
        dialog = ProgressDialog('Processing Files...', ['Parsing trs file %d...' % (i + 1) for i in range(len(paths))] + ['Comparing files...', 'Generating output...'])
        dialog.show()
        
        for i in range(len(paths)):
            file_segs = TRSParser(paths[i]).parse(
                progress_update_fcn=dialog.set_fraction,
                validate=False,
                remove_bad_trans_codes=False
            )
            segs.append(file_segs)
            
            dialog.next_phase()

        desc_strs = self._build_desc_strs(segs, dialog)
        dialog.next_phase()

        html = difflib.HtmlDiff().make_file(*desc_strs, fromdesc=file1_name, todesc=file2_name, context=True, numlines=0)
        
        #prevent font selection from killing webkit on Windows systems
        html = html.replace('font-family:Courier;', '')
        DiffWin(html)
        
        dialog.ensure_finish()

        self.window.destroy()

    def _build_desc_strs(self, segs, dialog):
        descs = []

        for i in range(len(segs)):
            file_descs = []
            for seg in segs[i]:
                for utter in seg.utters:
                    file_descs.append(self._build_utter_desc(utter))
                    
                dialog.set_fraction(float(i) / float(len(segs)))
            descs.append(file_descs)

        return descs

    def _build_utter_desc(self, utter):
        desc_str = ''
        
        speaker_cd = '?'
        if utter.speaker:
            if utter.speaker.speaker_codeinfo:
                    speaker_cd = utter.speaker.speaker_codeinfo.get_code()
            else:
                speaker_cd = ' - '

            desc_str = '%s [%s - %s]' % ( speaker_cd, BackendUtils.get_time_str(utter.start), BackendUtils.get_time_str(utter.end))
            if utter.lena_notes:
                desc_str += ' %s' % (utter.lena_notes)
            if utter.trans_phrase:
                desc_str += ' %s' % (utter.trans_phrase)
            if utter.lena_codes:
                desc_str += ' |%s|' % ('|'.join(utter.lena_codes))
            if utter.trans_codes:
                if not utter.lena_codes:
                    desc_str += ' |'
                desc_str += '%s|' % ('|'.join(utter.trans_codes))

            desc_str += '\n'

        return desc_str
