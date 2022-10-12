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


class ImportMetaModel(BaseModel):
    __tablename__ = 'import_meta'
    __table_args__ = {'schema':'cjdb'}
    source_file = Column(String)
    version = Column(String(10), nullable=False)
    transform = Column(JSONB)
    meta = Column(JSONB, name="metadata")
    extensions = Column(JSONB)
    extra_properties = Column(JSONB)
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
    attributes = Column(JSONB)
    geometry = Column(JSONB)
    parents = Column(JSONB)
    children = Column(JSONB)
    bbox = Column(Geometry('POLYGON'))

    import_meta = relationship(ImportMetaModel)

