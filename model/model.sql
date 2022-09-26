create schema if not exists {schema};

create table if not exists {schema}.import_meta
(
    id serial primary key,
    source_file text, --unique? warning when importing the same file again?
    version varchar(10) not null,
    transform jsonb not null,
    metadata jsonb,
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    bbox geometry--2d bbox of the entire file
);

create table if not exists {schema}.cj_object
(
    id serial primary key,
    import_meta_id int references {schema}.import_meta(id),
    object_id text unique not null,
    type text not null,
    attributes jsonb,
    geometry jsonb,
    parents jsonb,
    children jsonb,
    bbox geometry
);

-- check how to index json attribute, for example to find object by its type