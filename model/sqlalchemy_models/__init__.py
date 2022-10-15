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
    srid = Column(Integer)
    extensions = Column(NullableJSONB())
    extra_properties = Column(NullableJSONB())
    started_at = Column(TIMESTAMP, default=func.now())
    finished_at = Column(TIMESTAMP)
    bbox = Column(Geometry('POLYGON'))

    def compare_existing(self, session, ignore_repeated_file):
        result_ok = True

        # check if the file was already imported
        if self.source_file.lower() != 'stdin' and not ignore_repeated_file:
            same_source_import = session.query(ImportMetaModel)\
                .filter_by(source_file=self.source_file)\
                .filter(ImportMetaModel.finished_at.isnot(None))\
                .order_by(ImportMetaModel.finished_at.desc())\
                .first()
            if same_source_import:
                print(f"\nFile '{self.source_file}' was previously imported at {same_source_import.finished_at}.\n" \
                        "Use the -g flag to suppress this warning")
                user_answer = input("Should the import continue?\n [y / n]\n")
                if user_answer.lower() != "y":
                    return False
    
        # check if the CRS is consistent with other imports
        different_srid_meta = session.query(ImportMetaModel)\
                            .filter(ImportMetaModel.srid != self.srid)\
                            .filter(ImportMetaModel.finished_at.isnot(None))\
                            .order_by(ImportMetaModel.finished_at.desc())\
                            .first()

        if different_srid_meta:
            print("Inconsistent Coordinate Reference Systems detected")
            print(f"Currently imported SRID: {self.srid}")
            print(f"Recently imported SRID: {different_srid_meta.srid}")
            print("Use the '-I/--srid' flag to reproject everything to a single specified CRS.")
            return False

        return result_ok


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

