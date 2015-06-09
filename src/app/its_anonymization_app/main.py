#!/usr/bin/python3
from gi.repository import Gtk

builder = Gtk.Builder()
builder.add_from_file("main.glade")

handlers = {
    "myDelete": Gtk.main_quit
}
builder.connect_signals(handlers)

window = builder.get_object("window")
#window.set_size_request(320, 640)
window.show_all()
Gtk.main()
