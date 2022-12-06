from flask import Blueprint
from flask_restful import Api
from cjdb_api.app.resources import server, querying, updating, deletion


v1_api_blueprint = Blueprint("api", __name__)
v1_api = Api(v1_api_blueprint)


# - Query by Attribute
v1_api.add_resource(query.Show, "/show")
v1_api.add_resource(query.FilterAttributes, "/filter/<string:attrib>/<string:operator>/<string:value>")
v1_api.add_resource(query.QueryByAttribute, "/select/<string:attrib>/<string:value>")
v1_api.add_resource(query.GetInfo, "/info/<string:attrib>/<string:object_id>")

# - Query by Parent / Child
v1_api.add_resource(query.GetChildren, "/children/<string:object_id>")
v1_api.add_resource(query.GetParent, "/parent/<string:object_id>")

# - Query by Geometry
v1_api.add_resource(query.QueryByPoint, "/point/<string:coor>")
v1_api.add_resource(query.QueryByBbox, "/bbox/<string:coor>")

# - Query by CQL
v1_api.add_resource(query.CQL_query, "/cql")

# - Calculate Footprint
v1_api.add_resource(querying.CalculateFootprint, "/footprint", endpoint='footprint')

# - Update
v1_api.add_resource(updating.AddAttribute, "/operation/add")
v1_api.add_resource(updating.UpdateAttrib, "/operation/update")

# - Deletion
v1_api.add_resource(deletion.DelAttrib, "/operation/delete")
v1_api.add_resource(deletion.DelObject, "/operation/delete/object")
