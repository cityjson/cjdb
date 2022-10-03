from flask_restful import Resource
from model.sqlalchemy_models import CjObjectModel
from cjdb_api.app.schemas import CityJsonSchema
from cjdb_api.app.db import session
cityjson_schema = CityJsonSchema()
cityjson_list_schema = CityJsonSchema(many=True)

class all(Resource):
    @classmethod
    def get(cls):
        # cj_object = CjObjectModel.object_id(obj_id)
        all = session.query(CjObjectModel).all()


        if not all:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(all)

class QueryById(Resource):
    @classmethod
    def get(cls, obj_id: str):

        cj_object = session.query(CjObjectModel).filter(CjObjectModel.object_id == str(obj_id))

        if not cj_object:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(cj_object)

class QueryByAnything(Resource):
    @classmethod
    def get(cls, attrib: str, value: str):
        cj_object = session.query(CjObjectModel).filter(getattr(CjObjectModel, attrib) == str(value))

        if not cj_object:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(cj_object)

class QueryByAttributeResource(Resource):
    pass
    # todo: querying by attribute



class QueryByGeometry(Resource):
    pass
    # todo: querying by geometry (bbox?)
