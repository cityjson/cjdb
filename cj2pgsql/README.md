# cj2pgsql
cj2pgsql is a Python based importer of CityJSONL files to a PostgreSQL database.

## Table of Contents  
- [Basic CLI Usage](#usage)

- [CLI tutorial](#tutorial)

- [Local development of the CLI](#localdev)

- [Running tests](#tests)

### Basic CLI usage <a name="usage"></a>
---
https://leoleonsio.github.io/cjdb/#cj2pgsql-cli-usage

#### Quickstart command
This command assumes the pipenv environment already exists in the repository root.

The password should be specified in the PGPASSWORD environment variable.

```
PGPASSWORD=your_pass PYTHONPATH="$PWD" pipenv run python cj2pgsql/main.py -H localhost -U postgres -d postgres -s cjdb -p 5432 file.jsonl
```

### cj2pgsql CLI tutorial <a name="tutorial"></a>
---

#### Source data
The importer works only on *CityJSONL* files.
Instructions on how to obtain such a file from a *CityJSON* file: https://cjio.readthedocs.io/en/latest/includeme.html#stdin-and-stdout


The importer has 3 possible sources of imports:
- a single CityJSONL file
- a directory of CityJSONL files (all files with *jsonl* extensions are located and imported)
- STDIN using the pipe operator:
```
cat file.jsonl | cj2pgsql ...
```

#### Model assumptions
The

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


