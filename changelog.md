# CJDB Changelog
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

## [Unreleased]
`Changed`
- detect when pyproj 3D transformation would be incomplete and attempt to download missing transformation grids
`Fixed`
- fixed error for family table when importing in append mode

## [0.0.7a] - 2022-10-25
`Fixed`
- silent error when resolving coordinates for multiple CityObjects within a CityJSONFeature, resulting in incorrect geometries
- replaced psycopg2 requirement with psycopg2-binary requirement for easier installation
