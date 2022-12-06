# cjdb_api
[![MIT badge](https://img.shields.io/pypi/l/cjdb)](../LICENSE) &nbsp; [![PyPI](https://img.shields.io/pypi/v/cjdb)](https://pypi.org/project/cjdb)

cjdb_api is Flask application enabling querying and maintenance of cjdb data via a REST interface.

## Table of Contents  
### [1. Installation](#Installation)
### [2. Run](#Run)
### [3. Functionality](#Functionality)
   #### [3.1 Simple Queries](#Simple)
   #### [3.2 Complex Queries](#Complex)
   #### [3.3 CQL](#CQL)
   #### [3.4 Add/Update](#Add/Update)
   #### [3.5 Deletion](#Deletion)

---
## 1. Installation <a name="Installation"></a>
See [README.md](../README.md)

## 2. Run <a name="Run"></a>

### Using CLI

```
cjdb_api -C postgresql://postgres:postgres@localhost:5432/cjdb -s cjdb2 -p 5000
```

### Using the repository code
```
pipenv run python cjdb_api/run.py -C postgresql://postgres:postgres@localhost:5432/cjdbv5 -s cjdb2 -p 5000
```

API will be launched at localhost:
```
http://localhost:5000/api
```

### Arguments 

1. 'C' 
Data base connection string, in format of:
```
"postgresql://<user>:<password>@<host>:<port>/<database>"
```
2. 'p'
Port to connect API to. Default = 8080
3. 's'
Database schema, where the CityObjects are kept

4. 'd'
To run in debug mode.


## 3. Functionality <a name="Functionality"></a>

Home page: http://localhost:5000
View the first 50th collections: http://localhost:5000/collections
API documentation: http://localhost:5000/api
 
### 3.1 Simple Queries <a name="Simple"></a>
**Show** - Show an x amount of entries in the db. For instance: 
```
http://localhost:5000/collections?limit=5
```
**QueryByAttribute** - Look for specific values of attributes. For instance to select the object with id 5:
```
http://localhost:5000/collections/items?id=5
```
http://localhost:5000/collections/items?type=Building
```
**GetChildren** - Get the children of an object. For instance:
```
http://localhost:5000/collections/items?parent_id=NL.IMBAG.Pand.0503100000000018
```
**GetParent** - Get the parent of an object. For instance:
```
http://localhost:5000/collections/items?child_id=NL.IMBAG.Pand.0503100000000018-0
```

### 3.2 Complex Queries <a name="Complex"></a>
**QueryByBbox** - Returns all objects whose ground geometries are within a given 2D bounding box. For instance:
```
http://localhost:5000/collections/items?bbox=(81400,451400,81600,451600)
```
**QueryByPoint** - Returns the object located at a given point. For instance:
```
http://localhost:5000/collections/items?point=(81402.6705,451405.4224)
```

### 3.3 CQL <a name="CQL"></a>
**CQL_query** - Allows the usage of common query language to chain queries. For instance:
```
localhost:5000/collections/cql?FILTER=type="Building"ANDdata_area>30
```

### 3.4 Add/Update <a name="Add/Update"></a>
**AddAttribute** - Add an attribute to an object, or to all, by replacing the object_id with “all”. For instance: 
```
http://localhost:5000/operation/add?object_id=NL.IMBAG.Pand.0503100000000021&attribute=attrib&value=10
```
**UpdateAttrib**  - update the value of an attribute from an object, or to all objects, by replacing the object_id with “all”. For instance:
```
http://localhost:5000/operation/update?object_id=all&attribute=attrib&value=12
```

### 3.5 Deletion <a name="Deletion"></a>
**DelAttrib** - Delete an attribute from an object, or from all, by replacing the object_id with “all”. For instance:
```
http://localhost:5000/operation/delete?object_id=NL.IMBAG.Pand.0503100000000021&attribute=attrib
```
**DelObject** - Delete an object from the data. If the object has children, these are also deleted.
```
http://localhost:5000/operation/delete/object?object_id=NL.IMBAG.Pand.0503100000000021
```
