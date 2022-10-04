from flask import Blueprint
from flask_restful import Api
from cjdb_api.app.resources import querying

from cjdb_api.app.resources.querying import all, QueryByAttribute, CalculateFootprint, CalculateVolume, AddAttribute

api_blueprint = Blueprint("api", __name__)
api = Api(api_blueprint)

api.add_resource(all, "/all")
# api.add_resource(QueryById, "/query_id/<string:obj_id>")
api.add_resource(QueryByAttribute, "/<string:attrib>/<string:value>")
api.add_resource(CalculateFootprint, "/area/<string:object_id>")
api.add_resource(CalculateVolume, "/volume/<string:object_id>")
api.add_resource(AddAttribute, "/update")

# todo add more resources when they are ready