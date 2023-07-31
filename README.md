# cjdb
[![MIT badge](https://img.shields.io/pypi/l/cjdb)](LICENSE) &nbsp; [![PyPI](https://img.shields.io/pypi/v/cjdb)](https://pypi.org/project/cjdb)

`cjdb` is a Python-based importer/exporter of [CityJSONL files (CityJSON Lines)](https://www.cityjson.org/cityjsonl/) to and from a PostgreSQL database. 
It requires the [PostGIS](https://postgis.net/) extension.


## Installation
```bash
pip install cjdb
```
It is recommended to install it in an isolated environment.



## Usage

Check our [docs online](https://cityjson.github.io/cjdb/cjdb.html)  or

```bash
cjdb --help
```

## Quickstart

Sample CityJSON data can be downloaded from [3DBAG download service](https://3dbag.nl/). 
For example [download the tile "9-284-556"](https://data.3dbag.nl/cityjson/v20230622/tiles/9/284/556/9-284-556.city.json), where part of TU Delft is located.
Then, having the CityJSON file, a combination of [cjio](https://github.com/cityjson/cjio) (external CityJSON processing library) and cjdb is needed to import it to a specified schema in a database. 

1. Convert CityJSON to CityJSONL

```bash
cjio --suppress_msg 9-284-556.json export jsonl 9-284-556.jsonl 
```

2. Create a new database called "testcjdb"

If you installed PostgreSQL you should have the program 'createdb', so `createdb testcjdb`

Alternatively, you can use PgAdmin, [see how](https://postgis.net/workshops/postgis-intro/creating_db.html).

3. Import CityJSONL to the database in the schema "cjdb"
```bash
cjdb import -H localhost -U postgres -d testcjdb -s cjdb  9-284-556.jsonl
```

4. Export the whole database in a CityJSONL file: 
```bash
cjdb export -H localhost -U postgres -d testcjdb -s cjdb -o result.jsonl
```
or export only part of it, based on the Objects ids:

```bash
cjdb export -H localhost -U postgres -d testcjdb -s cjdb -o result.jsonl -q "SELECT 1 as id"
```

**Alternatively steps 1 and 3 in a single command:**

```bash
cjio --suppress_msg 9-284-556.json export jsonl stdout | cjdb import -H localhost -U postgres -d postgres -s cjdb
```

The metadata and the objects can then be found in the tables in the specified schema (`cjdb` in this example).


Password can be specified in the `PGPASSWORD` environment variable. If not specified, the app will prompt for the password.

## Local development

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

## Using docker
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
docker run -v {MYDIRECTORY}:/data --rm -it --network=host cjdb cjdb import -H localhost -U postgres -d postgres -W postgres /data/5870_ext.jsonl 
```

## Explanation
### Data model

The `cjdb` importer loads the data in accordance with a specific data model.

For the underlying data model see [cjdb/model/README.md](cjdb/model/README.md)

For example SQL queries on the table see [cjdb/model/BASICQUERIES.md](cjdb/model/BASICQUERIES.md)


### Indexes
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
If [CityJSON Extensions](https://www.cityjson.org/extensions/) are present in the imported files, they can be found listed in the `extensions` column in the `cj_metadata` table.

The [CityJSON specifications](https://www.cityjson.org/specs/#extensions) mention 3 different extendable features, and the `cjdb` importer deals with them as follows:

1. Complex attributes

No action is taken. These attributes end up in the `attributes` JSONB column.

2. Additional root properties

Additional root properties are placed in the `extra properties` JSONB column in the `cj_metadata` table.

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

The user can choose to run the import with either the `-e/--skip-existing` option to skip existing objects or `--overwrite` to overwrite existing objects. This will slow down the import, but it will also ensure that repeated object cases are handled.


## Contributors

This project started as a group project in the [MSc Geomatics at TUDelft](https://geomatics.tudelft.nl/).
The original code for the project is available at https://github.com/leoleonsio/cjdb, and the authors were:
@#2cynthiacai56, @LanYan1110, @YitongXia, @Topher2k, @siebren014, @leoleonsio

This version has been improved and will be maintained by @GinaStavropoulou and @hugoledoux.

