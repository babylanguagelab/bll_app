## @package utils.enum

from collections import OrderedDict

## A primitive enum class (Python has none).
# Sample usage:
# \code
# Animals = Enum(['COW', 'GOAT', 'ELEPHANT'])
# Animals.COW #this gives 0
# Animals.GOAT #this gives 1
# Animals.ELEPHANT #this gives 2
# Animals.TURKEY #this gives AttributeError
#
# #Supports ordered iteration:
# for creature in Animals:
#   print creature
# #This prints 0, 1, 2
#
# #Also supports indexing:
# print Animals[1] #this prints 1
#
#Can grab length like this:
# len(Animals) #this gives 3
#\endcode
#
# Note: Names should not override any Python internal class varibles (i.e. don't pass in names starting with '__'), or bad things will happen.
#
class Enum(object):
    ## Constructor
    # @param self
    # @param names (list) list of attribute names to assign to this enum
    # @param vals (list=None) list of values corresponding to the names. Passing None will cause the Enum to default to an integer value for each name (starting from zero and ascending).
    def __init__(self, names, vals=None):
        if vals == None:
            vals = range(len(names))

        self.elements = OrderedDict( zip(names, vals) )

    ## This is a Python hook method for retreival by direct key name (eg. Animals.COW).
    # @param self
    # @param name (string) name of the attribute to retrieve from this instance
    # @returns (anything) the requested attribute - or raises an AttributeError if an attribute with that name doesn't exist
    def __getattr__(self, name):
        if name in self.elements:
            return self.elements[name]
        raise AttributeError("Enum instance has no attribute '%s'" % (name))

    ## This is a Python hook method for iteration.
    # @param self
    # @returns (iterable object) an object that can be used to traverse the data structure
    def __iter__(self):
        return self.elements.__iter__()

    ## This is a Python hook method for for returning length.
    # @param self
    # @returns (int) the number of keys in this Enum.
    def __len__(self):
        return len(self.elements)

    ## This is a Python hook method for indexing.
    # @param self
    # @param index (int) the index of the element to look up - elements are indexed in the order the keys were in when they were passed to the constructor
    # @returns (anything) the value at the requested index, or throws an exception if the index is out of range
    def __getitem__(self, index):
        return self.elements.values()[index]

    ## Returns a list of the values contained in this Enum, in the order in which they were specified when passed to the constructor.
    # @param self
    # @returns (list) list of values
    def get_ordered_vals(self):
        return self.elements.values()

    ## Returns a list of the keys contained in this Enum, in the order in which they were specified when passed to the constructor.
    # @param self
    # @returns (list) list of keys
    def get_ordered_keys(self):
        return self.elements.keys()

    ## Static method to create an Enum from a dictionary of key-value pairs. If the Enum is created with an unordered dictionary,
    # the get_ordered_vals() and get_ordered_keys() methods will return values in an unspecified order.
    # @param src_dict (Dictionary) a dictionary of key-value pairs to insert into the Enum
    # @returns (Enum) a new Enum containing the dictionary data
    @staticmethod
    def from_dict(src_dict):
        names = src_dict.keys()
        vals = map(lambda key: src_dict[key], names)

        return Enum(names, vals)
