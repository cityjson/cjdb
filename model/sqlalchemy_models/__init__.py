from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy import Column, ForeignKey, \
    String, func, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from geoalchemy2 import Geometry

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

def NullableJSONB():
    return JSONB(none_as_null=True)

class ImportMetaModel(BaseModel):
    __tablename__ = 'import_meta'
    __table_args__ = {'schema':'cjdb'}
    source_file = Column(String)
    version = Column(String(10), nullable=False)
    transform = Column(NullableJSONB())
    meta = Column(JSONB, name="metadata")
    extensions = Column(NullableJSONB())
    extra_properties = Column(NullableJSONB())
    started_at = Column(TIMESTAMP, default=func.now())
    finished_at = Column(TIMESTAMP)
    bbox = Column(Geometry('POLYGON'))

    def compare_existing(self):
        pass
        # todo check existing import meta records
        # if there is already a file with this name, ask for confirmation
        # if the CRS doesn't match, tell the user that he has to specify one crs, which will be applied for all
        


class CjObjectModel(BaseModel):
    __tablename__ = 'cj_object'
    __table_args__ = {'schema':'cjdb'}
    import_meta_id = Column(Integer, ForeignKey(ImportMetaModel.id))
    object_id = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)
    attributes = Column(NullableJSONB())
    geometry = Column(NullableJSONB())
    parents = Column(NullableJSONB())
    children = Column(NullableJSONB())
    bbox = Column(Geometry('POLYGON'))

    import_meta = relationship(ImportMetaModel)

