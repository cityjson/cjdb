from model.sqlalchemy_models import Base
from sqlalchemy import Column, String

class ImportMetaModel(Base):
    __tablename__ = ''
    __table_args__ = {'schema':'cjdb'}
    source_file = Column(String)
    version = Column(String(10), nullable=False)
    version varchar(10) not null,
    transform jsonb not null,
    metadata jsonb,
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    bbox geometry not null--2d bbox of the entire file

#sqlalchemy batch insert performance