-- Compare schema sizes:
SELECT
    schemaname,
    pg_size_pretty(
        sum(
            pg_relation_size(
                quote_ident(schemaname) || '.' || quote_ident(tablename)
            )
        ) :: bigint
    ) AS table_size,
    pg_size_pretty(
        sum(
            pg_indexes_size(
                quote_ident(schemaname) || '.' || quote_ident(tablename)
            )
        ) :: bigint
    ) AS index_size,
    pg_size_pretty(
        sum(pg_total_relation_size(reltoastrelid)) :: bigint
    ) AS toast_size,
    pg_size_pretty(
        sum(
            pg_total_relation_size(
                quote_ident(schemaname) || '.' || quote_ident(tablename)
            )
        ) :: bigint
    ) AS total_size
FROM
    pg_tables
    JOIN pg_class c ON c.oid = (
        quote_ident(schemaname) || '.' || quote_ident(tablename)
    ) :: regclass :: oid
WHERE
    schemaname IN (
        'bag_3dcitydb_test',
        'bag_cjdb',
        'vienna_3dcitydb',
        'vienna_cjdb',
        'ny_cjdb',
        'ny_3dcitydb'
    )
GROUP BY
    schemaname
ORDER BY
    schemaname;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------0. Show the ids of all buildings made after the year 2000 ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 3DcityDB
EXPLAIN ANALYZE
SELECT
    gmlid
FROM
    bag_3dcitydb.cityobject co
    JOIN bag_3dcitydb.cityobject_genericattrib coga ON co.id = coga.cityobject_id
WHERE
    coga.attrname = 'oorspronkelijkbouwjaar'
    AND coga.intval > 2000;

-- CJDB:
EXPLAIN ANALYZE
SELECT
    object_id
FROM
    bag_cjdb.city_object
WHERE
    (attributes -> 'oorspronkelijkbouwjaar') :: int > 2000;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------1. Query all buildings with roof_height higher than 20m ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
--- 1A: BAG
-- 3DCityDB :
EXPLAIN ANALYZE
SELECT
    gmlid
FROM
    bag_3dcitydb_test.cityobject co
    JOIN bag_3dcitydb_test.cityobject_genericattrib coga ON co.id = coga.cityobject_id
WHERE
    coga.attrname = 'h_dak_max'
    AND coga.realval > 20;

SELECT
    *
FROM
    bag_3dcitydb.building cg;

-- CJDB: 
EXPLAIN ANALYZE
SELECT
    object_id
FROM
    bag_cjdb.city_object
WHERE
    (attributes -> 'h_dak_max') :: float > 20;

--- 1B: NYC
---NOT Possible
--- 1C: Vienna
-- 3DCityDB: 24 + 23 + 24 + 20 + 20
EXPLAIN ANALYZE
SELECT
    gmlid
FROM
    vienna_3dcitydb.cityobject co
    JOIN vienna_3dcitydb.cityobject_genericattrib coga ON co.id = coga.cityobject_id
WHERE
    coga.attrname = 'HoeheDach'
    AND coga.strval :: float > 20;

-- CJDB: Execution Time: 2 + 2 + 2 + 2 + 2
EXPLAIN ANALYZE
SELECT
    object_id
FROM
    vienna_cjdb.city_object
WHERE
    REPLACE((attributes -> 'HoeheDach') :: varchar, '"', '') :: float > 20;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------2. Query all buildings within a certain bounding box ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
--- 2A: BAG
-- 3DcityDB
EXPLAIN ANALYZE
SELECT
    c.gmlid,
    sg.geometry
FROM
    bag_3dcitydb.thematic_surface AS ts
    LEFT JOIN bag_3dcitydb.surface_geometry AS sg ON ts.lod2_multi_surface_id = sg.parent_id
    LEFT JOIN bag_3dcitydb.cityobject AS c ON ts.building_id = c.id
WHERE
    ST_Contains(
        ST_MakeEnvelope(85400, 446900, 85600, 447100, 7415),
        sg.geometry
    )
    AND ts.objectclass_id = 35;

-- CJDB:
EXPLAIN ANALYZE
SELECT
    object_id,
    ground_geometry
FROM
    bag_cjdb.city_object
WHERE
    TYPE = 'Building'
    AND ST_Contains(
        ST_MakeEnvelope(85400, 446900, 85600, 447100, 7415),
        ground_geometry
    );

--- 2B: NYC
-- 3DcityDB
EXPLAIN ANALYZE
SELECT
    c.gmlid,
    sg.geometry
FROM
    ny_3dcitydb.thematic_surface AS ts
    LEFT JOIN ny_3dcitydb.surface_geometry AS sg ON ts.lod2_multi_surface_id = sg.parent_id
    LEFT JOIN ny_3dcitydb.cityobject AS c ON ts.building_id = c.id
