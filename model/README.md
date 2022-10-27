The implemented data model includes three sub-data models: import_meta model for keeping information on every imported file, ob_object model for city objects, and family for city_objects' relations.

import_meta
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
started_at: importing start time
finished_at: importing finish time
Bounding box: bounding box of the input file's geographic extent is calculated and stored as one additional attribute.

cj_object
The cj_object model stores individual city objects, for instance, buildings, roads, or bridges. Its attributes are described below.

id: city object's index within the database
import_meta_id: the source file id of the city object
object_id: the identification string of the city object (e.g. NL.IMBAG.Pand.0503100000000033-0)
type: type of the city object (e.g. building, buildingparts..)
attributes: attributes of the city object (e.g. dak_type)
geometry: geometry of the city object
bbox: bounding box of the city object
ground_geometry: ground geometry of the city object

Family
The family model stores the relations between city objects.

id: family object's index within the database
parent_id: the identification of the parent object
child_id: the identification of the child object
