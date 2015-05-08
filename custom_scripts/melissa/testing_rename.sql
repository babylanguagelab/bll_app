create table clips (
id integer primary key autoincrement,
Filename text,
Age integer,
Condition text,
Speaker test,
Sentence_Type text,
Question_Type text,
Start_Time real,
Stop_Time real,
Duration real,
Lag_Time real,
Mother_Max_Pitch real,
Mother_Min_Pitch real,
Mother_Mean_Pitch real,
Mother_Pitch_Delta real,
Mother_Pitch_Category text,
Baby_Max_Pitch real,
Baby_Min_Pitch real,
Baby_Mean_Pitch real,
Baby_Pitch_Delta real,
Baby_Pitch_Category text);

insert into clips (
Filename,
Age,
Condition,
Speaker,
Sentence_Type,
Question_Type,
Start_Time,
Stop_Time,
Duration,
Lag_Time,
Mother_Max_Pitch,
Mother_Min_Pitch,
Mother_Mean_Pitch,
Mother_Pitch_Delta,
Mother_Pitch_Category,
Baby_Max_Pitch,
Baby_Min_Pitch,
Baby_Mean_Pitch,
Baby_Pitch_Delta,
Baby_Pitch_Category) select
col0,
col1,
col2,
col3,
col4,
col5,
col6,
col7,
col8,
col9,
col10,
col11,
col12,
col13,
col14,
col15,
col16,
col17,
col18,
col19 from data;

drop table data;

alter table clips add column Batch_Num integer;
alter table clips add column Batch_Order integer;
create index filename_index on clips (Filename);
create index batch_index on clips (Batch_Num, Batch_Order);

create table ratings (
id integer primary key autoincrement,
clip_id integer not null references clips (id),
Participant_Num integer not null,
Question_Rating integer not null
);
