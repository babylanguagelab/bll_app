## @package data_structs.base_objects

import types

## A custom object that provides some handy debugging routines to subclasses.
class BLLObject(object):
    _FCN_TYPES = [types.FunctionType, types.MethodType]
    
    ## Checks if a particular attribute of this object is a function or method.
    #   @returns (boolean) True if the attribute with 'name' is a function/method, otherwise False
    #   @param self
    #   @param name (string) name of attribute to check
    def _is_function(self, name):
        found = False
        obj = getattr(self, name)
            
        i = 0
        while not found and i < len(BLLObject._FCN_TYPES):
            found = isinstance(obj, BLLObject._FCN_TYPES[i])
            i += 1
        
        return found

    ## Builds a nicely formatted string containing all attributes of this object (except those in omit_attr_names), for debugging purposes. Proceeds recursively (eg. if attribute is a object, calls __str__() on that object.
    #  @returns (string) as described above
    #  @param self
    #  @param omit_attr_names (list=[]) list of attribute names you don't want in the returned string (useful for preventing infinite recursion due to self-referencing pointers)
    def __str__(self, omit_attr_names=[]):
        #place the omitted names in a dictionary for quick lookup in the loop below
        omissions = {}
        for name in omit_attr_names:
            omissions[name] = True
            
        output = self.__class__.__name__ + ':\n'
        #go through all (at least, 'all' as defined by dir() ) attributes of this object
        for name in dir(self):
            #omit private (starts with underscore) attributes, methods, and names in the ommissions dictionary
            if not name.startswith('_') and not name in omissions and not self._is_function(name):
                val = getattr(self, name)
                val_str = val
                
                #format lists nicely
                if isinstance(val, list):
                    size = len(val)
                    val_str = '[\n' if size > 0 else '['
                    for i in range(size):
                        val_str += '  ' + str(val[i])
                        if i < size - 1:
                            val_str += ',\n'

                    val_str += '  ]'
                
                output += '  -%s: %s\n' % (name, val_str)

        return output

## Represents an object that can be stored in the database.
class DBObject(BLLObject):
    ## Constructor
    #  @param self
    def __init__(self):
        self.db_id = None

    ## Performs operations needed to insert this object into the database. Subclasses must override this method.
    #  @param self
    #  @param db (BLLDatabase) database object to use for the insertion operation.
    def db_insert(self, db):
        pass

    ## Performs operations needed to delete this object from the database. Subclasses must override this method.
    #  @param self
    #  @param db (BLLDatabase) database object to use for the deletion operation.
    def db_delete(self, db):
        pass

    ## Selects objects of this type from the database. Subclasses must override this method.
    #  @param db (BLLDatabase) database object to use for the selection operation.
    #  @param ids (list=[]) list of ids (primary key integers) from the corresponding DB table for this object that are to be selected. If empty, all objects from the corresponding table are selected.
    #  @returns (list) list of objects of this type, constructed from a SELECT query on the corresponding DB table.
    @staticmethod
    def db_select(db, ids=[]):
        pass

    ## Convenience method for subclasses. Constructs a SQL where condition clause from the specified ids.
    #  @param ids (list) list of integer primary keys
    #  @returns (string) clause like "WHERE id IN (0, 1, 2, 3, 4)" - assumes primary key column is named 'id'. Returns None if ids is empty.
    @staticmethod
    def _build_where_cond_from_ids(ids):
        where_cond = None
        if ids:
            in_str = reduce(lambda accum, x: '%s,%d' % (str(accum), x), ids)
            where_cond = 'id IN (%s)' % (in_str)

        return where_cond
