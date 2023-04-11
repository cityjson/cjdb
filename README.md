# cjdb
[![MIT badge](https://img.shields.io/pypi/l/cjdb)](LICENSE) &nbsp; [![PyPI](https://img.shields.io/pypi/v/cjdb)](https://pypi.org/project/cjdb)

CJDB is a tool for enabling CityJSON integration with a PostgreSQL database.

Authors: Cynthia Cai, Lan Yan, Yitong Xia, Chris Poon, Siebren Meines, Leon Powalka

Maintainer: Gina Stavropoulou

## Table of Contents  
### [1. Data model](#model)
### [2. Installation & running](#install)
### [3. Local development](#local)
### [4. Running tests](#tests)
---
## 1. Data model <a name="model"></a>
For the underlying data model see [cjdb/model/README.md](cjdb/model/README.md)


## 2. Installation & running <a name="install"></a>
### Using pip

```bash
pip install cjdb
```
It is recommended to install it in an isolated environment, because of fragile external library dependencies for CQL filter parsing.

### Using docker
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
docker run -v {MYDIRECTORY}:/data --rm -it --network=host cjdb cjdb -H localhost -U postgres -d postgres -W postgres /data/5870_ext.jsonl 
```

## 3. Local development <a name="local"></a>
Make sure `poetry` is installed. Then, to create a local environment with all the necessary dependencies, run from the repository root:
```bash
poetry install
```

To build the wheel run:
```bash
poetry build
```

Then install the .whl file with pip:
```bash
pip3 install dist/*.whl --force-reinstall
```

Then you can run the CLI command:
```bash
cjdb --help
```

## 4. Running tests <a name="tests"></a>
In onrder to run the tests you need to have PostgreSQL installed. Then you can run:

```bash
pytest -v
```