WHERE
    ST_Contains(
        ST_MakeEnvelope(
            985330.000,
            219464.200,
            987330.000,
            221464.200,
            7415
        ),
        sg.geometry
    )
    AND ts.objectclass_id = 35;

-- CJDB: 
EXPLAIN ANALYZE
SELECT
    object_id,
    ground_geometry
FROM
    ny_cjdb.city_object
WHERE
    ST_Contains(
        ST_MakeEnvelope(
            985330.000,
            219464.200,
            987330.000,
            221464.200,
            3628
        ),
        ground_geometry
    );

--- 2C: Vienna
----------------------------------------------------------------------------------------------------------------
--------------------------------------------3. Query building on point ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 3DcityDB
EXPLAIN ANALYZE
SELECT
    gmlid,
    envelope
FROM
    bag_3dcitydb.cityobject
WHERE
    envelope & & st_setsrid(ST_MakePoint(85200, 446900), 7415)
    AND objectclass_id = 26;

-- BUT MORE ACCURATE:   
EXPLAIN ANALYZE
SELECT
    c.gmlid,
    sg.geometry
FROM
    bag_3dcitydb.thematic_surface AS ts
    LEFT JOIN bag_3dcitydb.surface_geometry AS sg ON ts.lod2_multi_surface_id = sg.parent_id
    LEFT JOIN bag_3dcitydb.cityobject AS c ON ts.building_id = c.id
WHERE
    sg.geometry & & st_setsrid(ST_MakePoint(85200, 446900), 7415)
    AND ts.objectclass_id = 35;

-- CJDB :  Query building on point
EXPLAIN ANALYZE
SELECT
    object_id,
    ground_geometry
FROM
    bag_cjdb.city_object
WHERE
    TYPE = 'Building'
    AND ground_geometry & & st_setsrid(ST_MakePoint(85200, 446900), 7415);

----------------------------------------------------------------------------------------------------------------
--------------------------------------------4. Query the number of parts for each building ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 3DcityDB
EXPLAIN ANALYZE
SELECT
    cj.gmlid AS building_id,
    count(b.id) AS number_of_parts
FROM
    bag_3dcitydb.cityobject cj
    LEFT JOIN bag_3dcitydb.building b ON cj.id = b.building_parent_id
WHERE
    cj.objectclass_id = 26
GROUP BY
    cj.id;

-- CJDB
EXPLAIN ANALYZE
SELECT
    co.object_id AS building_id,
    COUNT(cor.child_id) AS number_of_parts
FROM
    bag_cjdb.city_object co
    LEFT JOIN bag_cjdb.city_object_relationships cor ON co.object_id = cor.parent_id
WHERE
    co.type = 'Building'
GROUP BY
    co.object_id;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------5. Query all buildings LoD 1.1 ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 3DcityDB :
EXPLAIN ANALYZE
SELECT
    co.gmlid,
    co.envelope
FROM
    bag_3dcitydb.cityobject co
    JOIN bag_3dcitydb.building b ON co.id = b.id
    JOIN bag_3dcitydb.surface_geometry sg ON b.id = sg.cityobject_id
WHERE
    b.lod1_solid_id IS NOT NULL;

-- CJDB:
EXPLAIN ANALYZE
SELECT
    object_id,
    ground_geometry
FROM
    bag_cjdb.city_object
WHERE
    geometry :: jsonb @ > '[{"lod": 1.2}]' :: jsonb;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------6. Example query of building roofs constructed after the year 2000 ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 3DcityBAG 
EXPLAIN ANALYZE
SELECT
    ts.id AS roof_id,
    co_ts.gmlid AS roof_gmlid,
    building.id AS building_id,
    co.gmlid AS building_gmlid,
    coga.intval AS year_of_construction,
    ST_Collect(sg.geometry) AS roof_geom
FROM
    bag_3dcitydb.thematic_surface AS ts
    INNER JOIN bag_3dcitydb.cityobject AS co_ts ON (co_ts.id = ts.id)
    INNER JOIN bag_3dcitydb.surface_geometry AS sg ON (ts.lod2_multi_surface_id = sg.root_id)
    INNER JOIN bag_3dcitydb.building AS building_part ON (building_part.id = ts.building_id)
    INNER JOIN bag_3dcitydb.building AS building ON (building_part.building_parent_id = building.id)
    INNER JOIN bag_3dcitydb.cityobject AS co ON (co.id = building.id)
    INNER JOIN bag_3dcitydb.cityobject_genericattrib coga ON co.id = coga.cityobject_id
WHERE
    ts.objectclass_id = 33 -- roofsurfaces
    AND building.objectclass_id = 26
    AND coga.attrname = 'oorspronkelijkbouwjaar'
    AND coga.intval > 2000
GROUP BY
    ts.id,
    co_ts.gmlid,
    building.id,
    co.gmlid,
    coga.intval
ORDER BY
    ts.id;

-- Not possible in  CJDB