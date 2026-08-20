# cjdb Changelog
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

### Types of changes
`Added`
for new features.

`Changed` 
for changes in existing functionality.

`Deprecated` 
for soon-to-be removed features.

`Removed` for now removed features.

`Fixed` for any bug fixes.

`Security` in case of vulnerabilities.

## [2.2.0] - 2025-02-12
`Added`
Flag --clustering to make clustering optional 
Polygon validation

`Changed` 
Clustering is now optional.

`Fixed`
Bug with PGPASSWORD not being recognized


## [2.1.0] - 2023-10-20

`Changed` 
- The exporter does not close the connection
- Compliance with cityJSON v2.0.0
- Exporter SQL uses the object_id instead of the id.


## [2.0.0] - 2023-08-01

`Added`
- exporter
- --transform flag
- sphinx docs
- benchmark
- unit tests

`Changed`
- click instead of arg_parser
- functionality of --overwrite and -I/--srid flags
- filepath became an option instead of an argument
- Shorter ReadMe
- changes in data model: every object is given an integer id instead of the object id.

`Removed`
- --append flag


## [1.2.0] - 2023-04-12
Version 1.2.0

`Added`
- cjio
- tests independent of postgres 
- logger
- '--version' flag
- some exceptions

`Changed`
- merged README
- default schema to 'cjdb'

## [1.1.0] - 2023-04-06
Version 1.1.0

`Removed`
- cjdb_api, cli has import as single purpose. 
- --skip-existing flag, skipping is default.
- sphinx docs

`Changed` 
- Switched to using poetry instead of pyenv.
- renamed cli function from cj2pgsql to cjdb.
- Yanked version 1.0.0 (No CLI) 

`Fixed`
- -I/--srid flag

`Added`
- some tests


## [0.1.0] - 2022-11-11
First official release

## [0.0.8] - 2022-11-10
`Fixed`
Bug when deleting an object


## [0.0.8b] - 2022-11-09
`Added`
- user can choose between an ordinary (-x) and partial index (-px) on any attribute
- lod is indexed using GIN by default
- use multi inserts for performance
- cjdb_api is now also a CLI
- warnings if ground_geometry cannot be calculated


## [0.0.8a] - 2022-10-31
`Changed`
- detect when pyproj 3D transformation would be incomplete and attempt to download missing transformation grids
- moved argument parser help texts to a separate file
- use arg_parser mutually exclusive argument groups instead of manual checking (if flag1 and flag2...)

`Fixed`
- fixed error for family table when importing in append mode

`Added`
- dockerfile to build and run locally with docker
- --ignore-existing/-e flag to check and ignore objects with duplicated ID
- --update-existing/-u flag to update existing objects matched by ID with the new properties when importing a file

`Removed`
- bbox column for cjdb object (ground_geometry now used)

## [0.0.7a] - 2022-10-25
`Fixed`
- silent error when resolving coordinates for multiple CityObjects within a CityJSONFeature, resulting in incorrect geometries
- replaced psycopg2 requirement with psycopg2-binary requirement for easier installation
- UpdateAttrib route in cjdb_api only works if the input value is the of the same type as the mapped attribute type. 


`Added`
- Deletion of Objects from the database with cjdb_api. If an object is deleted, it is both deleted in the cj_object as the family database. If the object has children, it recursively deletes those too. 
- GetParent & GetChildren in cjdb_api, to retrieve the parents or children of an object. 
