from flask import Blueprint
from flask_restful import Api
from cjdb_api.app.resources import querying

import  cjdb_api.app.resources.querying as query
#import all, QueryByAttribute, CalculateFootprint, CalculateVolume, AddAttribute

api_blueprint = Blueprint("api", __name__)
api = Api(api_blueprint)

#finished
api.add_resource(query.all, "/all")
api.add_resource(query.QueryByAttribute, "/select/<string:attrib>/<string:value>")
api.add_resource(query.GetInfo, "/info/<string:attrib>/<string:object_id>")
api.add_resource(query.QueryByPoint, "/point/<string:coor>")
api.add_resource(query.QueryByBbox, "/bbox/<string:coor>")
api.add_resource(query.CalculateFootprint, "/area/<string:object_id>")

#in progress
api.add_resource(query.CalculateVolume, "/volume/<string:object_id>")
api.add_resource(query.AddAttribute, "/update")
api.add_resource(query.FilterAttributes, "/filter/<string:attrib>/<string:operator>/<string:value>")
api.add_resource(query.Geometry, "/geometry")
api.add_resource(query.CQL_query, "/cql")
# api.add_resource(query.Sequel, "/sql")

# todo add more resources when they are ready
