create index on {schema}.import_meta using gist(bbox);
create index on {schema}.cj_object using gist(bbox);
