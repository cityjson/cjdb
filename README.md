# cjdb
CJDB is a set of tools enabling CityJSON integration with a PostgreSQL database.

There are 2 software components available:

### cj2pgsql
See [cj2pgsql/README.md](cj2pgsql/README.md)
### cjdb_api
See [cjdb_api/README.md](cjdb_api/README.md)


## Docs
https://leoleonsio.github.io/cjdb/

## Installation & running
The package is available in PyPI:
```
pip install cjdb
```

For instructions on running the software check specific READMEs.

## Local development
Make sure pipenv is installed:
```
pip install pipenv
```
Create the environment:
```
pipenv install
```

### Generating documentation
1. Make sure sphinx is installed:
```
pip3 install python3-sphinx sphinx-argparse myst-parser
```

2. Generate documentation command, called from repository root:
```
make docs
```
or:
```
sphinx-build -b html docs/config docs
```

As a result, he documentation is generated in the docs folder. 

Open `index.html` file to see the main page.
