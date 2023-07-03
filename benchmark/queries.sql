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
        'bag_3dcitydb',
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
    bag_3dcitydb.cityobject co
    JOIN bag_3dcitydb.cityobject_genericattrib coga ON co.id = coga.cityobject_id
WHERE
    coga.attrname = 'h_dak_max'
    AND coga.realval > 20;

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
-- 3DCityDB
EXPLAIN ANALYZE
SELECT
    gmlid
FROM
    vienna_3dcitydb.cityobject co
    JOIN vienna_3dcitydb.cityobject_genericattrib coga ON co.id = coga.cityobject_id
WHERE
    coga.attrname = 'HoeheDach'
    AND coga.strval :: float > 20;

-- CJDB: 
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
EXPLAIN ANALYZE
SELECT
    c.gmlid,
    sg.geometry
FROM
    vienna_3dcitydb.thematic_surface AS ts
    LEFT JOIN vienna_3dcitydb.surface_geometry AS sg ON ts.lod2_multi_surface_id = sg.parent_id
    LEFT JOIN vienna_3dcitydb.cityobject AS c ON ts.building_id = c.id
WHERE
    ST_Contains(
        ST_MakeEnvelope(
            1305.187,
            340920.83400000003,
            1505.187,
            341120.83400000003,
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
    vienna_cjdb.city_object
WHERE
    ST_Contains(
        ST_MakeEnvelope(
            1305.187,
            340920.83400000003,
            1505.187,
            341120.83400000003,
            4585
        ),
        ground_geometry
    );

----------------------------------------------------------------------------------------------------------------
--------------------------------------------3. Query building on point ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
--3A: BAG
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
    sg.geometry & & st_setsrid(ST_MakePoint(85200, 446900), 7415)
    AND ts.objectclass_id = 35;

-- CJDB :
EXPLAIN ANALYZE
SELECT
    object_id,
    ground_geometry
FROM
    bag_cjdb.city_object
WHERE
    TYPE = 'Building'
    AND ground_geometry & & st_setsrid(ST_MakePoint(85200, 446900), 7415);

--3B: BAG
--3C: BAG
----------------------------------------------------------------------------------------------------------------
--------------------------------------------4. Query the number of parts for each building ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 4A: BAG
-- 3DcityBAG: 
EXPLAIN ANALYZE
SELECT
    cj.gmlid,
    count(b.id)
FROM
    bag_3dcitydb.cityobject cj
    LEFT JOIN bag_3dcitydb.building b ON cj.id = b.building_parent_id
WHERE
    cj.objectclass_id = 26
GROUP BY
    cj.id;

-- CJDB: 
EXPLAIN ANALYZE
SELECT
    co.object_id,
    COUNT(cor.child_id)
FROM
    bag_cjdb.city_object co
    LEFT JOIN bag_cjdb.city_object_relationships cor ON co.id = cor.parent_id
WHERE
    co.type = 'Building'
GROUP BY
    co.object_id;

-- 4B: NYC
-- 3DcityBAG   
EXPLAIN ANALYZE
SELECT
    cj.gmlid,
    count(b.id)
FROM
    ny_3dcitydb.cityobject cj
    LEFT JOIN ny_3dcitydb.building b ON cj.id = b.building_parent_id
WHERE
    cj.objectclass_id = 26
GROUP BY
    cj.id;

-- CJDB
EXPLAIN ANALYZE
SELECT
    co.object_id,
    COUNT(cor.child_id)
FROM
    ny_cjdb.city_object co
    LEFT JOIN ny_cjdb.city_object_relationships cor ON co.id = cor.parent_id
WHERE
    co.type = 'Building'
GROUP BY
    co.object_id;

-- 4C: Vienna
-- 3DcityBAG      
EXPLAIN ANALYZE
SELECT
    cj.gmlid,
    count(b.id)
FROM
    vienna_3dcitydb.cityobject cj
    LEFT JOIN vienna_3dcitydb.building b ON cj.id = b.building_parent_id
WHERE
    cj.objectclass_id = 26
GROUP BY
    cj.id;

-- CJDB
EXPLAIN ANALYZE
SELECT
    co.object_id,
    COUNT(cor.child_id)
FROM
    vienna_cjdb.city_object co
    LEFT JOIN vienna_cjdb.city_object_relationships cor ON co.id = cor.parent_id
WHERE
    co.type = 'Building'
GROUP BY
    co.object_id;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------5. Query all buildings by LOD ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 5A: BAG
-- 3DcityDB :
EXPLAIN ANALYZE
SELECT
    co.gmlid
FROM
    bag_3dcitydb.cityobject co
    JOIN bag_3dcitydb.building b ON co.id = b.id
WHERE
    b.lod1_solid_id IS NOT NULL;

-- CJDB:
EXPLAIN ANALYZE
SELECT
    object_id
FROM
    bag_cjdb.city_object
WHERE
    geometry :: jsonb @ > '[{"lod": 1.2}]' :: jsonb;

-- 5B: NYC
EXPLAIN ANALYZE
SELECT
    co.gmlid
FROM
    ny_3dcitydb.cityobject co
    JOIN bag_3dcitydb.building b ON co.id = b.id
WHERE
    b.lod1_solid_id IS NOT NULL;

-- CJDB:
EXPLAIN ANALYZE
SELECT
    object_id
FROM
    ny_cjdb.city_object
WHERE
    geometry :: jsonb @ > '[{"lod": "2"}]' :: jsonb;

-- 5C: Vienna
EXPLAIN ANALYZE
SELECT
    co.gmlid
FROM
    vienna_3dcitydb.cityobject co
    JOIN bag_3dcitydb.building b ON co.id = b.id
WHERE
    b.lod1_solid_id IS NOT NULL;

-- CJDB:
EXPLAIN ANALYZE
SELECT
    object_id
FROM
    vienna_cjdb.city_object
WHERE
    geometry :: jsonb @ > '[{"lod": "2"}]' :: jsonb;

----------------------------------------------------------------------------------------------------------------
--------------------------------------------6. INSERT new attribute  ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 6A: BAG
-- 3DcityDB
EXPLAIN ANALYZE
INSERT INTO
    bag_3dcitydb.cityobject_genericattrib (attrname, datatype, realval, cityobject_id)
SELECT
    'footprint_area',
    3,
    ST_Area(cityobject.envelope),
    cityobject.id
FROM
    bag_3dcitydb.cityobject
WHERE
    cityobject.objectclass_id = 26;

--cjdb
EXPLAIN ANALYZE
UPDATE
    bag_cjdb.city_object
SET
    attributes = jsonb_set(
        attributes :: jsonb,
        '{footprint_area}',
        to_jsonb(ST_Area(ground_geometry))
    ) :: json
WHERE
    TYPE = 'Building';

-- 6B: NYC
-- 3DcityDB
EXPLAIN ANALYZE
INSERT INTO
    ny_3dcitydb.cityobject_genericattrib (attrname, datatype, realval, cityobject_id)
SELECT
    'footprint_area',
    3,
    ST_Area(cityobject.envelope),
    cityobject.id
FROM
    ny_3dcitydb.cityobject
WHERE
    cityobject.objectclass_id = 26;

--cjdb
EXPLAIN ANALYZE
UPDATE
    ny_cjdb.city_object
SET
    attributes = jsonb_set(
        attributes :: jsonb,
        '{footprint_area}',
        to_jsonb(ST_Area(ground_geometry))
    ) :: json
WHERE
    TYPE = 'Building';

-- 6C: VIENAA
-- 3DcityDB
EXPLAIN ANALYZE
INSERT INTO
    vienna_3dcitydb.cityobject_genericattrib (attrname, datatype, realval, cityobject_id)
SELECT
    'footprint_area',
    3,
    ST_Area(cityobject.envelope),
    cityobject.id
FROM
    vienna_3dcitydb.cityobject
WHERE
    cityobject.objectclass_id = 26;

--cjdb
EXPLAIN ANALYZE
UPDATE
    vienna_cjdb.city_object
SET
    attributes = jsonb_set(
        attributes :: jsonb,
        '{footprint_area}',
        to_jsonb(ST_Area(ground_geometry))
    ) :: json
WHERE
    TYPE = 'Building';

----------------------------------------------------------------------------------------------------------------
--------------------------------------------7. UPDATE attribute  ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 7A: BAG
-- 3DcityDB
EXPLAIN ANALYZE
UPDATE
    bag_3dcitydb.cityobject_genericattrib
SET
    realval = realval + 10
WHERE
    attrname = 'footprint_area';

--CJDB:
EXPLAIN ANALYZE
UPDATE
    bag_cjdb.city_object
SET
    attributes = jsonb_set(
        attributes :: jsonb,
        '{footprint_area}',
        to_jsonb(
            CAST (
                jsonb_path_query_first(
                    attributes :: jsonb,
                    '$.footprint_area'
                ) AS real
            ) + 10.0
        )
    ) :: json
WHERE
    TYPE = 'Building';

-- 7B: NY
-- 3DcityDB
EXPLAIN ANALYZE
UPDATE
    ny_3dcitydb.cityobject_genericattrib
SET
    realval = realval + 10
WHERE
    attrname = 'footprint_area';

--CJDB:
EXPLAIN ANALYZE
UPDATE
    ny_cjdb.city_object
SET
    attributes = jsonb_set(
        attributes :: jsonb,
        '{footprint_area}',
        to_jsonb(
            CAST (
                jsonb_path_query_first(
                    attributes :: jsonb,
                    '$.footprint_area'
                ) AS real
            ) + 10.0
        )
    ) :: json
WHERE
    TYPE = 'Building';

-- 7C: Vienna
-- 3DcityDB
EXPLAIN ANALYZE
UPDATE
    vienna_3dcitydb.cityobject_genericattrib
SET
    realval = realval + 10
WHERE
    attrname = 'footprint_area';

--CJDB:
EXPLAIN ANALYZE
UPDATE
    vienna_cjdb.city_object
SET
    attributes = jsonb_set(
        attributes :: jsonb,
        '{footprint_area}',
        to_jsonb(
            CAST (
                jsonb_path_query_first(
                    attributes :: jsonb,
                    '$.footprint_area'
                ) AS real
            ) + 10.0
        )
    ) :: json
WHERE
    TYPE = 'Building';

----------------------------------------------------------------------------------------------------------------
--------------------------------------------8. Delete attribute  ----------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
-- 8A: BAG
-- 3DcityDB
EXPLAIN ANALYZE
DELETE FROM
    bag_3dcitydb.cityobject_genericattrib
WHERE
    attrname = 'footprint_area';

--CJDB   
EXPLAIN ANALYZE
UPDATE
    bag_cjdb.city_object
SET
    attributes = jsonb_set_lax(
        attributes :: jsonb,
        '{footprint_area}',
        NULL,
        TRUE,
        'delete_key'
    ) :: json
WHERE
    TYPE = 'Building';

-- 8B: NY
-- 3DcityDB
EXPLAIN ANALYZE
DELETE FROM
    ny_3dcitydb.cityobject_genericattrib
WHERE
    attrname = 'footprint_area';

--CJDB   
EXPLAIN ANALYZE
UPDATE
    ny_cjdb.city_object
SET
    attributes = jsonb_set_lax(
        attributes :: jsonb,
        '{footprint_area}',
        NULL,
        TRUE,
        'delete_key'
    ) :: json
WHERE
    TYPE = 'Building';

-- 8C: Vienna
-- 3DcityDB
EXPLAIN ANALYZE
DELETE FROM
    vienna_3dcitydb.cityobject_genericattrib
WHERE
    attrname = 'footprint_area';

--CJDB   
EXPLAIN ANALYZE
UPDATE
    vienna_cjdb.city_object
SET
    attributes = jsonb_set_lax(
        attributes :: jsonb,
        '{footprint_area}',
        NULL,
        TRUE,
        'delete_key'
    ) :: json
WHERE
    TYPE = 'Building';