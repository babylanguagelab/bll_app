insert into settings (code_name, val) values ('LAST_NAPTIME_UPDATE', NULL);
insert into settings (code_name, val) values ('LAST_NAPTIME_FOLDER', NULL);

create table naptime_files (
id integer primary key autoincrement,
filename text
);

create table naptime (
id integer primary key autoincrement,
child_cd text not null,
start real not null,
end real not null
);

create index child_index on naptime (
child_cd,
start,
end
);
