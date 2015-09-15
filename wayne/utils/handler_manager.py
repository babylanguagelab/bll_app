## @package utils.handler_manager

## This class is a data structure that stores information about handler methods for UI widgets. Handler methods are called
# when a UI widget generates an event, such as a button click. The main benefit of using this class is that it
# provides a lookup mechansim.
# You can lookup handlers for a particular widget based on a specified type of signal (event). Plain PyGTK does
# not provide a straightforward way to do this.
# Another benefit is that if we have a centralized data structure for all handlers in a form, we don't have to
# pass around lots of handler ids or function pointers when we want to do things like temporarily block a handler for a particular widget.
# Instead, you can just call the block_handler() / unblock_handler() methods for a particular widget and signal.
class HandlerManager(object):
    ## Constructor
    # @param self
    def __init__(self):
        self.conn_dict = {}

    ## Internal method to check if a particular handler (for a particular widget) is already stored in this instance.
    # @param self
    # @param obj (UI object) a UI widget object
    # @param sig (string) a GTK+ event string (like 'clicked' or 'destroy' - see PyGTK docs for a list for your desired widget)
    # @returns (boolean) True if the obj has a handler for sig that is stored in this instance, False otherwise
    def _have_handler(self, obj, sig):
        return obj in self.conn_dict and sig in self.conn_dict[obj]

    ## Adds a handler (for a particular widget) to this instance.
    # @param self
    # @param obj (UI object) the UI widget object for which we are adding a handler
    # @param sig (string)  a GTK+ event string (like 'clicked' or 'destroy' - see PyGTK docs for a list for your desired widget)
    # @param fcn (function pointer) the function that the signal will invoke
    # @param data (object=None) optional extra data to pass to the function when it is invoked (see pyGTK signal tutorials to learn more about this)
    def add_handler(self, obj, sig, fcn, data=None):
        handler_id = obj.connect(sig, fcn, data) if data else obj.connect(sig, fcn)

        if not obj in self.conn_dict:
            self.conn_dict[obj] = {}

        if not sig in self.conn_dict[obj]:
            self.conn_dict[obj][sig] = handler_id

    ## Retrieves a handler id (number used by GTK+ to identify a handler) for a given UI object and signal.
    # @param self
    # @param obj (UI object) the UI widget object to lookup
    # @param sig (string) a GTK+ event string (eg. 'clicked') indicating the signal to look for handlers for
    # @returns (int) a GTK+ handler id (see GTK+ docs for more info), or None if the (obj, sig) is not stored in this instance
    def get_handler_id(self, obj, sig):
        handler_id = None
        if self._have_handler(obj, sig):
            handler_id = self.conn_dict[obj][sig]

        return handler_id

    ## Temporarily prevents a specified signal from invoking handlers, for a given UI widget.
    # This does not remove the handler from this instance, nor does it disconnect the handler from the widget object.
    # The signal will be blocked for this widget until unblock_handler() is called (see below).
    # @param self
    # @param obj (UI object) the UI widget on which to block a handler
    # @param sig (string) a GTK+ event string (eg. 'clicked') indicating the signal to block
    def block_handler(self, obj, sig):
        if self._have_handler(obj, sig):
            obj.handler_block(self.conn_dict[obj][sig])

    ## Unblocks a signal that has been blocked with block_handler().
    # @param self
    # @param obj (UI object) the UI widget on which to unblock signal handlers.
    # @param sig (string) a GTK+ event string (eg. 'clicked') indicating the signal to unblock.
    def unblock_handler(self, obj, sig):
        if self._have_handler(obj, sig):
            obj.handler_unblock(self.conn_dict[obj][sig])

    ## Disconnects handler methods from a widget, and removes all record of the handler from this instance.
    # @param self
    # @param obj (UI object) the UI object whose handler we are disconnecting
    # @param sigs (list=None) list of GTK+ event strings (eg. ['clicked']) indicating the signals to remove handlers for. Pass None to remove all handlers for all signals for the widget.
    def remove_handlers(self, obj, sigs=None):
        if sigs:
            for cur_sig in sigs:
                if self._have_handler(obj, cur_sig):
                    obj.handler_disconnect(self.conn_dict[obj][cur_sig])
                    self.conn_dict[obj].pop(cur_sig)
            if not len(self.conn_dict[obj]):
                self.conn_dict.pop(obj)

        else:
            if obj in self.conn_dict:
                for sig in self.conn_dict[obj]:
                    obj.handler_disconnect(self.conn_dict[obj][sig])
                self.conn_dict.pop(obj)
