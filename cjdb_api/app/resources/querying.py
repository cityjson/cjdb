from flask import render_template, make_response, request, jsonify
from flask_restful import Resource
from sqlalchemy import update, delete
from sqlalchemy.sql import text
import ast

from model.sqlalchemy_models import CjObjectModel, FamilyModel, ImportMetaModel
from cjdb_api.app.db import session, engine
from cjdb_api.app.resources import cityjson_schema, cityjson_list_schema, FIELD_MAPPING, in_database, parse_json

from pygeofilter.parsers.ecql import parse as parse_ecql
from pygeofilter.backends.sqlalchemy import to_filter


def parse_html(parse):
    # convert cityjson schema to a list of headers and a list of lists of values
    headings = list(parse[0].keys())
    data = []
    for item in parse:
        data.append(list(item.values()))

    return headings, data


#Select all objects in the database
class Show(Resource):
    @classmethod
    def get(cls):
        lim = request.args.get('limit', 50)
        all = session.query(CjObjectModel).limit(lim).all()

        if not all:
            return {"message": "Object not found"}, 404

        headings, data = parse_html(cityjson_list_schema.dump(all))

        return make_response(render_template("all.html", headings=headings, data=data))

    
# Item load query parameters, not path parameters    
class Item(Resource):
    @classmethod
    def get(cls):
        # optional parameters: id, import_meta_id, object_id, type, attribute.xx, bbox
        args = request.args.to_dict()

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
        # geometries: point, bbox

        key_list = list(args.keys())
        if key_list == {}:
            cj_object = session.query(CjObjectModel).limit(50).all()

        else:
            attrib = str(key_list[0])
            value = str(args[attrib])
            print(key_list)

            att = attrib.split('.')
            if len(att) > 1:
                cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[att[1]] == value).limit(50)
            elif attrib == 'parent_id':  # get children, value = object_id
                cj_object = session.query(CjObjectModel).join(FamilyModel,FamilyModel.child_id == CjObjectModel.object_id).filter(FamilyModel.parent_id == value).all()
            elif attrib == 'child_id':  # get parents, value = object_id
                cj_object = session.query(CjObjectModel).join(FamilyModel,FamilyModel.parent_id == CjObjectModel.object_id).filter(FamilyModel.child_id == value).all()
            elif attrib == 'bbox':
                sql = text('SELECT * FROM cjdb.cj_object WHERE bbox && ST_MakeEnvelope' + value)
                results = engine.execute(sql)
                cj_object = []
                for record in results:
                    one_record = {'object_id': record[2], 'type': record[3], 'attributes': record[4],
                                  'geometry': record[5]}
                    cj_object.append(one_record)
            elif attrib == 'point':
                sql = text('SELECT * FROM cjdb.cj_object WHERE bbox && ST_MakePoint' + value)
                results = engine.execute(sql)
                cj_object = []
                for record in results:
                    one_record = {'object_id': record[2], 'type': record[3], 'attributes': record[4],
                                  'geometry': record[5]}
                    cj_object.append(one_record)
            elif attrib == 'id' or 'object_id' or 'import_meta_id' or 'type':
                cj_object = session.query(CjObjectModel).filter(getattr(CjObjectModel, attrib) == value).limit(50)

        if not cj_object:
            return {"message": "The queried object does not exist"}, 404

        output = parse_json(cityjson_list_schema.dump(cj_object))
        return jsonify(output)

    
# Given an object_id, return the value of the footprint area
class CalculateFootprint(Resource):
    @classmethod
    def get(cls):
        # required parameter: object_id
        object_id = request.args.get('object_id', None)
        
        if object_id is None:
            return {"message": "Invalid parameter. Please include the right object_id."}, 404
        else:
            in_database(object_id)

        cj_object = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        if not cj_object:
            return {"message": "Object not found"}, 404

        with engine.connect() as connection:
            area_pointer = connection.execute(cj_object.bbox.ST_Area())

        for row in area_pointer:
            area = row[0]

        if not area:
            return {"message": "Object not found"}, 404

        return area


class CQL_query(Resource):
    @classmethod
    def get(cls):
        cql_filter = request.args.get("filter") or request.args.get("FILTER")
        filters = parse_ecql(cql_filter)

        # the external library converts the CQL_filter to an sqlalchemy_filter
        sqlalchemy_filters = to_filter(filters, FIELD_MAPPING)

        # apply the filter here:
        query = session.query(CjObjectModel).filter(sqlalchemy_filters)
        lim = query.limit(50)

        output = parse_json(cityjson_list_schema.dump(lim))

        # return cityjson_list_schema.dump(cj_objects)
        return output

    
## Old methods    
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
        sql = text('SELECT * FROM cjdb.cj_object WHERE bbox && ST_MakePoint' + coor)
        results = engine.execute(sql)

        cj_object = []
        for record in results:
            one_record = {'object_id': record[2],'type': record[3], 'attributes': record[4], 'geometry': record[5]}
            cj_object.append(one_record)

        output = parse_json(cityjson_list_schema.dump(cj_object))
        return output


# Given 2D bounding box, like (81400, 451400, 81600, 451600), return the table of object_id
class QueryByBbox(Resource):
    @classmethod
    def get(cls, coor: str):
        sql = text('SELECT * FROM cjdb.cj_object WHERE bbox && ST_MakeEnvelope'+coor)
        results = engine.execute(sql)

        cj_object = []
        for record in results:
            one_record = {'object_id': record[2],'type': record[3], 'attributes': record[4], 'geometry': record[5]}
            cj_object.append(one_record)

        output = parse_json(cityjson_list_schema.dump(cj_object))
        return output
