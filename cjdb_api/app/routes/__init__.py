from flask import Blueprint
from flask_restful import Api
from cjdb_api.app.resources import querying

from cjdb_api.app.resources.querying import QueryByAttributeResource, QueryByIdResource

api_blueprint = Blueprint("api", __name__)
api = Api(api_blueprint)

api.add_resource(QueryByIdResource, "/query_id/<string:obj_id>")
# todo add more resources when they are ready