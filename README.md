# cjdb
![MIT badge](https://img.shields.io/pypi/l/cjdb)

CJDB is a set of tools enabling CityJSON integration with a PostgreSQL database.

Authors: Cynthia Cai, Lan Yan, Yitong Xia, Chris Poon, Siebren Meines, Leon Powalka

## Table of Contents  
### [1. Data model](#model)
### [2. Installation & running](#install)
### [3. Local development](#local)
### [4. Local CLI development](#cli)
### [5. Generating documentation](#docs)
---
## 1. Data model <a name="model"></a>
For the underlying data model see [model/README.md](model/README.md)

Based on this model, there are 2 software components available:

### cj2pgsql
See [cj2pgsql/README.md](cj2pgsql/README.md)
### cjdb_api
See [cjdb_api/README.md](cjdb_api/README.md)


## 2. Installation & running <a name="install"></a>
The package is available in PyPI:
```
pip install cjdb
```
It is recommended to install it in an isolated environment, because of fragile external library dependencies for CQL filter parsing. 

For instructions on running the software check specific READMEs.

## 3. Local development <a name="local"></a>
Make sure pipenv is installed:
```
pip install pipenv
```
Create the environment:
```
pipenv install
```

## 4. Local development of the CLI <a name="cli"></a>
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
3. Activate environment (note: this is not the pipenv environment. This is a separate environment just to test the CLI build)
```
. venv/bin/activate

```

4. Build the CLI:
python setup.py develop

5. The cj2pgsql importer should now work as a command inside this environment:
```
cj2pgsql --help
```

### 5. Generating documentation <a name="docs"></a>
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
