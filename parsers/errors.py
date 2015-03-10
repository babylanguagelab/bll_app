## @package parsers.errors

## This is an 'abstract' base class for custom exception classes.
class BllAppError(Exception):
    ## Constructor
    #  @param self
    #  @param msg (string) a descriptive error message for this exception
    #  @param obj (object) the object that this exception pertains to (eg. an Utterance or Segment)
    def __init__(self, msg, obj):
        super(Exception, self).__init__(msg)
        self.obj = obj
        self.msg = msg

    ## This method is called by the Python runtime when a string representatin of this exception is requested (eg. the exception is printed)
    #  @param self
    def __str__(self):
        output = '%s:\n' % (self.__class__.__name__)
        output += '-msg: "%s"\n' % (self.msg)
        #output += '-obj: %s\n' % (self.obj)

        return output

## The class represents an error that has been detected in a TRS file.
# (For example, the error could be something an invalid transcriber code, or a missing I/C link code.)
class ParserError(BllAppError):
    ## Constructor
    #  Currenlty, this class exists only to differentiate warnings from errors. We might need to add more stuff here later...
    #  See superclass parameter descriptions.
    def __init__(self, msg, obj):
        BllAppError.__init__(self, msg, obj)

## This class represents a warning that has been detected in a TRS file.
# Warnings are not as serious as errors - for example, an utterance might not have a speaker specified.
class ParserWarning(BllAppError):
    ## Constructor
    #  Currenlty, this class exists only to differentiate warnings from errors. We might need to add more stuff here later...
    #  See superclass parameter descriptions.
    def __init__(self, msg, obj):
        BllAppError.__init__(self, msg, obj)
