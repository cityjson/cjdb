from flask import Blueprint
from flask_restful import Api
from cjdb_api.app.resources import server, querying, updating, deletion

blueprint = Blueprint("master", __name__)
api = Api(blueprint)

# Server
api.add_resource(server.Home, "/")
api.add_resource(server.Swagger, "/api", endpoint='api')
api.add_resource(querying.Show, "/collections", endpoint='collections')

# Query
api.add_resource(querying.Item, "/collections/items", endpoint='items')
api.add_resource(querying.CQL_query, "/collections/cql", endpoint='cql')
api.add_resource(querying.CalculateFootprint, "/footprint", endpoint='footprint')

# Add, Update
api.add_resource(updating.AddAttribute, "/operation/add")
api.add_resource(updating.UpdateAttrib, "/operation/update")

# Deletion
api.add_resource(deletion.DelAttrib, "/operation/delete")
api.add_resource(deletion.DelObject, "/operation/delete/object")
