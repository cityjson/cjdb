import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from shapely.geometry.base import BaseGeometry
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from cjdb.logger import logger
from cjdb.model.sqlalchemy_models import (BaseModel, CjObjectModel,
                                          FamilyModel, ImportMetaModel)
from cjdb.modules.checks import (check_object_type, check_reprojection,
                                 check_root_properties)
from cjdb.modules.exceptions import (InvalidCityJSONObjectException,
                                     InvalidMetadataException)
from cjdb.modules.extensions import ExtensionHandler
from cjdb.modules.geometric import (get_ground_geometry, get_srid,
                                    reproject_vertex_list,
                                    resolve_geometry_vertices,
                                    transform_vertex)
from cjdb.modules.utils import (find_extra_properties, get_cj_object_types,
                                is_cityjson_object, to_dict)


# class to store variables per file import - for clarity
class SingleFileImport:
    def __init__(self, file="stdin"):
        self.file = file
        self.target_srid = None
        self.import_meta = None  # meta read from the file
        self.source_srid = None
        self.extension_handler = (
            None  # data about extensions - extra properties, root attributes
        )
        self.cj_objects = []
        self.families = []


# importer class called once per whole import
class Importer:
    def __init__(self, engine, args):
        self.engine = engine
        self.args = args
        # get allowed types for validation
        self.cj_object_types = get_cj_object_types()
        self.current = SingleFileImport()

        for table in BaseModel.metadata.tables.values():
            table.schema = self.args.db_schema

    def __enter__(self):
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def run_import(self) -> None:
        # create model if in create mode, else append data
        if not self.args.append_mode:
            self.prepare_database()
        self.parse_cityjson()
        self.session.commit()
        # post import operations like clustering, indexing...
        if not self.args.append_mode:
            self.post_import()
        self.current.import_meta.finished_at = func.now()
        self.session.commit()
        logger.info(f"Imported from {self.args.filepath} successfully")

    def prepare_database(self) -> None:
        """Adds the postgis extension and creates
        the schema and the tables."""
        with self.engine.connect() as conn:
            conn.execute(text("""CREATE EXTENSION IF NOT EXISTS postgis"""))
            if self.args.overwrite:
                conn.execute(text(f"""DROP SCHEMA
                             IF EXISTS {self.args.db_schema}
                             CASCADE"""))
            conn.execute(text(f"""CREATE SCHEMA IF NOT EXISTS
                                  {self.args.db_schema}"""))
            conn.commit()
        # create all tables defined as SqlAlchemy models
        for table in BaseModel.metadata.tables.values():
            table.create(self.engine, checkfirst=True)

    def parse_cityjson(self) -> None:
        """Parses the input path."""
        source_path = self.args.filepath

        if os.path.isfile(source_path) or source_path.lower() == "stdin":
            self.process_file(source_path)

        elif os.path.isdir(source_path):
            self.process_directory(source_path)

        else:
            raise Exception(f"Path: '{source_path}' not found")

    def post_import(self) -> None:
        """Perform post import operation on the schema,
           like clustering and indexing"""

        cur_path = Path(__file__).parent
        sql_path = os.path.join(cur_path.parent, "resources/post_import.sql")

        with open(sql_path) as f:
            cmd = f.read().format(schema=self.args.db_schema)
        with self.engine.connect() as conn:
            conn.execute(text(cmd))
        self.index_attributes()

    def extract_import_metadata(self, line_json):
        if "metadata" not in line_json:
            raise InvalidMetadataException("The file should contain a member"
                                           "'metadata', in the first object")

        extra_root_properties = find_extra_properties(line_json)
        self.current.source_srid = get_srid(
            line_json["metadata"].get("referenceSystem")
        )
        if not self.current.source_srid:
            logger.warning("No Coordinate Reference System"
                           " specified for the dataset.")

        # use specified target SRID for all the geometries
        # If not specified use same as source.
        if self.args.target_srid and self.current.source_srid:
            self.current.target_srid = self.args.target_srid
            check_reprojection(self.current.source_srid,
                               self.current.target_srid)
        elif self.args.target_srid:
            self.current.target_srid = self.args.target_srid
        else:
            self.current.target_srid = self.current.source_srid

        # calculate dataset bbox based on geographicalExtent
        bbox = None
        if "geographicalExtent" in line_json["metadata"]:
            bbox_coords = line_json["metadata"]["geographicalExtent"]
            bbox_vertices = [bbox_coords[:3], bbox_coords[3:]]

            if (
                self.current.source_srid
                and self.current.target_srid != self.current.source_srid
            ):
                bbox_vertices = reproject_vertex_list(
                    bbox_vertices,
                    self.current.source_srid,
                    self.current.target_srid,
                )

            bbox = func.st_makeenvelope(
                bbox_vertices[0][0],
                bbox_vertices[0][1],
                bbox_vertices[1][0],
                bbox_vertices[1][1],
                self.current.target_srid,
            )

        # store extensions data - extra root properties, extra city objects
        self.current.extension_handler = ExtensionHandler(
            line_json.get("extensions")
        )

        # prepare extra properties coming from extensions
        # they will be placed in the extra_properties jsonb column
        extra_properties_obj = {}
        for prop_name in extra_root_properties:
            extra_properties_obj[prop_name] = line_json[prop_name]

        # check the occurring properties against
        # the extension defined extra properties
        check_root_properties(
            extra_root_properties,
            self.current.extension_handler.extra_root_properties,
        )

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
            bbox=bbox,
        )

        # compare to existing import metas
        # for example to detect inconsistent CRS from different files
        result_ok = import_meta.compare_existing(
            self.session,
            self.args.ignore_repeated_file,
            self.args.update_existing
        )
        if not result_ok:
            raise InvalidMetadataException()

        # add metadata to the database
        import_meta.__table__.schema = self.args.db_schema
        self.current.import_meta = import_meta
        self.session.add(import_meta)
        self.session.commit()

    def process_line(self, line_json) -> None:
        # unpack vertices for the cityobjects based on
        # the CityJSON transform
        # this is done once for the CityJSONFeature
        vertices = [
            transform_vertex(v, self.current.import_meta.transform)
            for v in line_json["vertices"]
        ]

        # reproject if needed
        source_target_srid = None
        if (
            self.current.source_srid
            and self.current.target_srid != self.current.source_srid
        ):
            source_target_srid = (
                self.current.source_srid,
                self.current.target_srid,
            )
            vertices = reproject_vertex_list(vertices, *source_target_srid)

        # list of relationships for the CityJSONFeature
        family_ties = []
        # objects for the CityJSONFeature
        cj_feature_objects = {}

        # create CityJSONObjects
        for obj_id, cityobj in line_json["CityObjects"].items():
            obj_to_update = None

            # optionally check if the object exists -
            # to skip it or update it
            if self.args.update_existing:
                existing = (
                    self.session.query(CjObjectModel)
                    .filter_by(object_id=obj_id)
                    .first()
                )

                if existing:
                    logger.warning(f"CityObject (id:{obj_id}) already exists. Updating.")  # noqa
                    obj_to_update = existing

            # get 3D geom, ground geom and bbox
            geometry, ground_geometry = self.get_geometries(
                obj_id, cityobj, vertices, source_target_srid
            )

            # check if the object type is allowed by the official
            # spec or extension
            check_result, message = check_object_type(
                cityobj.get("type"),
                self.cj_object_types,
                self.current.extension_handler.extra_city_objects,
            )
            if not check_result:
                logger.info(message)

            # update or insert the object
            # 'or None' is added to change empty json "{}" to database null
            if obj_to_update:
                cj_object = obj_to_update
                cj_object.type = cityobj.get("type")
                cj_object.attributes = cityobj.get("attributes") or None
                cj_object.geometry = geometry
                cj_object.ground_geometry = ground_geometry
                cj_object.import_meta = self.current.import_meta
            else:
                cj_object = CjObjectModel(
                    object_id=obj_id,
                    type=cityobj.get("type"),
                    attributes=cityobj.get("attributes") or None,
                    geometry=geometry,
                    ground_geometry=ground_geometry,
                )

                # add CityJson object to the database
                cj_object.__table__.schema = self.args.db_schema
                cj_object.import_meta_id = self.current.import_meta.id
                self.current.cj_objects.append(to_dict(cj_object))

            cj_feature_objects[obj_id] = cj_object

            # save children-parent links
            for child_id in cityobj.get("children", []):
                family_ties.append((obj_id, child_id))

                # delete previous ties if updating object
                if obj_to_update:
                    children = self.session.query(FamilyModel).filter_by(
                        child_id=child_id
                    )
                    children.delete()

        # create children-parent links after all objects
        # from the CityJSONFeature already exist
        for parent_id, child_id in family_ties:
            self.current.families.append({"parent_id": parent_id,
                                          "child_id": child_id})

    def process_file(self, filepath) -> None:
        """Process a single cityJSON file"""
        self.current = SingleFileImport(filepath)
        logger.info("Running import for file: %s", filepath)

        if filepath.lower() == "stdin":
            f = sys.stdin
        else:
            f = open(filepath, "rt")

        first_line = f.readline()
        first_line_json = json.loads(first_line.rstrip("\n"))
        if not is_cityjson_object(first_line_json):
            raise InvalidCityJSONObjectException()
        self.extract_import_metadata(first_line_json)
        for line in f.readlines():
            line_json = json.loads(line.rstrip("\n"))
            self.process_line(line_json)

        if self.current.cj_objects:
            obj_insert = (
                insert(CjObjectModel)
                .values(self.current.cj_objects)
                .on_conflict_do_nothing()
            )
            self.session.execute(obj_insert)

        if self.current.families:
            family_insert = (
                insert(FamilyModel)
                .values(self.current.families)
                .on_conflict_do_nothing()
            )  # noqa
            self.session.execute(family_insert)
        self.current.import_meta.finished_at = func.now()
        self.session.commit()

    def process_directory(self, dir_path) -> None:
        """Process all files in a directory."""
        logger.info("Running import for directory: %s", dir_path)
        ext = ".jsonl"
        for f in os.scandir(dir_path):
            if f.path.endswith(ext):
                self.process_file(f.path)

    def index_attributes(self):
        # postgres types to be used in type casted index
        postgres_type_mapping = {
            float: "float",
            str: "text",
            int: "int",
            bool: "boolean",
        }

        # python type mapping for the attributes based on sampled values
        type_mapping = CjObjectModel.get_attributes_and_types(self.session)

        # sql index command
        cmd_base = (
            "create index if not exists {table}_{attr_name}_idx "
            + "on {schema}.{table} using "
            + "btree(((attributes->>'{attr_name}')::{attr_type}))"
        )

        # prepare partial and non partial indexes in one list
        attributes = [
            (a, True) for a in self.args.partial_indexed_attributes
        ] + [  # noqa
            (a, False) for a in self.args.indexed_attributes
        ]

        # for each attribute to be indexed
        for attr_name, is_partial in attributes:
            msg = f"Indexing CityObject attribute: '{attr_name}'"
            if is_partial:
                msg += " with partial index"
            logger.info(msg)

            # get proper postgres type
            if attr_name in type_mapping:
                postgres_type = postgres_type_mapping[type_mapping[attr_name]]

                # prepare and run sql command
                if is_partial:
                    cmd = cmd_base
                    +" WHERE attributes->>'{attr_name}' IS NOT NULL"
                else:
                    cmd = cmd_base

                cmd = cmd.format(
                    table=CjObjectModel.__table__.name,
                    schema=CjObjectModel.__table__.schema,
                    attr_name=attr_name,
                    attr_type=postgres_type,
                )
                with self.engine.connect() as conn:
                    conn.execute(text(cmd))

            else:
                logger.warning(
                    f"Specified attribute to be indexed: '{attr_name}' does not exist"  # noqa
                )

    def get_geometries(
        self, obj_id, cityobj, vertices, source_target_srid
    ) -> Tuple[Optional[BaseGeometry], Optional[BaseGeometry]]:
        if "geometry" not in cityobj:
            return None, None

        # returned geometry is already in the required projection
        geometry = resolve_geometry_vertices(
            cityobj["geometry"],
            vertices,
            self.current.import_meta.geometry_templates,
            source_target_srid,
        )

        ground_geometry = get_ground_geometry(geometry, obj_id)

        if (ground_geometry is None) is False:
            if not self.current.target_srid:
                ground_geometry = func.st_geomfromtext(ground_geometry.wkt)
            else:
                ground_geometry = func.st_geomfromtext(
                    ground_geometry.wkt, self.current.target_srid
                )

        return geometry, ground_geometry
