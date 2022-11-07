# cjdb API
![MIT badge](https://img.shields.io/pypi/l/cjdb)

CJDB is a set of tools enabling CityJSON integration with a PostgreSQL database.

Authors: Cynthia Cai, Lan Yan, Yitong Xia, Chris Poon, Siebren Meines, Leon Powalka

## Table of Contents  
### [1. Installation](#Installation)
### [2. Run](#Run)
### [3. Functionality](#Functionality)
   #### [3.1 Simple Queries](#Simple)
   #### [3.2 Complex Queries](#Complex)
   #### [3.3 Add/Update](#Add/Update)
   #### [3.4 Deletion](#Deletion)

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
pipenv run python cjdb_api/run.py -C postgresql://postgres:postgres@localhost:5432/cjdbv5 -s cjd
b2 -p 5000
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
 
### 3.1 Simple Queries <a name="Simple"></a>
**Show** - Show an x amount of entries in the db. For instance: 
```
http://localhost:5000/api/show/5 
```

**QueryByAttribute** - Look for specific values of attributes. For instance to select the object with id 5:
```
http://localhost:5000/api/select/id/5
```
```
http://localhost:5000/api/select/type/Building
```
**GetInfo** - Get the attribute info of an object, given the object_id. For instance to get the geometry of NL.IMBAG.Pand.0175100000014322:
```
http://localhost:5000/api/info/geometry/NL.IMBAG.Pand.0503100000000021
```
**FilterAttributes** - Filter in the attributes with operators >, < , =. For Instance:
```
http://localhost:5000/api/filter/data_area/bigger/40
```
**GetChildren** - Get the children of an object. For instance:
```
http://localhost:5000/api/children/NL.IMBAG.Pand.0503100000000021
```
**GetParent** - Get the parent of an object. For instance:
```
http://localhost:5000/api/parent/NL.IMBAG.Pand.0503100000000021
```

### 3.2 Complex Queries <a name="Complex"></a>
**QueryByGroundGeometry** - Returns all objects within a given bounding box. For instance:
```
http://localhost:5000/api/ground_geometry/(81400,451400,81600,451600)
```
**QueryByPoint** - Returns the object located at a given point. For instance:
```
http://localhost:5000/api/point/(81402.6705,451405.4224)
```
**CQL_query** - Allows the usage of common query language to chain queries. For instance:
```
localhost:5000/api/cql?CQL_FILTER=type="Building"ANDdata_area>30
```

### 3.3 Add/Update <a name="Add/Update"></a>
**AddAttribute** - Add an attribute to an object, or to all, by replacing the object_id with “all”. For instance: 
```
http://localhost:5000/api/add/NL.IMBAG.Pand.0503100000000021/attrib/10
```
**UpdateAttrib**  - update the value of an attribute from an object, or to all objects, by replacing the object_id with “all”. For instance:
```
http://localhost:5000/api/update/all/attrib/12
```

### 3.4 Deletion <a name="Deletion"></a>
**DelAttrib** - Delete an attribute from an object, or from all, by replacing the object_id with “all”. For instance:
```
http://localhost:5000/api/del/NL.IMBAG.Pand.0503100000000021/attrib
```
**DelObject** - Delete an object from the data. If the object has children, these are also deleted.
```
http://localhost:5000/api/delObject/NL.IMBAG.Pand.0503100000000021
```
