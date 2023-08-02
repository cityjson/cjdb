# Basic Queries

## Query an object with a specific id:
```SQL
SELECT * FROM cjdb.city_object
WHERE object_id = 'NL.IMBAG.Pand.0503100000000010';
```

## Query a building with a specific child
```SQL
select * from cjdb.city_object p
inner join cjdb.city_object_relationships rel 
ON p.id = rel.parent_id
inner join cjdb.city_object c
ON c.id = rel.child_id
where c.object_id = 'NL.IMBAG.Pand.0503100000000010-0';
```

## Query all buildings within a bounding box
```SQL
SELECT * FROM cjdb.city_object
WHERE type = 'Building'
AND ST_Contains(ST_MakeEnvelope(85000.00, 446700.00, 85200.00, 446900.00, 7415), ground_geometry)
ORDER BY id ASC;
```

## Query the building intersecting with a point
```SQL
SELECT * FROM cjdb.city_object
WHERE ground_geometry && ST_MakePoint(85218.0, 446880.0)
AND type = 'Building'
ORDER BY object_id ASC;
```

## Query all objects with a slanted roof
```SQL
SELECT * FROM cjdb.city_object
WHERE (attributes->'b3_dak_type')::varchar = '"slanted"'
ORDER BY id ASC;
```

## Query all the buildings made after 2000:
```SQL
SELECT * FROM cjdb.city_object
WHERE (attributes->'oorspronkelijkbouwjaar')::int > 2000
AND type = 'Building'
ORDER BY id ASC;
```

## Query all objects with LOD 1.2

```SQL
SELECT * FROM cjdb.city_object
WHERE geometry::jsonb @> '[{"lod": "1.2"}]'::jsonb
```
