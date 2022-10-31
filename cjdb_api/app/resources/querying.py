from flask import render_template, make_response, request, jsonify
from flask_restful import Resource
from model.sqlalchemy_models import CjObjectModel, FamilyModel, ImportMetaModel
from cjdb_api.app.schemas import CjObjectSchema
from cjdb_api.app.db import session, engine
from sqlalchemy.sql import text
from pygeofilter.parsers.ecql import parse as parse_ecql
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy import update, delete
import ast

import calendar
import time
from datetime import datetime

cityjson_schema = CjObjectSchema()
cityjson_list_schema = CjObjectSchema(many=True)

global FIELD_MAPPING
FIELD_MAPPING = {
    "object_id": CjObjectModel.object_id,
    "type": CjObjectModel.type,
    "geometry": CjObjectModel.geometry,
    "ground_geometry": CjObjectModel.ground_geometry,
}

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


def what_type(attrib, new_value):
    if attrib in tm:
        if tm[attrib] == str:
            return new_value
        if tm[attrib] == bool:
            return bool(new_value)
        if tm[attrib] == int:
            return int(new_value)
        if tm[attrib] == float:
           return float(new_value)

    else:
        tp = ast.literal_eval(new_value)
        FIELD_MAPPING[attrib] = type(tp)
        return tp

def delete_children(has_children):
    for child in has_children:
        has_child = session.query(FamilyModel).join(CjObjectModel, CjObjectModel.object_id == FamilyModel.parent_id).filter(FamilyModel.parent_id == child.child_id).all()
        while has_child:
            delete_children(has_child)
        u = delete(FamilyModel)
        u = u.where(FamilyModel.parent_id == child.parent_id)
        c = delete(CjObjectModel)
        c = c.where(CjObjectModel.object_id == child.child_id)
        engine.execute(u)
        engine.execute(c)

def time_stamp():
    current_GMT = time.gmtime()
    timestamp = calendar.timegm(current_GMT)
    date_time = datetime.fromtimestamp(timestamp)
    str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")

    return str_date_time

def parse_json(data, datatype='multiple'):
    # to be added: children, parents
    if datatype == 'single':
        type_name = 'Feature'
    elif datatype == 'multiple':
        type_name = 'Feature collection'

    dict = {
        'type': type_name,
        'links': [],
        'numberReturned': len(data),
        'timeStamp': time_stamp(),
        'feature': data,
    }
    return dict

def parse_html(parse):
    # convert cityjson schema to a list of headers and a list of lists of values
    headings = list(parse[0].keys())
    data = []
    for item in parse:
        data.append(list(item.values()))

    return headings, data


#Select a certain amount of objects in the database
class show(Resource):
    @classmethod
    def get(cls, lim: int):
        all = session.query(CjObjectModel).limit(lim).all()

        if not all:
            return {"message": "Object not found"}, 404

        headings, data = parse_html(cityjson_list_schema.dump(all))

        return make_response(render_template("all.html", headings=headings, data=data))

# Item load query parameters, not path parameters    
class Item(Resource):
    @classmethod
    def get(cls):
        args = request.args.to_dict()
        # step 1: extract format
        if 'f' in args:
            format = args['f']
            args.pop('f')

        print(args)

        if len(args) == 0:
            cj_object = session.query(CjObjectModel).limit(50).all()
        elif len(args) > 1:
            print("The query parameters are wrong.")
            # return {"message": "The query parameters are wrong."}

        # step 2: which attribute to query
        # column: id, object_id
        # column: import_meta_id, type
        # attributes: attributes.xxx
        # family: parent, child
        # geometries: point

        key_list = list(args.keys())
        if key_list == {}:
            cj_object = session.query(CjObjectModel).limit(50).all()

        else:
            attrib = str(key_list[0])
            value = str(args[attrib])
            print(key_list)

            att = attrib.split('.')
            if len(att) > 1:
                print('task: attribute')
                cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[att[1]] == value).limit(50)
            elif attrib == 'parent_id':  # get children, value = object_id
                print('task: parent_id')
                cj_object = session.query(CjObjectModel).join(FamilyModel,FamilyModel.child_id == CjObjectModel.object_id).filter(FamilyModel.parent_id == value).all()
            elif attrib == 'child_id':  # get parents, value = object_id
                print('task:child_id')
                cj_object = session.query(CjObjectModel).join(FamilyModel,FamilyModel.parent_id == CjObjectModel.object_id).filter(FamilyModel.child_id == value).all()
            elif attrib == 'id' or 'object_id' or 'import_meta_id' or 'type':
                print('task:id / object_id / import_meta_id / type')
                cj_object = session.query(CjObjectModel).filter(getattr(CjObjectModel, attrib) == value).limit(50)


        if not cj_object:
            return {"message": "The queried object does not exist"}, 404

        output = parse_json(cityjson_list_schema.dump(cj_object))

        # todo 1: add html as a format
        # todo 2: add query by point and query by ground_geometry

        return jsonify(output)    

