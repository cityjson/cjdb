# cjdb data model
cjdb data model is designed to store CityJSONL files in a Postgres database.

## Table of Contents
### [1. Overview](#overview)

### [2. Table Structure](#table_structure)
 - [import_meta](#import_meta)
 - [cj_object](#cj_object)
 - [Family](#family)

### [3. Indexing](#Indexing)

 
## 1. Overview <a name="overview"></a>

After reading the readme, the user will:

1) Understand the table structure of cjdb model.

2) Understand the indexing possiblities within the database, and their effects on operations.

## 2. Table Structure <a name="table_structure"></a>

The conceptual data model contains two main tables. The **import_meta** table for storing imported files' information, e.g. name or metadata of the source file. The **cj_object** table for storing city objects. 

![UML drawio](https://user-images.githubusercontent.com/92783160/200633172-e33fc6ae-26b4-4b16-a2a7-968cc9a34d5e.png)


The physical data model adds one more table on the conceptual data model: the **family** table to store relations between city objects, e.g the parent-children relationship. This table is added to achieve higher querying speed when selecting objects by their parent/child relationship. Example of this would be: "give me all the objects which are children of X". 


![Physical Model drawio (3)](https://user-images.githubusercontent.com/92783160/200633220-92f95184-edce-44b9-bfa9-7db5fccbfc0e.png)


### 1. import_meta <a name="import_meta"></a>

The import_meta table stores information from imported files, e.g. name or metadata of the source file. Belowing section describes its attributes.

<**id**: import_meta record's index within the database.<br/>
**source_file**: name of the source file.<br/>
**version**: cityJSON version used.<br/>
**metadata**: [cityJSON metadata object](https://www.cityjson.org/specs/#metadata), a JSON object describing the creator, dataset extent or coordinate reference system used, etc.<br/>
**transform**:[cityJSON transform object](https://www.cityjson.org/specs/#transform-object), a JSON object describing how to decompress the integer coordinates of the geometries to obtain real-world coordinates.<br/>
**geometry_templates**: [cityJSON geometry-templates object](https://www.cityjson.org/specs/#geometry-templates), a JSON object containing the templates that can be reused by different City Objects (usually for trees).<br/>
**srid**: Coordinate reference system (CRS) of the imported city objects in the database. If not specified when importing, the CRS will be the same with the source file's CRS. If specified when importing, the CRS will be the specified CRS.<br/>
**extensions**: [cityJSON Extensions](https://www.cityjson.org/specs/#extensions), a JSON file that documents how the core data model of CityJSON is extended.<br/>
**extra_properties**: [extraRootProperties](https://www.cityjson.org/specs/#case-2-adding-new-properties-at-the-root-of-a-document), a JSON object with added new properties at the root of the imported document.<br/>
**started_at**: importing start time.<br/>
**finished_at**: importing finish time. `null` if not finished.<br/>
**Bounding box**: bounding box is taken from the `geographicExtent` object from the `metadata` section

### 2. cj_object <a name="cj_object"></a>

The cj_object model stores individual city objects, for instance buildings, roads, or bridges. Its attributes are described below. The **attributes** and **geometry** are seperated into two jsonb column for query optimization purpose.

**id**: city object's index within the database.<br/>
**import_meta_id**: the source file id of the city object, foriegn key to the id column of import_meta table.<br/>
**object_id**: the identification string of the city object (e.g. NL.IMBAG.Pand.0503100000000033-0).<br/>
**type**: type of the city object (e.g. building, buildingparts, etc.).<br/>
**attributes**:[cityJSON attributes](https://www.cityjson.org/specs/#attributes-for-all-city-objects), a JSON object that describes attributes of the city object (e.g. roof type, area, etc.).<br/>
**geometry**: [cityJSON geometry](https://www.cityjson.org/specs/#geometry-objects), a JSON object that describes the geometry of the city object.<br/>
**ground_geometry**: ground geometry of the city object, in geometry type.<br/>

### 3. Family <a name="family"></a>
The family model stores the relations between city objects.

**id**: family object's index within the database.<br/>
**parent_id**: the identification id of the parent object.<br/>
**child_id**: the identification id of the child object.<br/>

## 3. Indexing

Indexing certain columns or [expressions](https://www.postgresql.org/docs/current/indexes-expressional.html) speeds up querying on them. 

The users can use GIN index on lod, to speed up queries on geometries:

CREATE INDEX lod ON cjdb.cj_object USING GIN (geometry jsonb_path_ops);

The users can use B-tree partial index on attributes. It will slightly increase the query speed.


