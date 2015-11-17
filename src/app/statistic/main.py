#!/usr/bin/python2
from gi.repository import Gtk
from gi.repository import GObject
import glob
import os


class main():
    def __init__(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_title('Statistics Application')
        self.window.set_border_width(10)
        self.window.set_default_size(600, 450)
        self.window.connect('destroy', lambda x: Gtk.main_quit())

        vbox = Gtk.VBox()

        treeview = self.build_treeview()
        scrolled_win = Gtk.ScrolledWindow()
        scrolled_win.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_win.add(treeview)
        vbox.pack_start(scrolled_win, True, True, 0)

        button_box = Gtk.HButtonBox()
        button_box.set_layout(Gtk.ButtonBoxStyle.EDGE)

        create_button = Gtk.Button('Create Configuration')
        # create_button.connect('clicked',
        #                       lambda w: ConfigWindow(lambda new_config:
        #                                              self._add_callback(
        #                                                  treeview.get_model(),
        #                                                  new_config)))
        button_box.pack_start(create_button, True, True, 0)

        run_button = Gtk.Button('Run Configuration')
        # run_button.connect('clicked', lambda w: self._run_config(treeview))
        button_box.pack_start(run_button, True, True, 0)

        delete_button = Gtk.Button('Delete')
        # delete_button.connect('clicked', lambda w: self._delete_config(treeview))
        button_box.pack_start(delete_button, True, True, 0)

        exit_button = Gtk.Button('Exit')
        exit_button.connect('clicked', lambda w: Gtk.main_quit())
        button_box.pack_start(exit_button, True, True, 0)

        vbox.pack_end(button_box, False, False, 0)
        self.window.add(vbox)

    def _add_callback(self, model, new_config):
        model.append([new_config.name,
                      new_config.desc,
                      UIUtils.get_db_timestamp_str(new_config.created) if new_config.created else '-',
                      self._get_output_names_str(new_config.outputs),
                      new_config,
                      ])

    def _edit_config(self, treeview):
        model, it = treeview.get_selection().get_selected()
        if it:
            config = model.get(it, 4)[0]
            ConfigWindow(lambda edited_config: self._edit_callback(treeview.get_model(), edited_config, it), config)

        else:
            UIUtils.show_message_dialog('Please select a row.', Gtk.MessageTYpe.WARNING)

    def _edit_callback(self, model, edited_config, row_it):
        model.set_value(row_it, 0, edited_config.name)
        model.set_value(row_it, 1, edited_config.desc)
        model.set_value(row_it, 2, UIUtils.get_db_timestamp_str(edited_config.created) if edited_config.created else '-')
        model.set_value(row_it, 3, self._get_output_names_str(edited_config.outputs))
        model.set_value(row_it, 4, edited_config)

    def _get_output_names_str(self, outputs):
        output_names = ''
        i = 0
        while i < len(outputs):
            output_names += outputs[i].name
            if i < len(outputs) - 1:
                output_names += ',\n'
            i += 1

        if not output_names:
            output_names = '-'

        return output_names

    def build_list_store(self):
        list_store = Gtk.ListStore(
            str,  # name
            str,  # description
            str,  # created timestamp
            str,  # output names
            GObject.TYPE_PYOBJECT,  # hidden object
            )

        # db = BLLDatabase()
        # configs = OutputConfig.db_select(db)
        # for cur_config in configs:
        #     output_names = self._get_output_names_str(cur_config.outputs)
        #     created_str = UIUtils.get_db_timestamp_str(cur_config.created) if cur_config.created else '-'

        #     list_store.append([
        #             cur_config.name,
        #             cur_config.desc,
        #             created_str,
        #             output_names,
        #             cur_config,
        #             ])

        # db.close()

        return list_store

    def build_treeview(self):
        list_store = self.build_list_store()
        treeview = Gtk.TreeView(list_store)

        col_names = ['Name', 'Description', 'Created', 'Outputs']
        for i in range(len(col_names)):
            col = Gtk.TreeViewColumn(col_names[i],
                                     Gtk.CellRendererText(),
                                     text=(i))
            col.set_resizable(True)
            col.set_min_width(90 + (len(col_names[i]) / 15) * 50)
            treeview.append_column(col)

        return treeview

    def _delete_config(self, treeview):
        model, it = treeview.get_selection().get_selected()
        if it:
            if UIUtils.show_confirm_dialog('Are you sure you want to delete this configuration?'):
                config = model.get(it, 4)[0]

                model.remove(it)

                if config.db_id != None:
                    db = BLLDatabase()
                    config.db_delete(db)
                    db.close()
        else:
            UIUtils.show_no_sel_dialog()

    # def _run_config(self, treeview):
    #     model, it = treeview.get_selection().get_selected()
    #     if it:
    #         config = model.get(it, 4)[0]
    #         trs_filename = UIUtils.open_file(
    #             title='Select TRS File...',
    #             filters=[UIUtils.TRS_FILE_FILTER,
    #                      UIUtils.ALL_FILE_FILTER,
    #                      ])

    #         if trs_filename: #will be None if user clicked 'cancel' or closed the dialog window
    #             export_filename, open_now = UIUtils.save_file(
    #                 title='Export to...',
    #                 filters=[UIUtils.CSV_FILE_FILTER,
    #                          UIUtils.ALL_FILE_FILTER,
    #                          ],
    #                 open_now_opt=True)

    #             if export_filename:
    #                 exporter = StatsExporter(config, trs_filename, export_filename)

    #                 progress_phases = ['Parsing TRS File...']
    #                 i = 0
    #                 while i < len(config.outputs):
    #                     progress_phases.append('Processing output #%d' % (i + 1))
    #                     i += 1

    #                 progress_dialog = ProgressDialog('Working...', progress_phases)
    #                 progress_dialog.show()
    #                 exporter.export(progress_update_fcn=progress_dialog.set_fraction,
    #                                 progress_next_phase_fcn=progress_dialog.next_phase)
    #                 progress_dialog.ensure_finish()

    #                 if open_now:
    #                     subprocess.Popen(['%s' % DBConstants.SETTINGS.SPREADSHEET_PATH, export_filename])
    #                 else:
    #                     UIUtils.show_message_dialog('Export successful.')

    #     else:
    #         UIUtils.show_no_sel_dialog()

    def _run_config(self, treeview):
        model, it = treeview.get_selection().get_selected()
        if it:
            config = model.get(it, 4)[0]
            trs_folder = UIUtils.open_folder(
                title='Select TRS Folder...'
                )

            if trs_folder: #will be None if user clicked 'cancel' or closed the dialog window
                export_folder = UIUtils.open_folder(
                    title='Select Output Folder...'
                    )
                if export_folder:
                    #trs_filenames = glob.glob(trs_folder + '\\*.trs')
                    trs_filenames = self._get_trs_filenames(trs_folder)
                    export_filenames = map(lambda name: '%s\\%s-stats.csv' % (export_folder, os.path.basename(name)[:-4]), trs_filenames)

                    phases = ['File %d of %d' % (i + 1, len(trs_filenames)) for i in range(len(trs_filenames))]
                    dialog = ProgressDialog('Working...', phases)
                    dialog.show()

                    for j in range(len(trs_filenames)):
                        exporter = StatsExporter(config, trs_filenames[j], export_filenames[j])
                        exporter.export()
                        dialog.set_fraction(1.0)
                        if j < len(trs_filenames) - 1:
                            dialog.next_phase()

                    dialog.ensure_finish()

                    UIUtils.show_message_dialog('Export successful.')

        else:
            UIUtils.show_no_sel_dialog()

    def _get_trs_filenames(self, root_dir):
        out_filenames = []
        # in_filenames = glob.glob(root_dir + '\\*')
        in_filenames = glob.glob(root_dir + '/*')

        for cur_name in in_filenames:
            if os.path.isdir(cur_name):
                out_filenames.extend(self._get_trs_filenames(cur_name))
            elif os.path.isfile(cur_name) and cur_name.lower().endswith('.trs'):
                out_filenames.append(cur_name)

        return out_filenames

    def run(self):
        self.window.show_all()
        Gtk.main()
