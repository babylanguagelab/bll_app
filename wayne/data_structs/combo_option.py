## @package data_structs.combo_option

from data_structs.base_objects import BLLObject

## This class represents a single entry in a UI combo box. This class is instantiated automatically by machinery in utils/ui_utils; it should never need to be directly instantiated by other code. See UIUtils.COMBOS if you need to access combo box data.
# Note: Although it is tied to the database, this object is not a subclass of DBObject because DBObjects can be inserted and removed via Python code, and that is not the intention for this ComboOptions (they should be added or deleted only by SQL update scripts).
class ComboOption(BLLObject):
    ## Constructor
    #  @param self
    #  @param db_id (int) corresponding id from the combo_options DB table
    #  @param code_name (string) value corresponding to the code_name column in the combo_options DB table
    #  @param group_id (int) value corresponding to the group_id column in combo_options DB table. All options belong to a group (from the combo_groups DB table), and each groups corresponds to a single combo box in the UI.
    #  @param disp_desc (string) value from the corresponding value from the combo_options DB table - this is the text the user sees for the combobox option
    #  @param hidden (boolean integer) value from the corresponding column in combo_options DB table - if 0, this option is not shown in the UI. If 1, it is shown.
    def __init__(self, db_id, code_name, group_id, disp_desc, hidden):
        self.db_id = db_id
        self.code_name = code_name
        self.group_id = group_id
        self.disp_desc = disp_desc
        self.hidden = hidden
