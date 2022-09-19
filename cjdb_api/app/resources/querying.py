from flask_restful import Resource
from app.models import CityJsonModel
from app.schemas import CityJsonSchema

cityjson_schema = CityJsonSchema()

class QueryByIdResource(Resource):
    @classmethod
    def get(cls, obj_id: str):
        cj_object = CityJsonModel.get_by_id(obj_id)

        if not cj_object:
            return {"message": "Object not found"}, 404

        return cityjson_schema.dump(cj_object)


class QueryByAttributeResource(Resource):
    pass
    # todo: querying by attribute


class QueryByGeometry(Resource):
    pass
    # todo: querying by geometry (bbox?)
