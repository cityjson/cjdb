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
    def get(cls):
        # cj_object = CjObjectModel.object_id(obj_id)
        all = session.query(CjObjectModel).all()


        if not all:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(all)

class QueryByAttributeResource(Resource):
    pass
    # todo: querying by attribute


class QueryByGeometry(Resource):
    pass
    # todo: querying by geometry (bbox?)
