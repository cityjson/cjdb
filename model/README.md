# cjdb data model
cjdb data model a data model designed to store cityJSON files in an Postgres Database.

The implemented data model includes three sub-data models: import_meta model for keeping information on every imported file, ob_object model for city objects, and family model for city_objects' relations.

![cjdb (1) drawio](https://user-images.githubusercontent.com/92783160/198408965-3e1daa65-057d-4387-b0e0-e2bceab6d945.png)


## Table of Contents
### [1. import_meta](#import_meta)

### [2. cj_object](#cj_object)

### [3. Family](#family)


### 1. import_meta <a name="import_meta"></a>
The import_meta model stores information from imported files. Its attributes are described below.

id: id in the database<br/>
source_file: name of the source file<br/>
version: cityJSON version<br/>
metadata: cityJSON version<br/>
transform: the transformation method from geometry's integer coordinates to real-world coordinates<br/>
geometry_templates: geometry_templates file for urban objects' geometry definition<br/>
srid: CRS of the source file<br/>
extensions: cityJSON extensions<br/>
extra_properties: added new properties at the root of the imported document<br/>
started_at: importing start time<br/>
finished_at: importing finish time<br/>
Bounding box: bounding box of the input file's geographic extent is calculated and stored as one additional attribute.

### 2. cj_object <a name="cj_object"></a>
The cj_object model stores individual city objects, for instance, buildings, roads, or bridges. Its attributes are described below.

id: city object's index within the database<br/>
import_meta_id: the source file id of the city object<br/>
object_id: the identification string of the city object (e.g. NL.IMBAG.Pand.0503100000000033-0)<br/>
type: type of the city object (e.g. building, buildingparts..)<br/>
attributes: attributes of the city object (e.g. dak_type)<br/>
geometry: geometry of the city object<br/>
bbox: bounding box of the city object<br/>
ground_geometry: ground geometry of the city object<br/>

### 3. Family <a name="family"></a>
The family model stores the relations between city objects.

id: family object's index within the database<br/>
parent_id: the identification of the parent object<br/>
child_id: the identification of the child object<br/>

