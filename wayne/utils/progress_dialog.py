## @package utils.progress_dialog

from gi.repository import Gtk as gtk

## A popup dialog box that displays a progress bar.
#
# Progress bars go through one or more "phases". In each phase, a different string is displayed in the middle of the bar.
# This allows you to tell the user something about what is being done while they're waiting. You can set up the phases
# by passing a list of strings to the constructor. You can move through them using the next_phase() method.
# The progress bar's "fill level" (a float value in [0.0, 1.0])can be updated by calling the set_fraction() method. This advances the fill level to
# a given proportion of completeness <em>for the current phase</em>.
#
# For example, if your progress bar has only one phase, calling set_fraction(0.5) will advance the fill level to the halfway fill point.
# On the other hand if the progress bar has two phases, and we are in phase 1, then calling set_fraction(0.5) will advance the fill level to half of phase one (the one quarter fill point).
# Subsequently calling next_phase() advances to phase 2. Here, calling set_fraction(0.5) will advance the fill level to half of phase two (the three-quarter fill point).
#
# When the progress bar reaches a fill level of 1.0 (or higher), the dialog box automatically closes.
#
# To ensure that progress bars don't get left lying around if something goes wrong (like an exception in the processing code that prevents an update of the fill level, or a round-off error in your fill level calculations that results in a
# maximum fill level of something like 0.99), you should always call ensure_finish() when you are done your processing (or in your exception handling code). This will force the dialog to close if it's still around.
# Note that instantiating this class does not show the progress dialog - you must call the show() method (inherited from gtk.Dialog) when you want that to happen.
class ProgressDialog(gtk.Dialog):
        ## Constructor
        # @param self
        # @param title (string=None) string to display in the titlebar of the dialog
        # @param phases (list=['']) list of strings, one for each phase
        # @param parent (gtk widget) the dialog's temporary parent, or None. This allows you to link the dialog together with its parent and do things like have them destroyed at the same time - see superclass description (gtk docs for gtk.Dialog) for details.
        # @param flags (int=0) gtk flags to control how the dialog works - see superclass description (gtk docs for gtk.Dialog) for available options here.
        # @param buttons (tuple=None) a tuple of button text/response code pairs for buttons to create in this dialog, or None - see superclass description (gtk docs for gtk.Dialog).
        def __init__(self, title=None, phases=[''], parent=None, flags=0, buttons=None):
            gtk.Dialog.__init__(self, title, parent, flags, buttons)
            self.phases = phases
            self.cur_phase = 0
            
            self.pb = gtk.ProgressBar()
            self.pb.set_show_text(True)
            self.pb.set_orientation(gtk.Orientation.HORIZONTAL)
            self.pb.set_fraction(0.0)
            self.pb.set_text(self.phases[self.cur_phase])

            content_box = self.get_content_area()
            content_box.pack_start(self.pb, True, True, 0)
            self.pb.show()
            content_box.show()
            #leave the responsibility of showing the dialog itself up to the caller

        ## Sets the "fill level" of the progress bar. See this class' description for details about how this is done.
        # @param self
        # @param fraction (float) a float value in the range [0.0, 1.0]. This will set the fill level to (phase / num_phases + fraction / num_phases).
        # In other words, it sets the current phase's fill level. To completely fill the progress bar, you must move through the phases (using next_phase()), increasing the fill level to 1.0 in each of them.
        def set_fraction(self, fraction):
            self.pb.set_fraction(float(self.cur_phase) / float(len(self.phases)) + float(fraction) / float(len(self.phases)))
            #this forces gtk to process all pending UI updates (without it, the progress bar remains uninitialized until processing is complete - then it displays 100% completion...
            while gtk.events_pending():
                #gtk.main_iteration(False)
                gtk.main_iteration()

            #kill the dialog when we reach 100% completion
            if self.pb.get_fraction() >= 1.0:
                self.destroy()

        ## Move the progress dialog to the next phase. See this class' description for more info on "phases". Moving to the next phase will update the text in the center of the progress bar
        # to the next value in the "phases" list that was passed to the constructor.
        # @param self
        def next_phase(self):
            self.cur_phase += 1
            self.pb.set_text(self.phases[self.cur_phase])
            while gtk.events_pending():
                #gtk.main_iteration(False)
                gtk.main_iteration()

        ## Returns the current fill level (absolute fill level, not the fill level of the current phase) of the progress bar, as a float.
        # @returns (float) a number in the range [0.0, 1.0]
        def get_fraction(self):
            return self.pb.get_fraction()

        ## If the progress bar is not at 100% completion, this method will move it there, which closes the dialog.
        def ensure_finish(self):
            if self.pb.get_fraction() < 1.0:
                self.set_fraction(1.0)
