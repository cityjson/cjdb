from flask import Blueprint
from flask_restful import Api
from cjdb_api.app.resources import querying

from cjdb_api.app.resources.querying import QueryByAttributeResource, all, QueryById, QueryByAnything

api_blueprint = Blueprint("api", __name__)
api = Api(api_blueprint)

api.add_resource(all, "/all")
api.add_resource(QueryById, "/query_id/<string:obj_id>")
api.add_resource(QueryByAnything, "/<string:attrib>/<string:value>")

# todo add more resources when they are ready