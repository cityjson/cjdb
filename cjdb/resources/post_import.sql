-- import_meta indexes
CREATE INDEX IF NOT EXISTS import_meta_gix ON {schema}.import_meta USING gist(bbox);

CREATE INDEX IF NOT EXISTS import_meta_source_file_idx ON {schema}.import_meta USING hash(source_file);

-- cj_object indexes
CREATE INDEX IF NOT EXISTS cj_object_type_idx ON {schema}.cj_object USING btree("type");

CREATE INDEX IF NOT EXISTS cj_object_ground_gix ON {schema}.cj_object USING gist(ground_geometry);

CREATE INDEX lod ON {schema}.cj_object USING gin (geometry);

-- family indexes
CREATE INDEX IF NOT EXISTS family_parent_idx ON {schema}.family USING btree(parent_id);

CREATE INDEX IF NOT EXISTS family_child_idx ON {schema}.family USING btree(child_id);

-- clustering
cluster {schema}.import_meta USING import_meta_gix;

cluster {schema}.cj_object USING cj_object_ground_gix;