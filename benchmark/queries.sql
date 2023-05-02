-- Compare schema sizes:
SELECT
    schema_name,
    pg_size_pretty(sum(table_size) :: bigint) AS "disk space",
    (
        sum(table_size) / pg_database_size(current_database())
    ) * 100 AS "percent"
FROM
    (
        SELECT
            pg_catalog.pg_namespace.nspname AS schema_name,
            pg_relation_size(pg_catalog.pg_class.oid) AS table_size
        FROM
            pg_catalog.pg_class
            JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid
    ) t
GROUP BY
    schema_name
HAVING
    schema_name IN (
        'vienna_3dcitydb',
        'vienna_cjdb',
        'bag_3dcitydb',
        'bag_cjdb'
    )
ORDER BY
    schema_name;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------1. Show the ids of all buildings made after the year 2000 ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 3DcityDB
EXPLAIN ANALYZE
SELECT
    gmlid
FROM
    bag_3dcitydb.cityobject
WHERE
    cityobject.id IN (
        SELECT
            cityobject_genericattrib.cityobject_id
        FROM
            bag_3dcitydb.cityobject_genericattrib
        WHERE
            attrname = 'oorspronkelijkbouwjaar'
            AND intval > 2000
    );

-- CJDB:
EXPLAIN ANALYZE
SELECT
    object_id
FROM
    bag_cjdb.city_object
WHERE
    (attributes -> 'oorspronkelijkbouwjaar') :: int > 2000;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------2. Query all buildings within a certain bounding box ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 3DcityDB
EXPLAIN ANALYZE
SELECT
    gmlid,
    envelope
FROM
    bag_3dcitydb.cityobject
WHERE
    objectclass_id = 26
    AND ST_Contains(
        ST_MakeEnvelope(85400, 446900, 85600, 447100, 7415),
        envelope
    );

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
    sg.geometry,
    *
FROM
    bag_3dcitydb.cityobject co
    JOIN bag_3dcitydb.building b ON co.id = b.id
    JOIN bag_3dcitydb.surface_geometry sg ON b.lod1_solid_id = sg.id
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
    geometry :: jsonb @ > '[{"lod": 1.2}]' :: jsonb
ORDER BY
    id ASC;

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