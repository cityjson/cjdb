from flask import request, jsonify
from flask_restful import Resource, reqparse
from sqlalchemy import update
import ast

from cjdb_api.app.db import session, engine
from cjdb_api.app.resources import cityjson_schema, cityjson_list_schema, FIELD_MAPPING, what_type, in_database, parse_json
from model.sqlalchemy_models import CjObjectModel, FamilyModel, ImportMetaModel


def type_mapping():
    global tm
    tm = CjObjectModel.get_attributes_and_types(session)
    for attr_name in tm:
        if tm[attr_name] == str:
            FIELD_MAPPING[attr_name] = CjObjectModel.attributes[attr_name].as_string()
        if tm[attr_name] == bool:
            FIELD_MAPPING[attr_name] = CjObjectModel.attributes[attr_name].as_boolean()
        if tm[attr_name] == int:
            FIELD_MAPPING[attr_name] = CjObjectModel.attributes[attr_name].as_integer()
        if tm[attr_name] == float:
            FIELD_MAPPING[attr_name] = CjObjectModel.attributes[attr_name].as_float()
    return tm


# Add an attribute to a CityJSON object.
class AddAttribute(Resource):
    @classmethod
    def get(cls):
        # required parameters: object_id, attribute, value
        args = request.args.to_dict()
        object_id, attrib, new_value = args['object_id'], args['attribute'], args['value']

        if attrib in FIELD_MAPPING:
            return {"message": "This object already has " + attrib + ". If you want to Update the attribute, use /update instead"}, 404

        if object_id is Null:
            return {"message": "Invalid parameter. Please include the right object_id."}, 404
        elif object_id == "all":
            obs = session.query(CjObjectModel)
            show = session.query(CjObjectModel).limit(50)
        else:
            in_database(object_id)
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes
            else:
                listObj = {}
            if attrib == "FootPrintArea":
                with engine.connect() as connection:
                    area_pointer = connection.execute(object.bbox.ST_Area())

                for row in area_pointer:
                    value = row[0]
            else:
                value = what_type(attrib, new_value)
                print(type(value))

            listObj[attrib] = value
            u = update(CjObjectModel)
            u = u.values({"attributes": listObj})
            u = u.where(CjObjectModel.object_id == object.object_id)
            engine.execute(u)

        if object_id == "all":
            show = session.query(CjObjectModel).limit(50)
            output = parse_json(cityjson_list_schema.dump(show))
        else:
            output = parse_json(cityjson_list_schema.dump(obs))
        
        return jsonify(output)


# Update the value of an attribute from a CityJSON object.
class UpdateAttrib(Resource):
    @classmethod
    def get(cls):
        # required parameters: object_id, attribute, value
        args = request.args.to_dict()
        object_id, attrib, new_value = args['object_id'], args['attribute'], args['value']

        if type(ast.literal_eval(new_value)) != tm[attrib]:
            print("type of type map = ", tm[attrib], "input type = ", type(ast.literal_eval(new_value)))
            return {"message": "Input type and mapped type don't match"}, 404

        if attrib not in FIELD_MAPPING and attrib != "FootPrintArea":
            return {"message": "This attribute does not exist, to create a new attribute, use /add instead"}, 404
    
        if object_id is Null:
            return {"message": "Invalid parameter. Please include the right object_id."}, 404
        elif object_id == "all":
            obs = session.query(CjObjectModel).all()
        else:
            in_database(object_id)
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes

                if attrib == "FootPrintArea":
                    with engine.connect() as connection:
                        area_pointer = connection.execute(object.bbox.ST_Area())

                    for row in area_pointer:
                        value = row[0]
                else:
                    value = what_type(attrib, new_value)
                    print(type(value))

                listObj[attrib] = value
                u = update(CjObjectModel)
                u = u.values({"attributes": listObj})
                u = u.where(CjObjectModel.object_id == object.object_id)
                engine.execute(u)

        if object_id == "all":
            show = session.query(CjObjectModel).limit(50)
            output = parse_json(cityjson_list_schema.dump(show))
        else:
            output = cityjson_list_schema.dump(obs)
            
        return parse_json(output)
