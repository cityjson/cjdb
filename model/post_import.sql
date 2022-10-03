create index import_meta_gix on {schema}.import_meta using gist(bbox);
create index cj_object_gix on {schema}.cj_object using gist(bbox);

cluster {schema}.import_meta using import_meta_gix;
cluster {schema}.cj_object using cj_object_gix;
