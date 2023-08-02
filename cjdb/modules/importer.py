import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from shapely.geometry.base import BaseGeometry
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

import cjdb.modules.exceptions as exceptions
from cjdb.logger import logger
from cjdb.model.sqlalchemy_models import (BaseModel,
                                          CityObjectRelationshipModel,
                                          CjMetadataModel, CjObjectModel)
from cjdb.modules.checks import (check_object_type,
                                 check_root_properties)
from cjdb.modules.extensions import ExtensionHandler
from cjdb.modules.geometric import (get_ground_geometry, get_srid,
                                    reproject_vertex_list,
                                    resolve_geometry_vertices,
                                    transform_vertex)
from cjdb.modules.utils import (find_extra_properties, get_city_object_types,
                                is_cityjson_object, is_valid_file, to_dict)


# class to store variables per file import - for clarity
class SingleFileImport:
    def __init__(self, file="stdin"):
        self.file = file
        self.source_srid = None
        self.cj_metadata = None  # meta read from the file
        self.target_srid = None
        self.extension_handler = (
            None  # data about extensions - extra properties, root attributes
        )
        self.city_objects = []
        self.families = []


# importer class called once per whole import
class Importer:
    def __init__(self, engine, filepath, db_schema, input_srid,
                 indexed_attributes, partial_indexed_attributes,
                 ignore_repeated_file, overwrite, transform):
        self.engine = engine
        self.filepath = filepath
        self.db_schema = db_schema
        self.input_srid = input_srid
        self.indexed_attributes = indexed_attributes
        self.partial_indexed_attributes = partial_indexed_attributes
        self.ignore_repeated_file = ignore_repeated_file
        self.overwrite = overwrite
        self.max_id = 0
        self.processed = dict()
        self.transform = transform

        # get allowed types for validation
        self.city_object_types = get_city_object_types()
        self.current = SingleFileImport()

        for table in BaseModel.metadata.tables.values():
            table.schema = self.db_schema

    def __enter__(self):
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def run_import(self) -> None:
        self.prepare_database()
        self.max_id = CjObjectModel.get_max_id(self.session)
        self.parse_cityjson()
        self.session.commit()
        # post import operations like clustering, indexing...
        self.post_import()
        self.session.commit()

    def prepare_database(self) -> None:
        """Adds the postgis extension and creates
        the schema and the tables."""
        with self.engine.connect() as conn:
            conn.execute(text("""CREATE EXTENSION IF NOT EXISTS postgis"""))
            conn.execute(text(f"""CREATE SCHEMA IF NOT EXISTS
                                  {self.db_schema}"""))
            conn.commit()
        # create all tables defined as SqlAlchemy models
        for table in BaseModel.metadata.tables.values():
            table.create(self.engine, checkfirst=True)

    def parse_cityjson(self) -> None:
        """Parses the input path."""
        source_path = self.filepath

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
            cmd = f.read().format(schema=self.db_schema)
        with self.engine.connect() as conn:
            conn.execute(text(cmd))
        self.index_attributes()

    def set_target_srid(self) -> None:
        """
        This function sets the  target SRID for the file being imported,
        i.e. the SRID for the geometries to be transformed to.
        If the flag --transform is used then the geometries should
        be transformed from the source SRID to the SRID of the existing
        schema and the target SRID is set to the SRID of the schema.
        If no --transform flag is used then the geometries do not need to
        be transformed and the target SRID is set to the source SRID.
        """
        if not self.transform:
            self.current.target_srid = self.current.source_srid
        else:
            schema_srid = (self.session.query(CjMetadataModel)
                           .filter(CjMetadataModel.finished_at.isnot(None))
                           .order_by(CjMetadataModel.finished_at.desc())
                           .first()
                           )
            if schema_srid:
                self.current.target_srid = schema_srid.srid
            else:
                raise exceptions.NoSchemaSridException()
        logger.debug("Target SRID: %s", self.current.target_srid)

    def set_source_srid(self, line_json) -> None:
        """
        This function sets the SRID of the file being imported.
        Usually the SRID of the file is defined in the "referenceSystem"
        member of the json's metadata. If the file does have such member,
        the user can use the flag -I/--srid to set the SRID of the file.
        If both metadata-defined and user-defined SRIDs exist then the
        user-defined SRID overwrites the metadata-SRID.
        """
        self.current.source_srid = get_srid(
            line_json["metadata"].get("referenceSystem")
        )

        if self.input_srid:
            if self.current.source_srid:
                logger.warning("""Input SRID is different than the SRID in the 
                                file's metadata:
                                Input SRID: %s
                                Source SRID: %s
                                Source SRID will be overwritten.""",
                               self.input_srid,
                               self.current.source_srid)

            self.current.source_srid = self.input_srid
        else:
            if not self.current.source_srid:
                raise exceptions.MissingCRSException()

        logger.debug("SRID of input file: %s", self.current.source_srid)

    def extract_cj_metadatadata(self, line_json):
        if "metadata" not in line_json:
            raise exceptions.InvalidMetadataException(
                "The file should contain a member"
                "'metadata', in the first object")

        extra_root_properties = find_extra_properties(line_json)

        self.set_source_srid(line_json)
        self.set_target_srid()

        # calculate dataset bbox based on geographicalExtent
        bbox = None
        if "geographicalExtent" in line_json["metadata"]:
            bbox_coords = line_json["metadata"]["geographicalExtent"]
            bbox_vertices = [bbox_coords[:3], bbox_coords[3:]]

            if (
                self.current.target_srid
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
        cj_metadata = CjMetadataModel(
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

        if cj_metadata.source_file.lower() != "stdin":
            # compare to existing import metas
            imported_files = cj_metadata.get_already_imported_files(
                self.session
            )

            if (
                self.ignore_repeated_file and
                    imported_files.first() and 
                    not self.overwrite):
                logger.warning("File already imported. Skipping...")
                return False
            elif imported_files.first() and not self.overwrite:
                logger.warning(
                    "A file with the same name (%s) was previously "
                    "imported on %s. Use the --ignore-repeated-file "
                    "to skip already imported files.",
                    cj_metadata.source_file, imported_files.first().finished_at
                )
                user_answer = input(
                    "Should the import continue? "
                    "Already imported city objects will be skipped. "
                    "If you want to overwrite them instead "
                    "use the flag --overwrite. \n"
                    " [y / n]\n"
                )
                if user_answer.lower() != "y":
                    logger.warning(
                        f"Import of file {cj_metadata.source_file}"
                        "skipped by user.")
                    return False
            elif imported_files.first() and self.overwrite:
                logger.warning(
                    "File already imported. Overwriting all objects"
                    f" from source file {cj_metadata.source_file}")
                imported_files.delete()

        different_srid = cj_metadata.different_srid_meta(self.session)
        if different_srid:
            logger.error("Not matching coordinate Reference Systems"
                         "\nCurrently imported SRID: %s"
                         "\nRecently imported SRID: %s",
                         cj_metadata.srid, different_srid.srid)
            raise exceptions.InconsistentCRSException()

        # add metadata to the database
        cj_metadata.__table__.schema = self.db_schema
        self.current.cj_metadata = cj_metadata
        self.session.add(cj_metadata)
        self.session.commit()
        return True

    def process_line(self, line_json) -> None:
        # unpack vertices for the cityobjects based on
        # the CityJSON transform
        # this is done once for the CityJSONFeature
        vertices = [
            transform_vertex(v, self.current.cj_metadata.transform)
            for v in line_json["vertices"]
        ]

        # reproject if needed
        source_target_srid = None
        if (
            self.current.target_srid != self.current.source_srid
        ):
            source_target_srid = (
                self.current.source_srid,
                self.current.target_srid,
            )
            vertices = reproject_vertex_list(vertices, *source_target_srid)

        # list of relationships for the CityJSONFeature
        city_object_relationships_ties = []
        # objects for the CityJSONFeature
        cj_feature_objects = {}

        # create CityJSONObjects
        for obj_id, cityobj in line_json["CityObjects"].items():

            # get 3D geom, ground geom and bbox
            geometry, ground_geometry = self.get_geometries(
                obj_id, cityobj, vertices, source_target_srid
            )

            # check if the object type is allowed by the official
            # spec or extension
            check_result, message = check_object_type(
                cityobj.get("type"),
                self.city_object_types,
                self.current.extension_handler.extra_city_objects,
            )
            if not check_result:
                logger.info(message)

            # update or insert the object
            # 'or None' is added to change empty json "{}" to database null

            city_object_id = self.processed.get(obj_id, None)
            if not city_object_id:
                self.max_id = self.max_id + 1
                self.processed[obj_id] = self.max_id
                city_object_id = self.max_id
            city_object = CjObjectModel(
                id=city_object_id,
                object_id=obj_id,
                type=cityobj.get("type"),
                attributes=cityobj.get("attributes") or None,
                geometry=geometry,
                ground_geometry=ground_geometry,
            )

            # add CityJson object to the database
            city_object.__table__.schema = self.db_schema
            city_object.cj_metadata_id = self.current.cj_metadata.id
            self.current.city_objects.append(to_dict(city_object))

            cj_feature_objects[obj_id] = city_object

            # save children-parent links
            for child_id in cityobj.get("children", []):
                child_unique_id = self.processed.get(child_id, None)
                if child_unique_id:
                    city_object_relationships_ties.append((city_object_id,
                                                           child_unique_id))
                else:
                    self.max_id = self.max_id + 1
                    self.processed[child_id] = self.max_id
                    city_object_relationships_ties.append((city_object_id,
                                                           self.max_id))

        # create children-parent links after all objects
        # from the CityJSONFeature already exist
        for parent_id, child_id in city_object_relationships_ties:
            self.current.families.append({"parent_id": parent_id,
                                          "child_id": child_id})

    def process_file(self, filepath) -> bool:
        """Process a single cityJSON file"""
        self.current = SingleFileImport(filepath)
        logger.info("Running import for file: %s", filepath)

        if filepath.lower() == "stdin":
            f = sys.stdin
        else:
            if not is_valid_file(filepath):
                raise exceptions.InvalidFileException()
            f = open(filepath, "rt")

        first_line = f.readline()
        first_line_json = json.loads(first_line.rstrip("\n"))
        if not is_cityjson_object(first_line_json):
            raise exceptions.InvalidCityJSONObjectException()
        metadata_ok = self.extract_cj_metadatadata(first_line_json)
        if not metadata_ok:
            return False
        for line in f.readlines():
            line_json = json.loads(line.rstrip("\n"))
            self.process_line(line_json)

        if self.current.city_objects:
            obj_insert = (
                insert(CjObjectModel)
                .values(self.current.city_objects)
                .on_conflict_do_nothing()
            )
            self.session.execute(obj_insert)
        self.session.commit()

        if self.current.families:
            city_object_relationships_insert = (
                insert(CityObjectRelationshipModel)
                .values(self.current.families)
                .on_conflict_do_nothing()
            )
            self.session.execute(city_object_relationships_insert)
        self.current.cj_metadata.finished_at = func.now()
        self.session.commit()
        logger.info(f"File {filepath} imported successfully.")
        return True

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
            "on {schema}.{table} using "
            "btree(((attributes->>'{attr_name}')::{attr_type}))"
        )

        # prepare partial and non partial indexes in one list
        attributes = [
            (a, True) for a in self.partial_indexed_attributes
        ] + [  # noqa
            (a, False) for a in self.indexed_attributes
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
            self.current.cj_metadata.geometry_templates,
            source_target_srid,
        )

        ground_geometry = get_ground_geometry(geometry, obj_id)

        if ground_geometry is not None:
            if not self.current.target_srid:
                ground_geometry = func.st_geomfromtext(ground_geometry.wkt)
            else:
                ground_geometry = func.st_geomfromtext(
                    ground_geometry.wkt, self.current.target_srid
                )

        return geometry, ground_geometry
