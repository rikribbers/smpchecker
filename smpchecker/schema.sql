drop table if exists events;

create table events (
  id integer primary key autoincrement,
  'event' integer not null,
  'timestamp' text(19) not null,
  smp_id integer
);

drop table if exists peppolmembers;

create table peppolmembers (
  id integer primary key autoincrement,
  peppolidentifier text not null unique,
  first_seen datetime not null,
  last_seen datetime
);

drop table if exists smpentries;

create table smpentries (
  id integer primary key autoincrement,
  documentidentifier text not null,
  certificate_not_before datetime not null,
  certificate_not_after datetime not null,
  endpointurl text not null,
  peppolmember_id integer not null,
  first_seen datetime not null,
  last_seen datetime,
  foreign key (peppolmember_id) references participants(id),
  unique (peppolmember_id, documentidentifier)
);
