# cjdb

[![MIT badge](https://img.shields.io/pypi/l/cjdb)](../LICENSE) &nbsp; [![PyPI](https://img.shields.io/pypi/v/cjdb)](https://pypi.org/project/cjdb)

`cjdb` is a Python based importer of CityJSONL files to a PostgreSQL database. It requires [PostGIS](https://postgis.net/) extension for geometry types.

## Table of Contents  
### [1. CLI Usage](#usage)
- [CLI instructions](#instructions)
- [Quickstart example](#quickstart)

### [2. cjdb explanations](#explanation)
 - [Model assumptions](#model)
 - [What is a City Model?](#citymodel)
 - [Types of input](#input)
 - [Coordinate Reference Systems](#crs)
 - [3D reprojections](#3d)
 - [CityJSON Extensions](#extensions)
 - [CityJSON GeometryTemplate](#geomtemplate)
 - [Data validation](#validation)
 - [Repeated object IDs](#repeated)

---------------------------------

## 1. CLI usage <a name="usage"></a>
---
### CLI instructions: <a name="instructions"></a>

usage: 

```bash
cj2pgsql [-h] [-H DB_HOST] [-p DB_PORT] -U DB_USER [-W DB_PASSWORD] -d DB_NAME [-s DB_SCHEMA] [-I TARGET_SRID][-x INDEXED_ATTRIBUTES] [-px PARTIAL_INDEXED_ATTRIBUTES] [-g] [-a | -o] [-e | -u] [file_or_directory]
```
#### Positional Arguments
file_or_directory
Source CityJSONL file or a directory with CityJSONL files. STDIN if not specified. If specifying a directory, all the *.jsonl files inside of it will be imported.

Default: “stdin”

#### Named Arguments
-I, --srid
Target coordinate system SRID. All 3D and 2D geometries will be reprojected.

-x, --attr-index
CityObject attribute to be indexed using a btree index. Can be specified multiple times, for each attribute once.

Default: []

-px, --partial-attr-index
CityObject attribute to be indexed using a btree partial index. Can be specified multiple times, for each attribute once. This index indexes on a condition ‘where {
                {ATTR_NAME
                }
        } is not null’. This means that it saves space and improves query performance when the attribute is not present for all imported CityObjects.

Default: []

-g, --ignore-repeated-file
Ignore repeated file names warning when importing. By default, the importer will send out warnings if a specific file has already been imported.

Default: False

-a, --append
Run in append mode (as opposed to default create mode). This assumes the database structure exists already and new data is to be appended.

Default: False

-o, --overwrite
Overwrite the data that is currently in the database schema. Warning: this causes the loss of what was imported before to the database schema.

Default: False

-u, --update-existing
Check if the object with given ID exists before inserting, and update it if it does. The old object will be updated with the new object’s properties.

Default: False

#### Database connection arguments
-H, --host
PostgreSQL database host

Default: “localhost”

-p, --port
PostgreSQL database port

Default: 5432

-U, --user
PostgreSQL database user name

-W, --password
PostgreSQL database user password

-d, --database
PostgreSQL database name

-s, --schema
Target database schema

Default: “public”

### Quickstart example <a name="quickstart"></a>
Sample CityJSON data can be downloaded from [3DBAG download service](https://3dbag.nl/nl/download?tid=901).

Then, having the CityJSON file, a combination of [cjio](https://github.com/cityjson/cjio) (external CityJSON processing library) and cjdb is needed to import it to a specified schema in a database.

1. Convert CityJSON to CityJSONL

```
cjio --suppress_msg tile_901.json export jsonl stdout > tile_901.jsonl 
```

2. Import CityJSONL to the database
```
PGPASSWORD=postgres cjdb -H localhost -U postgres -d postgres -s cjdb -o tile_901.jsonl   
```

**Alternatively steps 1 and 2 in a single command:**

```
cjio --suppress_msg tile_901.json export jsonl stdout | cjdb -H localhost -U postgres -d postgres -s cjdb -o
```

The metadata and the objects can then be found in the tables in the specified schema (`cjdb` in this example).


Password can be specified in the `PGPASSWORD` environment variable. If not specified, the app will prompt for the password.


## 2. cjdb explanations <a name="explanation"></a>
---
### Model assumptions <a name="model"></a>
The `cjdb` importer loads the data in accordance with a specific data model.

Model documentation:
 [model/README](model/README.md)

#### Indexes
Some indexes are created by default (refer to [model/README](model/README.md)).

Additionally, the user can specify which CityObject attributes are to be indexed with the `-x/--attr-index` or `-px/--partial-attr-index` flag. The second option uses a partial index with a `not null` condition on the attribute. This saves disk space when indexing an attribute that is not present among all the imported CityObjects. This is often the case with CityJSON, because in a single dataset there can be different object types, with different attributes.

### What is a City Model? How to organize CityJSON data from various sources? <a name="citymodel"></a>

The definition and scope of the City Model are for the user to decide. It is recommended to group together semantically coherent objects, by importing them to the same database schema.

While the static table structure (columns don't change) does support loading any type of CityJSON objects together, the data becomes harder to manage for the user. Example of this would be having different attributes for the same CityObject type (which should be consistent for data coming from the same source).

### Types of input <a name="input"></a>
The importer works only on *CityJSONL* files.
Instructions on how to obtain such a file from a *CityJSON* file: https://cjio.readthedocs.io/en/latest/includeme.html#stdin-and-stdout


The importer supports 3 kinds of input:
- a single CityJSONL file
- a directory of CityJSONL files (all files with *jsonl* extensions are located and imported)
- STDIN using the pipe operator:
```
cat file.jsonl | cjdb ...
```

### Coordinate Reference Systems <a name="crs"></a>
The `cjdb` importer does not allow inconsistent CRS (coordinate reference systems) within the same database schema. For storing data in separate CRS using multiple schemas is required.

The data needs to be either harmonized beforehand, or the `-I/--srid` flag can be used upon import, to reproject all the geometries to the one specified CRS. Specifying a 2D CRS (instead of a 3D one) will cause the Z-coordinates to remain unchanged.

**Note:** reprojections slow down the import significantly.

**Note:** Source data with missing `"metadata"/"referenceSystem"` cannot be reprojected due to unknown source reference system.

### 3D reprojections <a name="3d"></a>
`Pyproj` is used for CRS reprojections. It supports 3D CRS transformations between different systems. However, sometimes downloading additional [grids](https://pyproj4.github.io/pyproj/stable/transformation_grids.html) is required. The importer will attempt to download the grids needed for the reprojection, with the following message:
```
Attempting to download additional grids required for CRS transformation.
This can also be done manually, and the files should be put in this folder:
        {pyproj_directory}
```

If that fails, the user will have to download the required grids and put them in the printed `{pyproj_directory}` themselves. 


### CityJSON Extensions <a name="extensions"></a>
If [CityJSON Extensions](https://www.cityjson.org/extensions/) were present in the imported file, they can be found listed in the `extensions` column in the `import_meta` table.

The [CityJSON specifications](https://www.cityjson.org/specs/1.1.2/#extensions) mention 3 different extendable features, and the `cjdb` importer deals with them as follows:

1. Complex attributes

No action is taken. These attributes end up in the `attributes` JSONB column.

2. Additional root properties

Additional root properties are placed in the `extra properties` JSONB column in the `import_meta` table.

3. Additional CityObject type

Additional CityObject types are appended to the list of allowed CityJSON objects.

### CityJSON GeometryTemplates <a name="geomtemplate"></a>
[Geometry templates](https://www.cityjson.org/specs/1.1.2/#geometry-templates)
are resolved for each object geometry, so that the object in the table ends up with its real-world coordinates (instead of vertex references or relative template coordinates).

### Data validation <a name="validation"></a>
The importer does not validate the structure of the file. It is assumed that the input file is schema-valid ([CityJSON validator](https://validator.cityjson.org/)).
It sends out warnings when:
- there appear CityObject types defined neither in the main CityJSON specification nor any of the supplied extensions. 
- the specified target CRS does not have the Z-axis defined
- the source dataset does not have a CRS defined at all

### Repeated object IDs <a name="repeated"></a>
By default, the importer does not check if an object with a given ID exists already in the database. This is because such an operation for every inserted object results in a performance penalty.

The user can choose to run the import with either the `-e/--skip-existing` option to skip existing objects or `-u, --update-existing` to update existing objects. This will slow down the import, but it will also ensure that repeated object cases are handled.