#delet an object, and it's children from database
class DelObject(Resource):
    @classmethod
    def get(cls, object_id: str):
        in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        if not in_db:
            return {"message": "This object is not in the database " + object_id}, 404

        has_children = session.query(FamilyModel).join(CjObjectModel, CjObjectModel.object_id == FamilyModel.parent_id).filter(FamilyModel.parent_id == object_id).all()
        if has_children:
            delete_children(has_children)

        is_child = session.query(FamilyModel).join(CjObjectModel, CjObjectModel.object_id == FamilyModel.child_id).filter(FamilyModel.child_id == object_id).all()
        if is_child:
            for child in is_child:
                u = delete(FamilyModel)
                u = u.where(FamilyModel.child_id == child.child_id)
                engine.execute(u)

        u = delete(CjObjectModel)
        u = u.where(CjObjectModel.object_id == object_id)
        engine.execute(u)

        return ("Object " + object_id + "is deleted")


##Get all the information of an object, given a certain value: So for instance, select building with object_id NL.IMBAG.Pand.0518100000213709-0, or select building with id 2
class QueryByAttribute(Resource):
    @classmethod
    def get(cls, attrib: str, value: str):
        att = attrib.split('.')
        if len(att) > 1:
            cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[att[1]] == value).limit(50)
        else:
            cj_object = session.query(CjObjectModel).filter(getattr(CjObjectModel, attrib) == value).limit(50)

        if not cj_object:
            return {"message": "This object does not have " + attrib}, 404
        
        output = parse_json(cityjson_list_schema.dump(cj_object))

        return jsonify(output)

## Get the attribute info of an object, given the object_id, so for instance, get the geometry, id, or attributes of NL.IMBAG.Pand.0518100000213709-0
class GetInfo(Resource):
    @classmethod
    def get(cls, attrib: str, object_id: str):
        in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        if not in_db:
            return {"message": "This object is not in the database " + object_id}, 404

        att = attrib.split('.')
        cj_object = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        if len(att) > 1:
            attribute = cj_object.attributes[att[1]]
        else:
            attribute = getattr(cj_object, attrib)

        if not attribute:
            return {"message": "This object does not have " + attrib}, 404

        return attribute

#Get the children of an object, given an object_id
class GetChildren(Resource):
    @classmethod
    def get(cls, object_id: str):
        in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        if not in_db:
            return {"message": "This object is not in the database " + object_id}, 404

        cj_object = session.query(CjObjectModel).join(FamilyModel, FamilyModel.child_id == CjObjectModel.object_id).filter(FamilyModel.parent_id == object_id).all()
        if not cj_object:
            return {"message": "This object does not have children"}, 404
        
        output = parse_json(cityjson_list_schema.dump(cj_object))

        return jsonify(output)
    
#Get the parent of an object, given an object_id
class GetParent(Resource):
    @classmethod
    def get(cls, object_id: str):
        in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        if not in_db:
            return {"message": "This object is not in the database " + object_id}, 404

        cj_object = session.query(CjObjectModel).join(FamilyModel, FamilyModel.parent_id == CjObjectModel.object_id).filter(FamilyModel.child_id == object_id).all()
        if not cj_object:
            return {"message": "This object does not have children"}, 404

        output = parse_json(cityjson_list_schema.dump(cj_object))

        return jsonify(output)

#Filter objects based on attribute values
class FilterAttributes(Resource):
    @classmethod
    def get(cls, attrib: str, operator:str, value: str):
        if operator == "smaller":
            cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[attrib] < value).limit(50)
        if operator == "equals":
            cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[attrib] == value).limit(50)
        if operator == "bigger":
            cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[attrib] > value).limit(50)

        if not cj_object:
            return {"message": "Object not found"}, 404
        
        output = parse_json(cityjson_list_schema.dump(cj_object))

        return jsonify(output)


