from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy import Column, ForeignKey, \
    String, func, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from geoalchemy2 import Geometry

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    # @declared_attr
    # def __table_args__(cls):
    #     return dict(schema=cls.__name__[5:].upper())

    id = Column(Integer, primary_key=True)


class ImportMetaModel(BaseModel):
    __tablename__ = 'import_meta'
    __table_args__ = {'schema':'cjdb'}
    source_file = Column(String)
    version = Column(String(10), nullable=False)
    transform = Column(JSONB)
    meta = Column(JSONB, name="metadata")
    started_at = Column(TIMESTAMP, default=func.now())
    finished_at = Column(TIMESTAMP)
    bbox = Column(Geometry('POLYGON'))


class CjFeatureModel(BaseModel):
    __tablename__ = 'cj_feature'
    __table_args__ = {'schema':'cjdb'}
    import_meta_id = Column(Integer, ForeignKey(ImportMetaModel.id))
    feature_id = Column(String, nullable=False, unique=True)
    vertices = Column(JSONB)
    bbox = Column(Geometry('POLYGON'))

    import_meta = relationship(ImportMetaModel)


class CjObjectModel(BaseModel):
    __tablename__ = 'cj_object'
    __table_args__ = {'schema':'cjdb'}
    cj_feature_id = Column(Integer, ForeignKey(CjFeatureModel.id))
    object_id = Column(String, nullable=False, unique=True)
    object = Column(JSONB)
    bbox = Column(Geometry('POLYGON'))

    cj_feature = relationship(CjFeatureModel)

