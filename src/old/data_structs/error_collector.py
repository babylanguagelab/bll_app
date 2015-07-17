## @package data_structs.error_collector

## This class maintains a collection of errors and warnings, providing various lookup methods to retreive them.
class ErrorCollector(object):
    ## Constructor
    #  @param self
    def __init__(self):
        self.collection = {}

    ## Adds a warning/error to this collector.
    #  @param self
    #  @param error (instance of any subclass of BLLAppError)
    def add(self, error):
        #The internal dictionary is keyed by error object.
        #Each key's value is a sub-dictionary.
        #Each sub-dictionary is keyed by the error's class name.
        #Each key's value is an array of the error instances themselves.
        #This structure provides a reasonably efficient layout for performing all of the lookups we need.

        #If there is nothing stored for this object yet, add the object as a key.
        if not error.obj in self.collection:
            self.collection[error.obj] = {}

        #if the sub-dictionary has no entry for this error's class, add one.
        if not error.__class__ in self.collection[error.obj]:
            self.collection[error.obj][error.__class__] = []

        #drop the error object into the appropraite location
        self.collection[error.obj][error.__class__].append(error)

    ## Retreives a list of all of the objects assocated with errors that have been added to this collector.
    #  Currently, these objects are always Utterances.
    #  @param self
    #  @returns (list) list of objects - currently Utterances - obtained from the 'obj' attribute of the errors added to this collector.
    def get_all_utters(self):
        return self.collection.keys()

    ## Retreives a list of all errors associated with a specific utterance
    #  @param self
    #  @param utter (object) an object - currently always an Utterance - to search for within the errors that have been added to this collector.
    #  @returns (list) a list of all errors whose 'obj' attribute is equal to the specified utterance
    def get_errors_by_utter(self, utter):
        error_list = []
        if utter in self.collection:
            for cls in self.collection[utter]:
                error_list.extend(self.collection[utter][cls])
            
        return error_list

    ## This method is for debugging - it prints out all of the Utterances currently in this collector, grouped by the error/warning class in which they were inserted.
    #  @param self
    #  @param utter (Utterance=None) if 'utter' is present in this collector the method will print it. Otherwise if will print nothing. If this is set to 'None', all utterances in the collector will be printed.
    #  @param error_cls (class=None) specify a subclass of BLLAppError to force the method to print out only utterances associated with errors of this type. Use 'None' to print utterances from all error classes.
    def print_errors(self, utter=None, error_cls=None):
        utter_list = []
        if utter and utter in self.collection.keys():
            utter_list.append(utter)
        elif not utter:
            utter_list = self.collection.keys()

        for u in utter_list:
            cls_list = []
            if error_cls and error_cls in self.collection[u].keys():
                cls_list.append(error_cls)
            elif not error_cls:
                cls_list = self.collection[u].keys()

            for cls in cls_list:
                if self.collection[u][cls]:
                    print u
                    for err in self.collection[u][cls]:
                        print err
        
