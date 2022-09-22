from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Int
from sqlalchemy.ext.declarative import declared_attr, declarative_base

Base = declarative_base()
class BaseModel(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return dict(schema=cls.__name__[5:].upper())

    id = Column(Int, primary_key=True)