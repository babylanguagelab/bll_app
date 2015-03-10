from gi.repository import Gtk as gtk
from gi.repository import WebKit as webkit

class DiffWin():
    def __init__(self, html):
        self.window = gtk.Window()
        self.window.set_title('Transcription Verifier - File Comparison')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_default_size(1200, 600)
        self.window.set_resizable(True)

        scrolled_win = gtk.ScrolledWindow()
        view = webkit.WebView()
        scrolled_win.add(view)
        self.window.add(scrolled_win)

        view.load_html_string(
            html,
            'file:///'
        )

        self.window.show_all()
