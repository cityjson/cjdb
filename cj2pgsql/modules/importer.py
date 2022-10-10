from cj2pgsql.modules.checks import check_object_type, check_root_properties
from cj2pgsql.modules.extensions import ExtensionHandler
from cj2pgsql.modules.geometric import calculate_object_bbox, \
    geometry_from_extent, get_ground_geometry, get_srid, \
    reproject, resolve_geometry_vertices, to_ewkt
from cj2pgsql.modules.utils import find_extra_properties, get_cj_object_types, get_db_engine
import os
import json
import sys
from sqlalchemy.orm import Session
from model.sqlalchemy_models import BaseModel, ImportMetaModel, CjObjectModel
from sqlalchemy import func, MetaData, inspect


class Importer():
    def __init__(self, args):
        self.args = args
        self.import_meta = None # meta read from the file
        self.source_srid = None
        self.extension_handler = None
        self.cj_object_types = get_cj_object_types()

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

        if not self.args.append_mode:
            self.post_import()

        self.import_meta.finished_at = func.now()
        self.session.commit()
        print(f"Imported from {self.args.filepath} successfully")

    def prepare_database(self):
        self.engine.execute(f"create schema if not exists {self.args.db_schema}")

        for table in BaseModel.metadata.tables.values():
            table.schema = self.args.db_schema
            table.create(self.engine, checkfirst=True)

        # the type check constraint depends also on the extensions
        # cj_object_types = get_cj_object_types()
        # in_condition = ", ".join(["'" + t + "'" for t in cj_object_types])
        # cmd = f"""alter table {CjObjectModel.__table__.schema}.{CjObjectModel.__table__.name}
        #             add constraint check_obj_type check("type" in ({in_condition}))"""
        # self.engine.execute(cmd)

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
        with open("model/post_import.sql") as f:
            cmd = f.read().format(schema=self.args.db_schema)
        self.engine.execute(cmd)
        
    def process_line(self, line):
        line_json = json.loads(line)
        if "metadata" in line_json:
            extra_root_properties = find_extra_properties(line_json)
            self.source_srid = get_srid(line_json["metadata"].get("referenceSystem"))

            if not self.args.target_srid:
                self.args.target_srid = self.source_srid

            bbox = geometry_from_extent(line_json["metadata"]["geographicalExtent"])
            if self.args.target_srid != self.source_srid:
                bbox = reproject(bbox, self.source_srid, self.args.target_srid)

            # store extensions data - extra root properties, extra city objects...
            self.extension_handler = ExtensionHandler(line_json.get("extensions"))
            # ext_handler.check_root_properties(extra_root_properties)
            # check the appearing properties against the extension definition
            # todo check extra root props, extra attributes and extra objs

            # prepare extra properties coming from extensions
            extra_properties_obj = {}
            for prop_name in extra_root_properties:
                extra_properties_obj[prop_name] = line_json[prop_name]

            check_root_properties(extra_root_properties,
                                    self.extension_handler.extra_root_properties)
                
            import_meta = ImportMetaModel(
                source_file=os.path.basename(self.args.filepath),
                version=line_json["version"],
                transform=line_json["transform"],
                meta=line_json["metadata"],
                extensions=line_json.get("extensions", {}),
                extra_properties=extra_properties_obj,
                bbox=to_ewkt(bbox.wkt, self.args.target_srid)
            )

            self.import_meta = import_meta
            import_meta.__table__.schema = self.args.db_schema
            self.import_meta = import_meta
            self.session.add(import_meta)
            self.session.commit()
        else:
            # create CityJSONObjects
            for obj_id, cityobj in line_json["CityObjects"].items():
                geometry = resolve_geometry_vertices(cityobj.get("geometry"), 
                                                    line_json.get("vertices"),
                                                    self.import_meta.transform)

                bbox = calculate_object_bbox(geometry)
                if self.args.target_srid != self.source_srid:
                    bbox = reproject(bbox, self.source_srid, self.args.target_srid)

                # todo by Lan Yan
                geom_2d = get_ground_geometry(geometry)

                # check if the object type is allowed by the official spec or extension
                # todo - object types should be fetched from the matching CityJSON version
                # https://3d.bk.tudelft.nl/schemas/cityjson/
                check_result, msg = check_object_type(cityobj.get("type"), 
                                    self.cj_object_types, 
                                    self.extension_handler.extra_city_objects)
                assert check_result, msg

                cj_object = CjObjectModel(
                    object_id=obj_id,
                    type=cityobj.get("type"),
                    attributes=cityobj.get("attributes"),
                    geometry=geometry,
                    parents=cityobj.get("parents"),
                    children=cityobj.get("children"),
                    bbox=to_ewkt(bbox.wkt, self.args.target_srid)
                )

                cj_object.__table__.schema = self.args.db_schema
                cj_object.import_meta = self.import_meta
                self.session.add(cj_object)

    def process_file(self, filepath):
        print("Running import for file: ", filepath)

        with open(filepath) as f:
            for line in f.readlines():
                self.process_line(line)

        self.import_meta.finished_at = func.now()
        self.session.commit()

    def process_directory(self, dir_path):
        print("Running import for directory: ", dir_path)

        # todo add warning when files have different SRIDS
        current_srid = None
        ext = (".jsonl")
        for f in os.scandir(dir_path):
            if f.path.endswith(ext):
                self.process_file(f.path)

                current_srid = self.source_srid