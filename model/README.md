# cjdb data model
cjdb data model is designed to store cityJSON files in a Postgres database.

## Table of Contents
### [1. Overview](#overview)

### [2. Table Structure](#table_structure)

### [3. Indexing](#family)
 
## 1. Overview

## 2. Table Structure <a name="table structure"></a>

The conceptual data model contains two main tables. The **import_meta** table for storing imported files' information, e.g. name or metadata of the source file. The **cj_object** table for storing city objects. 

![UML data model](https://user-images.githubusercontent.com/92783160/198852049-1fa78a6b-734a-46ec-aa38-9c0a4eb9b794.png)

The physical data model adds one more table on the conceptual data model: the **family** table to store relations between city objects, e.g the parent-children relationship. This table is added because it improves certain operation performances. 

![2 Physical Model_Lan_Oct29](https://user-images.githubusercontent.com/92783160/198853247-ac5103c3-e221-4a5a-b9dc-d3505f8747bb.png)

### 1. import_meta <a name="import_meta"></a>

The import_meta table stores information from imported files, e.g. name or metadata of the source file. Belowing section describes its attributes.

<**id**: import_meta record's index within the database.<br/>
**source_file**: name of the source file.<br/>
**version**: cityJSON version used.<br/>
**metadata**: [cityJSON metadata object](https://www.cityjson.org/specs/1.1.2/#metadata), a JSON object describing the creator, dataset extent or coordinate reference system used, etc.<br/>
**transform**:[cityJSON transform object](https://www.cityjson.org/specs/1.1.2/#transform-object), a JSON object describing how to decompress the integer coordinates of the geometries to obtain real-world coordinates.<br/>
**geometry_templates**: [cityJSON geometry-templates object](https://www.cityjson.org/specs/1.1.2/#geometry-templates), a JSON object containing the templates that can be reused by different City Objects (usually for trees).<br/>
**srid**: Coordinate reference system (CRS) of the imported city objects in the database. If not specified when importing, the CRS will be the same with the source file's CRS. If specified when importing, the CRS will be the specified CRS.<br/>
**extensions**: [cityJSON Extensions](https://www.cityjson.org/specs/1.1.2/#extensions), a JSON file that documents how the core data model of CityJSON is extended.<br/>
**extra_properties**: [extraRootProperties](https://www.cityjson.org/specs/1.1.2/#case-2-adding-new-properties-at-the-root-of-a-document), a JSON object with added new properties at the root of the imported document.<br/>
**started_at**: importing start time.<br/>
**finished_at**: importing finish time.<br/>
**Bounding box**: bounding box of the input file's geographic extent is calculated and stored as one geometry attribute.

### 2. cj_object <a name="cj_object"></a>

The cj_object model stores individual city objects, for instance buildings, roads, or bridges. Its attributes are described below.

**id**: city object's index within the database.<br/>
**import_meta_id**: the source file id of the city object, foriegn key to the id column of import_meta table.<br/>
**object_id**: the identification string of the city object (e.g. NL.IMBAG.Pand.0503100000000033-0).<br/>
**type**: type of the city object (e.g. building, buildingparts, etc.).<br/>
**attributes**:[cityJSON attributes](https://www.cityjson.org/specs/1.1.2/#attributes-for-all-city-objects), a JSON object that describes attributes of the city object (e.g. roof type, area, etc.).<br/>
**geometry**: [cityJSON geometry](https://www.cityjson.org/specs/1.1.2/#geometry-objects), a JSON object that describes the geometry of the city object.<br/>
**bbox**: bounding box of the city object, in geometry type.<br/>
**ground_geometry**: ground geometry of the city object, in geometry type.<br/>

### 3. Family <a name="family"></a>
The family model stores the relations between city objects.

**id**: family object's index within the database.<br/>
**parent_id**: the identification id of the parent object.<br/>
**child_id**: the identification id of the child object.<br/>

## 3. Indexing

Indexing certain attributes in the tables can potentially speed up database operations. 

The users can use GIN index on lod, to speed up queries on geometries:

CREATE INDEX lod ON cjdb.cj_object USING GIN (geometry jsonb_path_ops);

The users can use B-tree partial index on attributes, to speed up queries on attributes:

CREATE INDEX bouwjaar2 ON cjdb.cj_object USING BTREE

## 4. Clustering

