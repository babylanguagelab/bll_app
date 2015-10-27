## @package data_structs.output

from data_structs.base_objects import DBObject
from data_structs.output_calcs import *
from data_structs.seg_filters import SegFilter

## An Output represents particular statistic that the user is trying to calculate from a TRS file. It is used in the Statistics Application.
# Each Output corresponds to a single Configuration object. Configurations can have multiple Outputs.
# The exported spreadsheet constains a single section for each Output in the selected Configuration.
# Calling code should instantiate this object, then use it's add_item() method to pass in segments/chains that it want's included in this output's calculations.
class Output(DBObject):
    ## Constructor
    #  @param self
    #  @param name (string) the user-specified name for this output
    #  @param desc (string) the user-specified description for this output
    #  @param filters (list) list of SegFilter objects to apply to data that is inserted into this Output
    #  @param output_calc (OutputCalc) an object used to perform any arithmetic/processing needed to generate this output's section in the spreadsheet file
    #  @param chained (boolean) True if we're using linked segments, False if we're using unlinked segments
    #  @param db_id (int=None) database primary key value for this object - code should not set, it's set via db_insert() and db_select(). A value of None indicates that this Output is not in the database.
    def __init__(self, name, desc, filters, output_calc, chained, db_id=None):
        self.name = name
        self.desc = desc
        self.filters = filters or []
        self.output_calc = output_calc
        self.chained = chained
        self.db_id = db_id

        #these are used to hold all of the data that's inserted into this output
        self.segs = []
        self.chains = []

    ## Clears any cached utterances in preparation for a new run.
    #  @param self
    def reset(self):
        self.segs = []
        self.chains = []
        #the calc object needs to be notified so it can restart it's processing
        self.output_calc.reset()

    ## Accepts a segment/chain, filters it, and (if it passes through the filters) factors it into this output's calculations.
    #  @param self
    #  @param item (Segment / Utterance) the data object to add to this output. If chained is set to True, this should be an Utterance object (potentially linked to other Utterance objects via its 'next'/'prev' pointers). If chained is False, this should be a Segment object.
    #  @param filter_utters (boolean=False) If True, and chained == False, then any utterances that don't pass the filter will be stripped out of the segments passed in (but the segment itself will still be included if it has other utterances. If False, and chained == False, then it the segment that's passed in has any utterance that fails to pass the filter, the whole segment will be excluded. If chained == True, the setting of this parameter has no effect (in all cases, if one node in the chain fails to pass the filter, the whole chain is excluded - conceptually, chains are treated as a single, long Utterance).
    def add_item(self, item, filter_utters=False):
        if self.chained:
            self._add_chain(item)
            
        else:
            self._add_seg(item, filter_utters)


    ## Adds an unlinked segment to this Output, if it passes through the filters.
    #  @param self
    #  @param seg (Segment) the Segment object to add
    #  @param filter_utters (boolean=False) see description for add_item()
    def _add_seg(self, seg, filter_utters=False):
        #run the segment through the filters - the tasks associated with filter_utters are deferred to the seg_filter objects
        i = 0
        filtered_seg = seg
        while filtered_seg and i < len(self.filters):
            filtered_seg = self.filters[i].filter_seg(filtered_seg, filter_utters)
            i += 1

        #if it made it through the filters, append the seg to this object's internal list of unlinked segments, and factor it into the output calculations
        if filtered_seg:
            self.segs.append(filtered_seg)
            self.output_calc.add_seg(filtered_seg)

    ## Adds chain (an Utterance) to this Output, if it passes through the filters.
    #  @param self
    #  @param head (Utterance) the Utterance (head of the chain) to add
    def _add_chain(self, head):
        #run the chain through the filters
        i = 0
        filtered_head = head
        while filtered_head and i < len(self.filters):
            filtered_head = self.filters[i].filter_linked_utter(filtered_head)
            i += 1

        #it if made it through the filters, append the chain to this object's internal list of chains, and factor it into the output calculations
        if filtered_head:
            self.chains.append(filtered_head)
            self.output_calc.add_chain(filtered_head)

    ## Grabs a list of all items that have been added to this Output that have passed through the filters.
    #  @param self
    #  @returns (list) list of Utterances, if chained. Otherwise list of Segments.
    def get_filtered_items(self):
        return (self.chains if self.chained else self.segs)

    ## See superclass description
    def db_insert(self, db):
        super(Output, self).db_insert(db)

        #insert this object into the outputs DB table, retreiving the PK id value.
        last_ids = db.insert('outputs',
                             'name desc calc_class_name calc_args chained'.split(),
                             [[self.name,
                               self.desc,
                               self.output_calc.__class__.__name__,
                               str(self.output_calc.get_db_args()),
                               self.chained,
                               ]])
        self.db_id = last_ids[0]

        #insert each of this Output's filters into the DB, if it's not already present in the DB
        for cur_filter in self.filters:
            if cur_filter.db_id == None:
                cur_filter.db_insert(db)

            #always insert a row into the relation table that maps outputs to their corresponding filters
            print '\nInserting into outputs_to_seg_filters:'
            print 'output_id: %s' % (str(self.db_id))
            print 'filter_id: %s' % (str(cur_filter.db_id))

            db.insert('outputs_to_seg_filters',
                      'output_id seg_filter_id'.split(),
                      [[self.db_id, cur_filter.db_id]])

    #See superclass description.
    def db_delete(self, db):
        super(Output, self).db_delete(db)
        
        db.delete('outputs',
                  'id=?',
                  [self.db_id])
        
        #Note: Foreign keys will cause the above statement to also delete from:
        #output_configs_to_outputs,
        #outputs_to_seg_filters
        
        #we still need to delete from seg_filters
        for cur_filter in self.filters:
            if cur_filter.db_id != None:
                cur_filter.db_delete(db)
            
        self.db_id = None

    ## Writes a description of this output, and the calculated information from this output, to a CSV file.
    #  @param self
    #  @param csv_writer (CSVWriter) this is a Python csv library writer objects, configured to write to the appropriate csv file.
    def write_csv_rows(self, csv_writer):
        #write out a description of this output
        csv_writer.writerow(['------------------'])
        csv_writer.writerow(['Name:', self.name])
        csv_writer.writerow(['Description:', self.desc])
        csv_writer.writerow(['Link Segments:', str(bool(self.chained))])
        csv_writer.writerow(['Filters:'])

        #write out any filters
        if self.filters:
            for cur_filter in self.filters:
                csv_writer.writerow(['', cur_filter.get_filter_type_str(), cur_filter.get_filter_desc_str()])
        else:
            csv_writer.writerow(['', 'None'])

        #write the calculated information
        csv_writer.writerow([''])
        self.output_calc.write_csv_rows(self.chained, csv_writer)
        csv_writer.writerow(['------------------'])
        

    ## See superclass description.
    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(db, ids)

        #select the output data from the outputs table
        rows = db.select('outputs',
                         'id name desc calc_class_name calc_args chained'.split(),
                         DBObject._build_where_cond_from_ids(ids),
                         )


        #create an Output object for each row
        output_list = []
        for cur_row in rows:
            #instantiate the OutputCalc object
            calc_class = eval(cur_row[3])
            calc_args = eval(cur_row[4])
            output_calc = calc_class(*calc_args)

            #instantiate any filter objects associated with this outputs
            filters = SegFilter.db_select_by_ref(
                db,
                'outputs_to_seg_filters',
                'seg_filter_id',
                'output_id',
                cur_row[0],
                )

            #create the Output object using the info retreived above
            output = Output(cur_row[1],
                            cur_row[2],
                            filters,
                            output_calc,
                            cur_row[5],
                            cur_row[0]
                            )

            output_list.append(output)

        return output_list

    ## Selects Outputs via a relationship table (a table linking output ids to some other type of id).
    #  @param db (BLLDatabase) a database handle object to use for the select operation
    #  @param ref_table (string) the name of the relationship table to use
    #  @param id_col (string) name of the column (in ref_table) containing output 
    #  @param ref_col (string) name of the column (in ref table) containing the value you want to look up outputs by
    #  @param ref_val (int) value to search for in ref_col. For each matching row, the id_col value is obtained (this is the output id), and used to do a lookup in the outputs table.
    #  @returns (list) list of Output objects, or empty list if no matches were found for ref_val in ref_col of ref_table
    @staticmethod
    def db_select_by_ref(db, ref_table, id_col, ref_col, ref_val):
        outputs = []

        #perfrom the select on ref_table
        rows = db.select(ref_table, [id_col], '%s=?' % (ref_col), [ref_val])
        #retreive the output ids from the result set
        ids = map(lambda cur_row: cur_row[0], rows)

        #select outputs if we obtained some ids from ref_table
        if ids:
            outputs = Output.db_select(db, ids)

        return outputs
