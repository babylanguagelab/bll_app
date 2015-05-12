from data_structs.base_objects import DBObject
from utils.enum import Enum

class PitchStudyProps(DBObject):
    PROPS = Enum(
        ['CLIPS_DB_PATH', 'CLIPS_DIR_PATH', 'MAX_PARTS_PER_BATCH', 'NUM_OPTIONS', 'BREAK_INTERVAL', 'INTER_CLIP_SOUND_DEL'],
        ['clips_db_path', 'clips_dir_path', 'max_parts_per_batch', 'num_options', 'break_interval', 'inter_clip_sound_del']
    )
    
    def __init__(
            self,
            clips_db_path,
            clips_dir_path,
            max_parts_per_batch,
            num_options,
            break_interval,
            inter_clip_sound_del,
            db_id = None
    ):
        super(PitchStudyProps, self).__init__()

        self.clips_db_path = clips_db_path
        self.clips_dir_path = clips_dir_path
        self.max_parts_per_batch = max_parts_per_batch
        self.num_options = num_options
        self.break_interval = break_interval
        self.inter_clip_sound_del  = inter_clip_sound_del
        self.db_id = db_id

    @staticmethod
    def db_select(db, ids=[]):
        DBObject.db_select(db, ids)

        where_cond = None
        if ids:
            where_cond = DBObject._build_where_cond_from_ids(ids)

        rows = db.select(
            'pitch_study_props',
            'clips_db_path clips_dir_path max_parts_per_batch num_options break_interval inter_clip_sound_del id'.split(),
            where_cond=where_cond
        )

        props = []
        for cur_row in rows:
            props.append(PitchStudyProps(*cur_row))
        return props

    def db_delete(self, db):
        super(PitchStudyProps, self).db_delete(db)

        num_rows = db.delete('pitch_study_props', 'id = ?', [self.db_id])
        self.db_id = None

        return num_rows

    #prop must be a  value from the PitchStudyApp.PROPS enum
    def update_prop(self, db, prop, val):
        rowcount = db.update(
            'pitch_study_props',
            [prop], #I know...it's not right - but there is no risk of SQL injection in the lab
            where_cond='id = ?',
            params=[val, self.db_id]
        )

        if rowcount > 0:
            setattr(self, prop, val)
