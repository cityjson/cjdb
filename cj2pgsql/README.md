# cj2pgsql
`cj2pgsql` is a Python based importer of CityJSONL files to a PostgreSQL database.

## Table of Contents  
### [1. Basic CLI Usage](#usage)
- [Quickstart example](#quickstart)

### [2. cj2pgsql explanations](#explanation)
 - [Model assumptions](#model)
 - [What is a City Model?](#citymodel)
 - [Types of input](#input)
 - [Coordinate Reference Systems](#crs)
 - [3D reprojections](#3d)
 - [CityJSON Extensions](#extensions)
 - [CityJSON GeometryTemplate](#geomtemplate)
 - [Data validation](#validation)

### [3. Running with local code](#local)

### [4. Running tests](#tests)
---------------------------------

## 1. Basic CLI usage <a name="usage"></a>
---
https://leoleonsio.github.io/cjdb/#cj2pgsql-cli-usage

### Quickstart example <a name="quickstart"></a>
Sample CityJSON data can be downloaded from [3DBAG download service](https://3dbag.nl/nl/download?tid=901).

Then, having the CityJSON file, a combination of [cjio](https://github.com/cityjson/cjio) (external CityJSON processing library) and cj2pgsql is needed to import it to a specified schema in a database.

1. Convert CityJSON to CityJSONL

```
cjio --suppress_msg tile_901.json export jsonl stdout > tile_901.jsonl 
```

2. Import CityJSONL to the database
```
PGPASSWORD=postgres cj2pgsql -H localhost -U postgres -d postgres -s cjdb -o tile_901.jsonl   
```

**Alternatively steps 1 and 2 in a single command:**

```
cjio --suppress_msg tile_901.json export jsonl stdout | cj2pgsql -H localhost -U postgres -d postgres -s cjdb -o
```

The metadata and the objects can then be found in the tables in the specified schema (`cjdb` in this example).


Password can be specified in the `PGPASSWORD` environment variable. If not specified, the app will prompt for the password.


## 2. cj2pgsql explanations <a name="explanation"></a>
---
### Model assumptions <a name="model"></a>
The `cj2pgsql` importer loads the data in accordance with a specific data model, which is also shared with the [`cjdb_api`](../cjdb_api/README.md).

Model documentation:
 [model/README](../model/README.md)


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
cat file.jsonl | cj2pgsql ...
```

### Coordinate Reference Systems <a name="crs"></a>
The `cj2pgsql` importer does not allow inconsistent CRS (coordinate reference systems) within the same database schema. For storing data in separate CRS using multiple schemas is required.

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

The [CityJSON specifications](https://www.cityjson.org/specs/1.1.2/#extensions) mention 3 different extendable features, and the `cj2pgsql` importer deals with them as follows:

1. Complex attributes

No action is taken. These attributes end up in the `attributes` JSONB column. Querying by complex attributes values is not supported in the `cjdb_api` as of v0.0.7a.

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

## 3. Running with local code <a name="local"></a>
Create `pipenv` environment in repository root:
```
pipenv install
```

Run the importer:
```
PYTHONPATH=$PWD pipenv run python cj2pgsql/main.py --help
```


## 4. Running tests <a name="tests"></a>
---
Test cases for Pytest are generated based on the CityJSONL files in:
- cj2pgsql/test/files

And the argument sets defined in the file:
- cj2pgsql/test/inputs/arguments

Where each line is a separate argument set.

The tests are run for each combination of a file and argument set. To run them locally, the cj2pgsql/test/inputs/arguments file has to be modified.

Install pytest first.
```
pip3 install pytest
```

Then, in repository root:
```
pytest cj2pgsql -v
```

or, to see the importer output:
```
pytest cj2pgsql -s
```


