from cj2pgsql.modules.checks import check_object_type, check_root_properties
from cj2pgsql.modules.extensions import ExtensionHandler
from cj2pgsql.modules.geometric import calculate_object_bbox, \
    geometry_from_extent, get_ground_geometry, get_srid, \
    reproject_vertex_list, resolve_geometry_vertices, transform_vertex
from cj2pgsql.modules.utils import find_extra_properties, get_cj_object_types, get_db_engine
import os
import json
import sys
from sqlalchemy.orm import Session
from model.sqlalchemy_models import BaseModel, FamilyModel, ImportMetaModel, CjObjectModel
from sqlalchemy import func
from pathlib import Path
from pyproj import CRS

# class to store variables per file import - for clarity
class SingleFileImport:
    def __init__(self, file="stdin"):
        self.file = file
        self.target_srid = None
        self.import_meta = None # meta read from the file
        self.source_srid = None
        self.extension_handler = None


class Importer:
    def __init__(self, args):
        self.args = args
        self.cj_object_types = get_cj_object_types()
        self.current = SingleFileImport()


    def __enter__(self):
        self.engine = get_db_engine(self.args)
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def run_import(self):
        if not self.args.append_mode:
            self.prepare_database()

        self.parse_cityjson()
        self.session.commit()

        # post import operations like clustering, indexing...
        if not self.args.append_mode:
            self.post_import()

        self.current.import_meta.finished_at = func.now()
        self.session.commit()
        print(f"Imported from {self.args.filepath} successfully")

    def prepare_database(self):
        if self.args.overwrite:
            self.engine.execute(f"drop schema if exists {self.args.db_schema} cascade")
        self.engine.execute(f"create schema if not exists {self.args.db_schema}")

        for table in BaseModel.metadata.tables.values():
            table.schema = self.args.db_schema
            table.create(self.engine, checkfirst=True)

    def parse_cityjson(self):
        source_path = self.args.filepath

        if source_path.lower() == "stdin":
            for line in sys.stdin:
                self.process_line(line.rstrip("\n"))

        elif os.path.isfile(source_path):
            self.process_file(source_path)

        elif os.path.isdir(source_path):
            self.process_directory(source_path)

        else:
            raise Exception(f"Path: '{source_path}' not found")

    def post_import(self):
        cur_path = Path(__file__).parent
        sql_path = os.path.join(cur_path.parent, "resources/post_import.sql")

        with open(sql_path) as f:
            cmd = f.read().format(schema=self.args.db_schema)
        self.engine.execute(cmd)
        self.index_attributes()
        
    def process_line(self, line):
        line_json = json.loads(line)
        if "metadata" in line_json:
            extra_root_properties = find_extra_properties(line_json)
            self.current.source_srid = get_srid(line_json["metadata"].get("referenceSystem"))
            if not self.current.source_srid:
                print("Warning: No Coordinate Reference System specified for the dataset.")

            # use specified target SRID for all the geometries
            # If not specified use same as source.
            if self.args.target_srid and self.current.source_srid:
                self.current.target_srid = self.args.target_srid
                target_crs = CRS.from_epsg(self.args.target_srid)
                if not target_crs.is_vertical:
                    print(f"Warning: The specified target SRID({self.args.target_srid}) " + \
                         "represents a non-vertical CRS. The Z vertex values will remain unchanged.")
            else:
                self.current.target_srid = self.current.source_srid

            # calculate dataset bbox based on geographicalExtent
            bbox = None
            if "geographicalExtent" in line_json["metadata"]:
                bbox = geometry_from_extent(line_json["metadata"]["geographicalExtent"])
                bbox = func.st_geomfromtext(bbox.wkt, self.current.source_srid)
                if self.current.source_srid \
                    and self.current.target_srid != self.current.source_srid:

                    bbox = func.st_transform(bbox, self.current.target_srid)

            # store extensions data - extra root properties, extra city objects...
            self.current.extension_handler = ExtensionHandler(line_json.get("extensions"))

            # prepare extra properties coming from extensions
            # they will be placed in the extra_properties jsonb column
            extra_properties_obj = {}
            for prop_name in extra_root_properties:
                extra_properties_obj[prop_name] = line_json[prop_name]

            # check the occurring properties against the extension defined extra properties
            check_root_properties(extra_root_properties,
                                    self.current.extension_handler.extra_root_properties)
                
            # "or None" is added to change empty json "{}" to database null
            import_meta = ImportMetaModel(
                source_file=os.path.basename(self.current.file),
                version=line_json["version"],
                meta=line_json.get("metadata") or None,
                transform=line_json.get("transform") or None,
                geometry_templates=line_json.get("geometry-templates") or None,
                srid=self.current.target_srid,
                extensions=line_json.get("extensions") or None,
                extra_properties=extra_properties_obj or None,
                bbox=bbox
            )

            # compare to existing import metas
            # for example to detect inconsistent CRS from different files
            result_ok = import_meta.compare_existing(self.session, 
                                                    self.args.ignore_repeated_file)
            if not result_ok:
                print("Cancelling import")
                sys.exit()

            # add metadata to the database
            import_meta.__table__.schema = self.args.db_schema
            self.current.import_meta = import_meta
            self.session.add(import_meta)
            self.session.commit()
        else:
            # unpack vertices for the cityobjects based on the CityJSON transform
            # this is done once for the CityJSONFeature
            vertices = [transform_vertex(v, self.current.import_meta.transform) 
                                        for v in line_json["vertices"]]

            # reproject if needed
            source_target_srid = None
            if self.current.source_srid and self.current.target_srid != self.current.source_srid:
                source_target_srid = (self.current.source_srid, self.current.target_srid)
                vertices = reproject_vertex_list(vertices, *source_target_srid)

            # create CityJSONObjects
            for obj_id, cityobj in line_json["CityObjects"].items():
                # get 3D geom, ground geom and bbox
                geometry, ground_geometry, bbox = self.get_geometries(cityobj, vertices,
                                                                        source_target_srid)
                    
                # check if the object type is allowed by the official spec or extension
                check_result, message = check_object_type(cityobj.get("type"), 
                                    self.cj_object_types, 
                                    self.current.extension_handler.extra_city_objects)
                if not check_result:
                    print(message)

                # 'or None' is added to change empty json "{}" to database null
                cj_object = CjObjectModel(
                    object_id=obj_id,
                    type=cityobj.get("type"),
                    attributes=cityobj.get("attributes") or None,
                    geometry=geometry,
                    bbox=bbox,
                    ground_geometry=ground_geometry
                )

                # create children-parent links
                for child_id in cityobj.get("children", []):
                    family = FamilyModel(parent_id=obj_id, child_id=child_id)
                    self.session.add(family)

                # add CityJson object to the database
                cj_object.__table__.schema = self.args.db_schema
                cj_object.import_meta = self.current.import_meta
                self.session.add(cj_object)

    def process_file(self, filepath):
        self.current = SingleFileImport(filepath)
        print("Running import for file: ", filepath)

        with open(filepath) as f:
            for line in f.readlines():
                self.process_line(line)

        self.current.import_meta.finished_at = func.now()
        self.session.commit()

    def process_directory(self, dir_path):
        print("Running import for directory: ", dir_path)
        ext = (".jsonl")
        for f in os.scandir(dir_path):
            if f.path.endswith(ext):
                self.process_file(f.path)

    def index_attributes(self):
        # postgres types to be used in type casted index
        postgres_type_mapping = {
            float: "float",
            str: "text",
            int: "int",
            bool: "boolean"
        }

        # python type mapping for the attributes based on sampled values
        type_mapping = CjObjectModel.get_attributes_and_types(self.session)

        # sql index command
        cmd_base = "create index {table}_{attr_name}_idx " + \
                "on {schema}.{table} using btree(((attributes->>'{attr_name}')::{attr_type}))" + \
                " WHERE attributes->>'{attr_name}' IS NOT NULL;"

        # for each attribute to be indexed
        for attr_name in self.args.indexed_attributes:
            print(f"Indexing CityObject attribute: '{attr_name}'")

            # get proper postgres type
            if attr_name in type_mapping:
                postgres_type = postgres_type_mapping[type_mapping[attr_name]]

                # prepare and run sql command
                cmd = cmd_base.format(
                    table=CjObjectModel.__table__.name,
                    schema=CjObjectModel.__table__.schema,
                    attr_name=attr_name,
                    attr_type=postgres_type
                )
                self.engine.execute(cmd)

            else:
                print(f"Specified attribute to be indexed: '{attr_name}' does not exist")
            # maybe create partial index?

    def get_geometries(self, cityobj, vertices, source_target_srid):
        if "geometry" not in cityobj:
            return None, None, None
        
        # returned geometry is already in the required projection
        geometry = resolve_geometry_vertices(cityobj["geometry"], 
                                            vertices,
                                            self.current.import_meta.geometry_templates,
                                            source_target_srid)

        bbox = calculate_object_bbox(geometry)
        bbox = func.st_geomfromtext(bbox.wkt, self.current.target_srid)

        ground_geometry = get_ground_geometry(geometry)
        ground_geometry = func.st_geomfromtext(ground_geometry.wkt, self.current.target_srid)

        return geometry, ground_geometry, bbox
