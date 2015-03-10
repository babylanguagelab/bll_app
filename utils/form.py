## @package utils.form

## This class provides a way to store UI input elements by name so that they can be retrieved later on.
# Basically, this is a dictionary, but elements can be added or accessed using the dot notation direclty.
# This is simply for convenience - so we don't have to pass a bunch of UI inputs around between methods
# in UI code for doing things like validation/retrieving user input.
# For example:
# \code
# def create_form():
#   form = Form()
#   form.my_entrybox = gtk.EntryBox(...)
#   form.my_spinner = gtk.SpinButton(...)
#   return form
#
# def process_form(form):
#   text_input = form.my_entrybox.get_text()
#   int_input = form.my_spinner.get_int_value()
#   ...
# \endcode
class Form(object):
    ## Constructor
    #  @param self
    def __init__(self):
        self._items = {}

    ## Called by Python when an instance's data/function member is set to something.
    #  @param self
    #  @param name (string) name of the member that is being set on this instance.
    #  @param val (anything) value to set the member to.
    def __setattr__(self, name, val):
        #this case is needed to prevent infinite recursion when the constructor assigns to _items
        if name == '_items':
            #Defer to the "object" class in a special way to perform the actual set.
            super(Form, self).__setattr__(name, val)
        else:
            self._items[name] = val

    ## Called by Python when an instance's data/function member is read.
    #  @param self
    #  @param name (string) name of the member being read.
    #  @returns (anything) value of the member being requested.
    def __getattr__(self, name):
        #This case is needed to prevent infinite recursion
        if name == '_items':
            return self._items
        #this case occurs when the user has requested something they've previously stored
        elif name in self._items:
            return self._items[name]
        #cause a fuss if nothing is found with the requested name
        else:
            raise AttributeError('Form instance has no attribute %s.' % (name))
    ## Returns a list of all the controls that have been stored in this Form instance (in no particular order)
    #  @param self
    #  @returns (list) list of whatever's been stored in this instance
    def get_item_list(self):
        return self._items.values()
