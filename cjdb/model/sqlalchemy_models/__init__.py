import sys

from geoalchemy2 import Geometry
from sqlalchemy import (Column, ForeignKey, Integer, String, UniqueConstraint,
                        func)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

from cjdb.logger import logger

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)


def NullableJSONB():
    return JSONB(none_as_null=True)


class CjMetadataModel(BaseModel):
    __tablename__ = "cj_metadata"
    __table_args__ = {"schema": "cjdb"}
    source_file = Column(String)
    version = Column(String(10), nullable=False)
    meta = Column(JSONB, name="metadata")
    transform = Column(NullableJSONB())
    geometry_templates = Column(NullableJSONB())
    srid = Column(Integer)
    extensions = Column(NullableJSONB())
    extra_properties = Column(NullableJSONB())
    started_at = Column(TIMESTAMP, default=func.now())
    finished_at = Column(TIMESTAMP)
    bbox = Column(Geometry("Polygon"))

    def compare_existing(self, session, ignore_repeated_file, update_existing):
        result_ok = True

        # check if the file was already imported
        if self.source_file.lower() != "stdin" and \
           not ignore_repeated_file and \
           not update_existing:
            same_source_import = (
                session.query(CjMetadataModel)
                .filter_by(source_file=self.source_file)
                .filter(CjMetadataModel.finished_at.isnot(None))
                .order_by(CjMetadataModel.finished_at.desc())
                .first()
            )
            if same_source_import:
                logger.warning(
                    "File %s was previously imported at %s. "
                    "Use the -g flag to suppress this warning.",
                    self.source_file,  same_source_import.finished_at
                )

                user_answer = input(
                    "Should the import continue? "
                    "Already imported City Objects will be skipped. "
                    "If you want to update them instead "
                    "use the flag --update-existing. \n"
                    " [y / n]\n"
                )
                if user_answer.lower() != "y":
                    logger.info("Import process terminated by user.")
                    sys.exit(1)

        # check if the CRS is consistent with other imports
        different_srid_meta = (
            session.query(CjMetadataModel)
            .filter(CjMetadataModel.srid != self.srid)
            .filter(CjMetadataModel.finished_at.isnot(None))
            .order_by(CjMetadataModel.finished_at.desc())
            .first()
        )

        if different_srid_meta:
            logger.error("Inconsistent Coordinate Reference Systems detected."
                         "\nCurrently imported SRID: %s \n"
                         "Recently imported SRID: %s "
                         "\nUse the '-I/--srid' flag to reproject everything "
                         "to a single specified CRS or modify source data.",
                         self.srid, different_srid_meta.srid
                         )
            return False

        return result_ok


class CjObjectModel(BaseModel):
    __tablename__ = "city_object"
    __table_args__ = {"schema": "cjdb"}
    cj_metadata_id = Column(Integer, ForeignKey(CjMetadataModel.id))
    object_id = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)
    attributes = Column(NullableJSONB())
    geometry = Column(NullableJSONB())
    ground_geometry = Column(Geometry("MultiPolygon"))
    cj_metadata = relationship(CjMetadataModel)

    @classmethod
    def get_attributes_and_types(cls, session):
        # sample attributes for each object type
        # this is needed to create proper indexes and also
        # to use those indexes when querying
        sampled_objects = (
            session.query(cls)
            .distinct(cls.type)
            .filter(cls.attributes.isnot(None))
            .order_by(cls.type, cls.id.desc())
            .all()
        )

        # create type mapping for each attribute appearing
        # across all object types this considers that different
        # object types have different attributes if same object
        # types have different attributes, then this will not work correctly
        type_mapping = {}
        if sampled_objects:
            for cj_obj in sampled_objects:
                for attr_name, value in cj_obj.attributes.items():
                    type_mapping[attr_name] = type(value)

        return type_mapping


class CityObjectRelationshipModel(BaseModel):
    __tablename__ = "city_object_relationships"
    __table_args__ = {"schema": "cjdb"}
    parent_id = Column(String, ForeignKey(CjObjectModel.object_id))
    child_id = Column(String, ForeignKey(CjObjectModel.object_id))

    parent = relationship(CjObjectModel,
                          foreign_keys=[parent_id],
                          post_update=True)
    child = relationship(CjObjectModel,
                         foreign_keys=[child_id],
                         post_update=True)

    parent_child_unique = UniqueConstraint(parent_id, child_id)
