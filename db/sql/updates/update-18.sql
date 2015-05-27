create table pitch_study_props(
id integer primary key autoincrement,
clips_db_path text,
clips_dir_path text,
max_parts_per_batch integer,
num_options integer,
break_interval integer,
inter_clip_sound_del real
);

insert into pitch_study_props (
clips_db_path,
clips_dir_path,
max_parts_per_batch,
num_options,
break_interval,
inter_clip_sound_del) values (
'C:/Experimental Data/Daycare Study/Pitch Study Data/testing/data/clips.db',
'C:/Experimental Data/Daycare Study/Pitch Study Data/testing/clips/',
10,
4,
50,
0.8
);
