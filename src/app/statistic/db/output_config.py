# new structure:
# output_configs -> Overview,
# output -> output,
# seg_filter -> filter
# class Overview()
# class Output()
# class Filter()

## An OutputConfig is a set of Outputs that can be 'run' on a particular TRS file. These groupings are recorded in the database.
class OutputConfig(DBObject):
    ## Constructor
    #  @param self
    #  @param name (string) user-defined name for this config
    #  @param desc (string) user-defined description of this config
    #  @param outputs (list) list of the Output objects that this config wraps
    #  @param created (string=None) creation timestamp string. This is set via db_insert() and db_select(), so you shouldn't often need to use it. A value of None indicates this config isn't in the DB yet.
    #  @param db_id (int=None) if this config is in the DB, this is the corresponding primary key value from the output_configs table (else it is None). This is set via db_insert() and db_select(), so you shouldn't often need to use it.
    def __init__(self, name, desc, outputs, created=None, db_id=None):
        self.name = name
        self.desc = desc
        self.outputs = outputs
        self.created = created
        self.db_id = db_id

    ## See superclass description.
    def db_insert(self, db):
        super(OutputConfig, self).db_insert(db)

        #insert into the output_configs DB table, and set the db_id
        last_ids = db.insert('output_configs',
                             'name desc'.split(),
                             [[self.name, self.desc]]
                             )
        self.db_id = last_ids[0]

        #perform a follow-up select to grab the created timestamp (the DB handles the setting of this upon insertion)
        rows = db.select('output_configs',
                         ["datetime(created,'localtime')"],
                         'id=?',
                         [str(self.db_id)],
                         )
        self.created = rows[0][0]

        #make sure all of the outputs are in the DB
        for cur_output in self.outputs:
            if not cur_output.db_id:
                cur_output.db_insert(db)

            #insert a record into the relationship table that links the outputs to this config in the DB
            db.insert('output_configs_to_outputs',
                      'config_id output_id'.split(),
                      [[self.db_id, cur_output.db_id]],
                      )

    ## See superclass description.
    def db_delete(self, db):
        super(OutputConfig, self).db_delete(db)

        #remove the outputs from the DB.
        #note: this will also delete the corresponding rows in output_configs_to_outputs due to foreign key cascades
        for cur_output in self.outputs:
            cur_output.db_delete(db) 

        if db.delete('output_configs', 'id=?', [self.db_id]) > 0:
            self.db_id = None

    ## See superclass description.
    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(db, ids)

        #select the configs
        rows = db.select('output_configs',
                         "id name desc datetime(created,'localtime')".split(),
                         DBObject._build_where_cond_from_ids(ids),
                         )

        #construct the OutputConfig objects
        config_list = []
        for cur_row in rows:
            #select the corresponding Outputs for this config using a relationship table
            outputs = Output.db_select_by_ref(db,
                                              'output_configs_to_outputs',
                                              'output_id',
                                              'config_id',
                                              cur_row[0],
                                              )

            config = OutputConfig(cur_row[1],
                                  cur_row[2],
                                  outputs,
                                  cur_row[3],
                                  cur_row[0],
                                  )
            config_list.append(config)

        return config_list

