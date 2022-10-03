from flask import Blueprint
from flask_restful import Api
from cjdb_api.app.resources import querying

from cjdb_api.app.resources.querying import QueryByAttributeResource, all

api_blueprint = Blueprint("api", __name__)
api = Api(api_blueprint)

api.add_resource(all, "/all")
# todo add more resources when they are ready