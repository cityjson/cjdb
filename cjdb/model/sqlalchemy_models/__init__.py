from geoalchemy2 import Geometry
from sqlalchemy import (Column, ForeignKey, Integer, String, UniqueConstraint,
                        func)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship


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
    objects = relationship("CjObjectModel",
                           backref='cj_metadata',
                           passive_deletes=True)

    def get_already_imported_files(self, session):
        # query already imported files,
        # return false if stdin.
        if self.source_file.lower() != "stdin":
            same_source_import = (
                session.query(CjMetadataModel)
                .filter_by(source_file=self.source_file)
                .filter(CjMetadataModel.finished_at.isnot(None))
            )

            return same_source_import
        return False

    def different_srid_meta(self, session):
        """Check if the CRS is consistent with previous imports."""
        return (
            session.query(CjMetadataModel)
            .filter(CjMetadataModel.srid != self.srid)
            .filter(CjMetadataModel.finished_at.isnot(None))
            .order_by(CjMetadataModel.finished_at.desc())
            .first()
        )


class CjObjectModel(BaseModel):
    __tablename__ = "city_object"
    __table_args__ = {"schema": "cjdb"}
    cj_metadata_id = Column(Integer, ForeignKey(CjMetadataModel.id, ondelete='CASCADE'))
    object_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    attributes = Column(NullableJSONB())
    geometry = Column(NullableJSONB())
    ground_geometry = Column(Geometry("MultiPolygon"))
    metadata_id_object_id_unique = UniqueConstraint(cj_metadata_id, object_id)

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

    @classmethod
    def get_max_id(cls, session) -> int:
        max = session.query(func.max(cls.id)).scalar()
        if max:
            return max
        else:
            return 0


class CityObjectRelationshipModel(BaseModel):
    __tablename__ = "city_object_relationships"
    __table_args__ = {"schema": "cjdb"}
    parent_id = Column(Integer, ForeignKey(CjObjectModel.id,
                                           ondelete='CASCADE'))
    child_id = Column(Integer, ForeignKey(CjObjectModel.id,
                                          ondelete='CASCADE'))

    parent = relationship(CjObjectModel,
                          foreign_keys=[parent_id],
                          post_update=True)
    child = relationship(CjObjectModel,
                         foreign_keys=[child_id],
                         post_update=True)

    parent_child_unique = UniqueConstraint(parent_id, child_id)
