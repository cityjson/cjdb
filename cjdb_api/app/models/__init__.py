from flask_sqlalchemy import BaseQuery
from app.db import db


class BaseModel(db.Model):
    __abstract__ = True
    query: BaseQuery

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_by_id(cls, _id: str):
        return cls.query.filter_by(id=_id).first()

    def save(self):
        db.session.add(self)
        db.session.commit()


class CityJsonModel(BaseModel):
    __tablename__ = "cityjsonobjects"
    __table_args__ = {"schema": "cjdb"}

    # define columns here
    # this IS the data model for the table
    id = db.Column(db.String, primary_key=True)

