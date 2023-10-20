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

Sample CityJSON data can be downloaded from [the 3DBAG download service](https://3dbag.nl/). 
For example, [download the tile "9-284-556"](https://data.3dbag.nl/cityjson/v20230622/tiles/9/284/556/9-284-556.city.json), within which part of TU Delft is located.
Then, having downloaded the CityJSON file, you need a combination of [cjio](https://github.com/cityjson/cjio) (external CityJSON processing library) and cjdb to import it to a schema in a database.  Here is a step-by-step guide:

1. Convert CityJSON to CityJSONL

```bash
cjio --suppress_msg 9-284-556.json export jsonl 9-284-556.jsonl 
```

2. Create a new database called "testcjdb"

If you installed PostgreSQL you should have the program 'createdb', so `createdb testcjdb`

Alternatively, you can use PgAdmin, [see how](https://postgis.net/workshops/postgis-intro/creating_db.html).

3. Import CityJSONL to the database in the schema "cjdb"
```bash
cjdb import -H localhost -U postgres -d testcjdb -s cjdb  -f 9-284-556.jsonl
```

**Alternatively steps 1 and 3 in a single command:**

```bash
cjio --suppress_msg 9-284-556.json export jsonl stdout | cjdb import -H localhost -U postgres -d postgres -s cjdb
```

The metadata and the objects can then be found in the tables in the specified schema (`cjdb` in this example).

The password can be specified in the `PGPASSWORD` environment variable. If not specified, the app will prompt for the password.

4. If you want to export from the database you have two options. You can export the whole database in a CityJSONL file with: 
```bash
cjdb export -H localhost -U postgres -d testcjdb -s cjdb -o result.jsonl
```
or export only part of it, using a select query as input. The select query should return the ids of the objects to be exported:

```bash
cjdb export -H localhost -U postgres -d testcjdb -s cjdb -o result.jsonl -q "SELECT 'NL.IMBAG.Pand.1655100000500568' as object_id"
```

5. If you want to convert from CityJSONFeatures to city json you can use `cjio`:
```bash
cat /path/to/result.city.jsonl | cjio  stdin save /path/to/output.city.json
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
docker run -v {MYDIRECTORY}:/data --rm -it --network=host cjdb cjdb import -H localhost -U postgres -d postgres -W postgres -f /data/5870_ext.jsonl 
```

## Important Notes
### Data model

The `cjdb` importer loads the data in accordance with a [specific data model](cjdb/model/README.md).

For example SQL queries on the tables see [here](cjdb/model/BASICQUERIES.md)


### Indexes
Some indexes are created when a new schema is created (refer to [Data Model](cjdb/model/README.md)).

In addition to these indexes, the user can add more indexes on certain  CityObject attributes with the `-x/--attr-index` or the `-px/--partial-attr-index` flags.
We recommend these additional indexes for attributes that are frequently queried.
The second option uses a partial index with a `not null` condition on the attribute.
This saves disk space when indexing an attribute that is not present among all the imported CityObjects.
This is often the case with CityJSON, because in a single dataset there can be different object types, with different attributes.


### Structuring the database and its schemas

It is recommended to group together semantically coherent objects, by importing them to the same database schema.
One database can have different schemas.

While the current data model supports the import of any type of CityJSON objects together (`Building` and `SolitaryVegetationObject`), the data becomes harder to manage for the user. 
Example of this would be having different attributes for the same CityObject type (which should be consistent for data coming from the same source).


### Input == CityJSONFeature
The importer works only on with [*CityJSONL* files](https://www.cityjson.org/specs/#text-sequences-and-streaming-with-cityjsonfeature), which are CityJSON files decomposed into their *features* (`CityJSONFeature`).

The easiest way to create these from a CityJSON file is with [cjio](https://github.com/cityjson/cjio), by following [these instructions](https://github.com/cityjson/cjio#stdin-and-stdout).

The importer supports 3 kinds of input:
  1. a single CityJSONL file (only those as the output of cjio currently work)
  1. a directory of CityJSONL files (all files with *jsonl* extensions are located and imported)
  1. STDIN using the pipe operator: `cat file.jsonl | cjdb ...`


### Coordinate Reference Systems
The `cjdb` importer does not allow inconsistent CRSs (coordinate reference systems) within the same database schema. For storing data in different CRSs, you have to create different schemas.

The data needs to be either harmonized beforehand, or the `--transform` flag can be used upon import, to reproject all the geometries to the CRS of the existing schema. 
Specifying a 2D CRS (instead of a 3D one) will cause the Z-coordinates to remain unchanged.

**Note:** reprojections slow down the import significantly.

**Note:** Source data with missing `"metadata"/"referenceSystem"` cannot be reprojected due to unknown source reference system. 
You can use the `-I/--srid` flag to set the SRID of the input file. 


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
- CityObject types appear which are defined neither in the main CityJSON specification nor in any of the supplied extensions. 
- the specified target CRS does not have the Z-axis defined
- the source dataset does not have a CRS defined at all

### Repeated object IDs
The importer does not check if an object with a specific ID exists already in the database - every imported object gets and new id. However, at the time of import the importer will detect previously detected files with the same filename. The user can choose to run the import with either the `-g, --ignore-repeated-file` option to import files with the same filename under a different id or `--overwrite` to overwrite *all* previously imported objects with this filename.


## Contributors

This project started as a group project in the [MSc Geomatics at TUDelft](https://geomatics.tudelft.nl/).
The original code for the project can be found [here](https://github.com/leoleonsio/cjdb), and the authors were:
[@cynthiacai56](https://github.com/cynthiacai56), [@LanYan1110](https://github.com/LanYan1110), [@YitongXia](https://github.com/YitongXia), [@Topher2k](https://github.com/Topher2k), [@siebren014](https://github.com/siebren014), [@leoleonsio](https://github.com/leoleonsio)

This version has been improved and will be maintained by [@GinaStavropoulou](https://github.com/GinaStavropoulou), and [@hugoledoux](https://github.com/hugoledoux).

