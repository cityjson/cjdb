-- import_meta indexes
create index if not exists import_meta_gix on {schema}.import_meta using gist(bbox);
create index if not exists import_meta_source_file_idx on {schema}.import_meta using hash(source_file);

-- cj_object indexes
create index if not exists cj_object_type_idx on {schema}.cj_object using btree("type");
create index if not exists cj_object_ground_gix on {schema}.cj_object using gist(ground_geometry);

-- family indexes
create index if not exists family_parent_idx on {schema}.family using btree(parent_id);
create index if not exists family_child_idx on {schema}.family using btree(child_id);

-- clustering
cluster {schema}.import_meta using import_meta_gix;
cluster {schema}.cj_object using cj_object_ground_gix;
