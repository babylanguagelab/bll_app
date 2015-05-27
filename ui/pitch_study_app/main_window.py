from gi.repository import Gtk as gtk
from ui.pitch_study_app.batch_sel_win import BatchSelectionWindow
from ui.pitch_study_app.options_window import OptionsWindow
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
import parsers.pitch_study_exporter as pitch_exporter
from db.bll_database import BLLDatabase
from data_structs.pitch_study_props import PitchStudyProps
import traceback

class MainWindow():
    def __init__(self):
        self.bll_db = BLLDatabase()
        self.props = PitchStudyProps.db_select(self.bll_db)[0]
        self.bll_db.close()
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Pitch Study')
        self.window.connect('destroy', lambda x: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 100)
                                         
        box = gtk.VBox(False, 5)
        create_button = UIUtils.create_button('Run Batch', UIUtils.BUTTON_ICONS.RUN)
        create_button.connect('clicked', lambda widget, data=None: BatchSelectionWindow(self.props.clips_db_path))
        box.pack_start(create_button, False, False, 0)

        export_button = UIUtils.create_button('Export Results', UIUtils.BUTTON_ICONS.EXPORT)
        export_button.connect('clicked', lambda widget, data=None: self._export_results())
        box.pack_start(export_button, False, False, 0)

        options_button = UIUtils.create_button('Options', UIUtils.BUTTON_ICONS.RUN)
        options_button.connect('clicked', lambda widget, data=None: OptionsWindow())
        box.pack_start(options_button, False, False, 0)

        exit_button = UIUtils.create_button('Exit', UIUtils.BUTTON_ICONS.EXIT)
        exit_button.connect('clicked', lambda widget: gtk.main_quit())
        box.pack_start(exit_button, False, False, 0)

        self.window.add(box)
        self.window.show_all()

    def _export_results(self):
        folder = UIUtils.open_folder()
        if folder is not None and not folder.endswith('\\') and not folder.endswith('/'):
            folder += '/'
        
        if folder != None:
            progress = ProgressDialog(title='Exporting Data...')
            progress.show()
            try:
                pitch_exporter.export_data(self.props.clips_db_path, folder, progress.set_fraction)
                progress.ensure_finish()
                UIUtils.show_message_dialog('Data exported successfully.')
                
            except Exception as err:
                print err
                print traceback.format_exc()
                
                progress.ensure_finish()
                UIUtils.show_message_dialog('There was an error exporting the data.\nPlease make sure the folders are not open in a Windows Explorer window.', dialog_type=gtk.MessageType.WARNING)
                

    