# Given point 2D coordinates, like (81402.6705,451405.4224), return the object_id
class QueryByPoint(Resource):
    @classmethod
    def get(cls, coor: str):
        sql = text('SELECT * FROM cjdb.cj_object WHERE ground_geometry && ST_MakePoint' + coor)

        results = engine.execute(sql)

        # View the records
        for record in results:
            building = record[2]

        # test URL: http://127.0.0.1:5000/api/point/(81402.6705,451405.4224)
        return building


# Given 2D bounding box, like (81400, 451400, 81600, 451600), return the table of object_id
class QueryByGroundGeometry(Resource):
    @classmethod
    def get(cls, coor: str):
        sql = text('SELECT * FROM cjdb.cj_object WHERE ground_geometry && ST_MakeEnvelope'+coor)
        results = engine.execute(sql)

        # View the records
        record_list = []
        for record in results:
            record_list.append(record[2])

        # test URL: http://127.0.0.1:5000/api/ground_geometry/(81400, 451400, 81600, 451600)
        return record_list

#Add an attribute to an or all objects
class AddAttribute(Resource):
    @classmethod
    def get(cls, object_id: str, attrib: str, new_value: str):
        if attrib in FIELD_MAPPING:
            return {"message": "This object already has " + attrib + " If you want to Update the attribute, use /update instead"}, 404

        if object_id == "all":
            obs = session.query(CjObjectModel)
            show = session.query(CjObjectModel).limit(50)
        else:
            in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
            if not in_db:
                return {"message": "This object is not in the database " + object_id}, 404
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes
            else:
                listObj = {}
            if attrib == "FootPrintArea":
                with engine.connect() as connection:
                    area_pointer = connection.execute(object.ground_geometry.ST_Area())

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
            return cityjson_list_schema.dump(show)
        else:
            return cityjson_list_schema.dump(obs)

#Delete an attribute of an or all objects
class DelAttrib(Resource):
    @classmethod
    def get(cls, object_id:str, attrib:str):

        if object_id == "all":
            obs = session.query(CjObjectModel).all()
        else:
            in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
            if not in_db:
                return {"message": "This object is not in the database " + object_id}, 404
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes
                del listObj[attrib]
                u = update(CjObjectModel)
                u = u.values({"attributes": listObj})
                u = u.where(CjObjectModel.object_id == object.object_id)
                engine.execute(u)

        if object_id == "all":
            show = session.query(CjObjectModel).limit(50)
            return cityjson_list_schema.dump(show)
        else:
            return cityjson_list_schema.dump(obs)

#Update an attribute of an or all objects
class UpdateAttrib(Resource):
    @classmethod
    def get(cls, object_id:str, attrib:str, new_value:str):
        if type(ast.literal_eval(new_value)) != tm[attrib]:
            print("type of type map = ", tm[attrib], "input type = ", type(ast.literal_eval(new_value)))
            return {"message": "Input type and mapped type don't match"}, 404

        if attrib not in FIELD_MAPPING and attrib != "FootPrintArea":
            return {"message": "This attribute does not exist, to create a new attribute, use /add instead"}, 404

        if object_id == "all":
            obs = session.query(CjObjectModel).all()
        else:
            in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
            if not in_db:
                return {"message": "This object is not in the database " + object_id}, 404
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes

                if attrib == "FootPrintArea":
                    with engine.connect() as connection:
                        area_pointer = connection.execute(object.ground_geometry.ST_Area())

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
            return cityjson_list_schema.dump(show)
        else:
            return cityjson_list_schema.dump(obs)

#Use CQL language to do queries.
class CQL_query(Resource):
    @classmethod
    def get(cls):
        cql_filter = request.args.get("cql_filter") or request.args.get("CQL_FILTER")
        filters = parse_ecql(cql_filter)

        # the external library converts the CQL_filter to an sqlalchemy_filter
        sqlalchemy_filters = to_filter(filters, FIELD_MAPPING)

        # apply the filter here:
        query = session.query(CjObjectModel).filter(sqlalchemy_filters)
        lim = query.limit(50)

        # return cityjson_list_schema.dump(cj_objects)
        return cityjson_list_schema.dump(lim)