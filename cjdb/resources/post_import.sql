-- cj_metadata indexes
CREATE INDEX IF NOT EXISTS cj_metadata_gix ON {schema}.cj_metadata USING gist(bbox);

CREATE INDEX IF NOT EXISTS cj_metadata_source_file_idx ON {schema}.cj_metadata USING hash(source_file);

-- city_object indexes
CREATE INDEX IF NOT EXISTS city_object_type_idx ON {schema}.city_object USING btree("type");

CREATE INDEX IF NOT EXISTS city_object_ground_gix ON {schema}.city_object USING gist(ground_geometry);

CREATE INDEX lod ON {schema}.city_object USING gin (geometry);

-- city_object_relationships indexes
CREATE INDEX IF NOT EXISTS city_object_relationships_parent_idx ON {schema}.city_object_relationships USING btree(parent_id);

CREATE INDEX IF NOT EXISTS city_object_relationships_child_idx ON {schema}.city_object_relationships USING btree(child_id);

-- clustering
cluster {schema}.cj_metadata USING cj_metadata_gix;

cluster {schema}.city_object USING city_object_ground_gix;