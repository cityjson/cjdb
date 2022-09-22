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
    bbox geometry not null--2d bbox of the entire file
);

create table if not exists {schema}.cj_feature
(
    id serial primary key,
    import_meta_id int references {schema}.import_metadata(id),
    feature_id text unique not null, --CityJSON object identifier
    -- cityobjects jsonb not null, probably not needed, because there is table cj_object
    vertices jsonb not null,
    bbox geometry --2d bbox
);

create table if not exists {schema}.cj_object
(
    id serial primary key,
    cj_feature_id int references {schema}.cj_feature(id),
    object_id text unique not null,
    bbox geometry, --2d bbox
    -- object jsonb not null, -- optionally entire object as json, without the columns below
    type text not null,
    attributes jsonb,
    geometry jsonb
);

-- check how to index json attribute, for example to find object by its type