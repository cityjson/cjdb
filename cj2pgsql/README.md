# cj2pgsql
cj2pgsql is a python based importer of CityJSONL files to a PostgreSQL database.

### CLI usage instructions
https://leoleonsio.github.io/cjdb/#cj2pgsql-cli-usage

### Running the importer example:
The password should be specified in the PGPASSWORD environment variable.

```
PYTHONPATH="$PWD" pipenv run python cj2pgsql/main.py -H localhost -U postgres -d postgres -s cjdb2 -p 5555 ~/Downloads/5870.jsonl
```

### Running tests
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


### Local development of the CLI
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

4. The cj2pgsql should now work as a command:
```
cj2pgsql --help
```
