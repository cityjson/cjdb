create index if not exists import_meta_gix on {schema}.import_meta using gist(bbox);
create index if not exists import_meta_source_file_idx on {schema}.import_meta using hash(source_file);

create index if not exists cj_object_gix on {schema}.cj_object using gist(bbox);


cluster {schema}.import_meta using import_meta_gix;
cluster {schema}.cj_object using cj_object_gix;
