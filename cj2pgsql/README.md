# cj2pgsql
cj2pgsql is a python based importer of CityJSONL files to a PostgreSQL database.

## Parameters
    todo - describe parameters

## Local development
### Initializing the virtual environment
```
cd cj2pgsql
pipenv install
```

### Running the importer example:
```
pipenv run cj2pgsql.py -H localhost -U postgres -d postgres -s cjdb2 -p 5555 ~/Downloads/5870.jsonl
```



