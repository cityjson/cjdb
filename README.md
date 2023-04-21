# cjdb
[![MIT badge](https://img.shields.io/pypi/l/cjdb)](LICENSE) &nbsp; [![PyPI](https://img.shields.io/pypi/v/cjdb)](https://pypi.org/project/cjdb)

`cjdb` is a Python based importer of CityJSONL files to a PostgreSQL database. It requires the [PostGIS](https://postgis.net/) extension.

Authors: Cynthia Cai, Lan Yan, Yitong Xia, Chris Poon, Siebren Meines, Leon Powalka

Maintainer: Gina Stavropoulou

## Table of Contents  
### [1.Data model](#1-data-model)
### [2.Installation](#2-installation)
- [Using pip](#using-pip)
- [Using Docker](#using-docker)
### [3.Usage](#3-usage)
- [CLI](#cli)
- [Quickstart](#quickstart)
- [Basic Queries](#basic-queries)
### [4.Local development](#4-local-development)
- [Install and Build](#install-and-build)
- [Testing](#testing)
### [5.Explanation](#5-explanation)
 - [Model assumptions](#model-assumptions)
 - [What is a City Model?](#what-is-a-city-model)
 - [Types of input](#types-of-input)
 - [Coordinate Reference Systems](#coordinate-reference-systems)
 - [3D reprojections](#3d-reprojections)
 - [CityJSON Extensions](#cityjson-extensions)
 - [CityJSON GeometryTemplate](#cityjson-geometrytemplate)
 - [Data validation](#data-validation)
 - [Repeated object IDs](#repeated-object-ids)
---
## 1. Data model
For the underlying data model see [cjdb/model/README.md](cjdb/model/README.md)


## 2. Installation
### Using pip
```bash
pip install cjdb
```
It is recommended to install it in an isolated environment, because of fragile external library dependencies for CQL filter parsing.

### Using docker
Build:
```bash
docker build -t cjdb:latest .
```

Run:
```bash
docker run --rm -it cjdb cjdb --help
```

To import some files, the `-v` option is needed to mount our local file directory in the container:
```bash
docker run -v {MYDIRECTORY}:/data --rm -it --network=host cjdb cjdb -H localhost -U postgres -d postgres -W postgres /data/5870_ext.jsonl 
```
## 3. Usage <a name="usage"></a>

### CLI <a name="cli"></a>

```bash
cj2pgsql [-h] [-H DB_HOST] [-p DB_PORT] -U DB_USER [-W DB_PASSWORD] -d DB_NAME [-s DB_SCHEMA] [-I TARGET_SRID][-x INDEXED_ATTRIBUTES] [-px PARTIAL_INDEXED_ATTRIBUTES] [-g] [-a | -o] [-e | -u] [file_or_directory]
```
#### Positional Arguments
file_or_directory
Source CityJSONL file or a directory with CityJSONL files. STDIN if not specified. If specifying a directory, all the *.jsonl files inside of it will be imported.

Default: “stdin”

#### Named Arguments
`-I, --srid`
Target coordinate system SRID. All 3D and 2D geometries will be reprojected.

`-x, --attr-index`
CityObject attribute to be indexed using a btree index. Can be specified multiple times, for each attribute once.

Default: []

`-px, --partial-attr-index`
CityObject attribute to be indexed using a btree partial index. Can be specified multiple times, for each attribute once. This index indexes on a condition ‘where {
                {ATTR_NAME
                }
        } is not null’. This means that it saves space and improves query performance when the attribute is not present for all imported CityObjects.

Default: []

`-g, --ignore-repeated-file`
Ignore repeated file names warning when importing. By default, the importer will send out warnings if a specific file has already been imported.

Default: False

`-a, --append`
Run in append mode (as opposed to default create mode). This assumes the database structure exists already and new data is to be appended.

Default: False

`-o, --overwrite`
Overwrite the data that is currently in the database schema. Warning: this causes the loss of what was imported before to the database schema.

Default: False

`-u, --update-existing`
Check if the object with given ID exists before inserting, and update it if it does. The old object will be updated with the new object’s properties.

Default: False

#### Database connection arguments
`-H, --host`
PostgreSQL database host

Default: “localhost”

`-p, --port`
PostgreSQL database port

Default: 5432

`-U, --user`
PostgreSQL database user name

`-W, --password`
PostgreSQL database user password

`-d, --database`
PostgreSQL database name

`-s, --schema`
Target database schema

Default: “public”

### Quickstart

Sample CityJSON data can be downloaded from [3DBAG download service](https://3dbag.nl/nl/download?tid=901). Then, having the CityJSON file, a combination of [cjio](https://github.com/cityjson/cjio) (external CityJSON processing library) and cjdb is needed to import it to a specified schema in a database. 

1. Convert CityJSON to CityJSONL

```bash
cjio --suppress_msg tile_901.json export jsonl tile_901.jsonl 
```

2. Create a new database

  - [how to create a new database](https://postgis.net/workshops/postgis-intro/creating_db.html)

3. Import CityJSONL to the database
```bash
PGPASSWORD=postgres cjdb -H localhost -U postgres -d postgres -s cjdb -o tile_901.jsonl   
```

**Alternatively steps 1 and 2 in a single command:**

```bash
cjio --suppress_msg tile_901.json export jsonl stdout | cjdb -H localhost -U postgres -d postgres -s cjdb -o
```

The metadata and the objects can then be found in the tables in the specified schema (`cjdb` in this example).


Password can be specified in the `PGPASSWORD` environment variable. If not specified, the app will prompt for the password.


### Basic Queries

- Query an object with a specific id:
```SQL
SELECT * FROM cjdb.cj_object
WHERE object_id = 'NL.IMBAG.Pand.0503100000000334';
```

- Query a building with a specific child
```SQL
SELECT o.* FROM cjdb.family f
INNER JOIN cjdb.cj_object o ON o.object_id = f.parent_id
WHERE f.child_id = 'NL.IMBAG.Pand.0503100000000334-0'
```

- Query all buildings within a bounding box
```SQL
SELECT * FROM cjdb.cj_object
WHERE type = 'Building'
AND ST_Contains(ST_MakeEnvelope(81900.00, 446850.00, 81930.00, 446900.00, 7415), ground_geometry)
ORDER BY id ASC;
```

- Query the building intersecting with a point
```SQL
SELECT * FROM cjdb.cj_object
WHERE ground_geometry && ST_MakePoint(81915.00, 446850.00)
AND type = 'Building'
ORDER BY object_id ASC;
```

- Query all objects with a slanted roof
```SQL
SELECT * FROM cjdb.cj_object
WHERE (attributes->'dak_type')::varchar = '"slanted"'
ORDER BY id ASC;
```

- Query all the buildings made after 2000:
```SQL
SELECT * FROM cjdb.cj_object
WHERE (attributes->'oorspronkelijkbouwjaar')::int > 2000
AND type = 'Building'
ORDER BY id ASC;
```

- Query all objects with LOD 1.2

```SQL
SELECT * FROM cjdb.cj_object
WHERE geometry::jsonb @> '[{"lod": 1.2}]'::jsonb
```

## 4. Local development

### Install and Build
Make sure [poetry](https://python-poetry.org/docs/) is installed and the [creation of virtual environments within the project is allowed](
https://python-poetry.org/docs/configuration/#virtualenvsin-project):

```
poetry config virtualenvs.in-project true
```

Then, to create a local environment with all the necessary dependencies, run from the repository root:
```bash
poetry install
```

To activate the env:
```bash
source .venv/bin/activate 
```

Then you can run the CLI command:
```bash
cjdb --help
```

Every time you make some changed to the package you can run `poetry install` to reinstall.


### Testing
In onder to run the tests you need to have [PostgreSQL](https://www.postgresql.org/download/) installed. Then you can run:

```bash
pytest -v
```

## 5. Explanation
---
### Model assumptions
The `cjdb` importer loads the data in accordance with a specific data model.

Model documentation:
 [model/README](model/README.md)

#### Indexes
Some indexes are created by default (refer to [model/README](model/README.md)).

Additionally, the user can specify which CityObject attributes are to be indexed with the `-x/--attr-index` or `-px/--partial-attr-index` flag, we recommend doing this if several queries are made on specific attributes. 
The second option uses a partial index with a `not null` condition on the attribute. This saves disk space when indexing an attribute that is not present among all the imported CityObjects. 
This is often the case with CityJSON, because in a single dataset there can be different object types, with different attributes.


### Structuring the database and its schemas

It is recommended to group together semantically coherent objects, by importing them to the same database schema.
One database can have different schemas.

While the current data model supports the import of any type of CityJSON objects together (`Building` and `SolitaryVegetationObject`), the data becomes harder to manage for the user. 
Example of this would be having different attributes for the same CityObject type (which should be consistent for data coming from the same source).


### Input == CityJSONFeature
The importer works only on [*CityJSONL* files](https://www.cityjson.org/specs/#text-sequences-and-streaming-with-cityjsonfeature), that is where a CityJSON file is decomposed into its *features* (`CityJSONFeature`).

The easiest way to create these from a CityJSON file is with [cjio](https://github.com/cityjson/cjio), and to follow [those instructions](https://github.com/cityjson/cjio#stdin-and-stdout).

The importer supports 3 kinds of input:
  1. a single CityJSONL file (only those as the output of cjio currently work)
  1. a directory of CityJSONL files (all files with *jsonl* extensions are located and imported)
  1. STDIN using the pipe operator: `cat file.jsonl | cjdb ...`



### Coordinate Reference Systems
The `cjdb` importer does not allow inconsistent CRSs (coordinate reference systems) within the same database schema. For storing data in separate CRSs, you have to use different schemas.

The data needs to be either harmonized beforehand, or the `-I/--srid` flag can be used upon import, to reproject all the geometries to the one specified CRS. 
Specifying a 2D CRS (instead of a 3D one) will cause the Z-coordinates to remain unchanged.

**Note:** reprojections slow down the import significantly.

**Note:** Source data with missing `"metadata"/"referenceSystem"` cannot be reprojected due to unknown source reference system.


### 3D reprojections
[`pyproj`](https://pyproj4.github.io/pyproj/stable/) is used for CRS reprojections. 
While it supports 3D CRS transformations between different systems, sometimes downloading additional [grids](https://pyproj4.github.io/pyproj/stable/transformation_grids.html) is required. 
The importer will attempt to download the grids needed for the reprojection, with the following message:

```
Attempting to download additional grids required for CRS transformation.
This can also be done manually, and the files should be put in this folder:
        {pyproj_directory}
```

If that fails, the user will have to download the required grids and put them in the printed `{pyproj_directory}` themselves. 


### CityJSON Extensions
If [CityJSON Extensions](https://www.cityjson.org/extensions/) are present in the imported files, they can be found listed in the `extensions` column in the `import_meta` table.

The [CityJSON specifications](https://www.cityjson.org/specs/#extensions) mention 3 different extendable features, and the `cjdb` importer deals with them as follows:

1. Complex attributes

No action is taken. These attributes end up in the `attributes` JSONB column.

2. Additional root properties

Additional root properties are placed in the `extra properties` JSONB column in the `import_meta` table.

3. Additional CityObject type

Additional CityObject types are appended to the list of allowed CityJSON objects.

### CityJSON GeometryTemplate
[Geometry templates](https://www.cityjson.org/specs/1.1.2/#geometry-templates)
are resolved for each object geometry, so that the object in the table ends up with its real-world coordinates (instead of vertex references or relative template coordinates).

### Data validation
The importer does not validate the structure of the file. It is assumed that the input file is schema-valid ([CityJSON validator](https://validator.cityjson.org/)).
It sends out warnings when:
- there appear CityObject types defined neither in the main CityJSON specification nor any of the supplied extensions. 
- the specified target CRS does not have the Z-axis defined
- the source dataset does not have a CRS defined at all

### Repeated object IDs
By default, the importer does not check if an object with a given ID exists already in the database. This is because such an operation for every inserted object results in a performance penalty.

The user can choose to run the import with either the `-e/--skip-existing` option to skip existing objects or `-u, --update-existing` to update existing objects. This will slow down the import, but it will also ensure that repeated object cases are handled.




