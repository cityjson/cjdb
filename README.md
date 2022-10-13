# cjdb
CJDB is a set of tools enabling CityJSON integration with a PostgreSQL database


## cj2pgsql
See [cj2pgsql/README.md](cj2pgsql/README.md)
## cjdb
See [cjdb_api/README.md](cjdb_api/README.md)

### Generating documentation
1. Make sure sphinx is installed:
```
pip3 install python3-sphinx sphinx-argparse
```

2. Generate documentation command, called from repository root:
```
make docs
```
or:
```
sphinx-build -b html docs/config docs/content 
```

As a result, he documentation is generated in the docs/content folder. 

Open `index.html` file to see the main page.