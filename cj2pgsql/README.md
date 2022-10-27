# cj2pgsql
`cj2pgsql` is a Python based importer of CityJSONL files to a PostgreSQL database.

## Table of Contents  
- [Basic CLI Usage](#usage)

- [cj2pgsql explanations](#explanation)

- [Local development of the CLI](#localdev)

- [Running tests](#tests)

### Basic CLI usage <a name="usage"></a>
---
https://leoleonsio.github.io/cjdb/#cj2pgsql-cli-usage

#### Quickstart example
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


 

### cj2pgsql explanations <a name="explanation"></a>
---
#### Model assumptions
The `cj2pgsql` importer loads the data in accordance with a specific data model, which is also shared with the [`cjdb_api`](../cjdb_api/README.md).

Model documentation:
 [model/README](../model/README.md)


#### What is a City Model? How to organize CityJSON data from various sources?

The definition and scope of the City Model are for the user to decide. It is recommended to group together semantically coherent objects, by importing them to the same database schema.

While the static table structure (columns don't change) does support loading any type of CityJSON objects together, the data becomes harder to manage for the user. Example of this would be having different attributes for the same CityObject type (which should be consistent for data coming from the same source).

#### Source data
The importer works only on *CityJSONL* files.
Instructions on how to obtain such a file from a *CityJSON* file: https://cjio.readthedocs.io/en/latest/includeme.html#stdin-and-stdout


The importer supports 3 kinds of input:
- a single CityJSONL file
- a directory of CityJSONL files (all files with *jsonl* extensions are located and imported)
- STDIN using the pipe operator:
```
cat file.jsonl | cj2pgsql ...
```

#### Coordinate Reference Systems
The `cj2pgsql` importer does not allow inconsistent reference systems within the same database schema. For storing data in separate CRS using multiple schemas is required.

The data needs to be either harmonized beforehand, or the `-I/--srid` flag can be used upon import, to reproject all the geometries to the one specified CRS. Specifying a 2D CRS (instead of a 3D one) will cause the Z-coordinates to remain unchanged.

Source data with missing `referenceSystem` cannot be reprojected due to unknown source reference system.


### Local development of the CLI <a name="localdev"></a>
---
To build the CLI app (so that it can be called as a command line tool from anywhere):


1. Sync the pipenv requirements with the setup.py file:
```
pipenv run pipenv-setup sync
```

2. Create a venv just for testing the CLI build.

**Note**: This is not the pipenv/development environment.
```
virtualenv venv
```
2. Activate environment (note: this is not the pipenv environment. This is a separate environment just to test the CLI build)
```
. venv/bin/activate

```

3. Build the CLI:
python setup.py develop

4. The cj2pgsql should now work as a command inside this environment:
```
cj2pgsql --help
```


### Running tests <a name="tests"></a>
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


