from flask import render_template, make_response, request
from flask_restful import Resource
from model.sqlalchemy_models import CjObjectModel
from cjdb_api.app.schemas import CjObjectSchema
from cjdb_api.app.db import session, engine
from sqlalchemy.sql import text
from pygeofilter.parsers.ecql import parse as parse_ecql
from pygeofilter.backends.sqlalchemy import to_filter
from sqlalchemy import update

cityjson_schema = CjObjectSchema()
cityjson_list_schema = CjObjectSchema(many=True)

# global tm
global FIELD_MAPPING
FIELD_MAPPING = {
    "object_id": CjObjectModel.object_id,
    "type": CjObjectModel.type,
    "bbox": CjObjectModel.bbox,
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
        if isinstance(new_value, bool):
            FIELD_MAPPING[attrib] = CjObjectModel.attributes[attrib].as_boolean()
            return bool(new_value)
        if isinstance(new_value, float):
            FIELD_MAPPING[attrib] = CjObjectModel.attributes[attrib].as_float()
            return float(new_value)
        if isinstance(new_value, int):
            FIELD_MAPPING[attrib] = CjObjectModel.attributes[attrib].as_integer()
            return int(new_value)
        else:
            FIELD_MAPPING[attrib] = CjObjectModel.attributes[attrib].as_string()
            return new_value

def parse_table(parse):
    # convert cityjson schema to a list of headers and a list of lists of values
    headings = list(parse[0].keys())
    data = []
    for item in parse:
        data.append(list(item.values()))

    return headings, data

##working

#Select all objects in the database
class show(Resource):
    @classmethod
    def get(cls, lim: int):
        all = session.query(CjObjectModel).limit(lim).all()

        if not all:
            return {"message": "Object not found"}, 404

        headings, data = parse_table(cityjson_list_schema.dump(all))

        return make_response(render_template("all.html", headings=headings, data=data))

##Get all the information of an object, given a certain value: So for instance, select building with object_id NL.IMBAG.Pand.0518100000213709-0, or select building with id 2
class QueryByAttribute(Resource):
    @classmethod
    def get(cls, attrib: str, value: str):
        cj_object = session.query(CjObjectModel).filter(getattr(CjObjectModel, attrib) == str(value)).limit(50)

        if not cj_object:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(cj_object)

## Get the attribute info of an object, given the object_id, so for instance, get the children, parents, or attributes of NL.IMBAG.Pand.0518100000213709-0
class GetInfo(Resource):
    @classmethod
    def get(cls, attrib: str, object_id: str):
        cj_object = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        attribute = getattr(cj_object, attrib)

        if not attribute:
            return {"message": "Object not found"}, 404

        return attribute

class FilterAttributes(Resource):
    @classmethod
    def get(cls, attrib: str, operator:str, value: str):

        val = what_type(attrib, value)
        if operator == "smaller":
            cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[attrib] < val).limit(50)
        if operator == "equals":
            cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[attrib] == val).limit(50)
        if operator == "bigger":
            cj_object = session.query(CjObjectModel).filter(CjObjectModel.attributes[attrib] > val).limit(50)

        if not cj_object:
            return {"message": "Object not found"}, 404

        for object in cj_object:
            print(object.id)

        return cityjson_list_schema.dump(cj_object)


# Given point 2D coordinates, like (81402.6705,451405.4224), return the object_id
class QueryByPoint(Resource):
    @classmethod
    def get(cls, coor: str):
        sql = text('SELECT * FROM cjdb.cj_object WHERE bbox && ST_MakePoint'+coor)
        results = engine.execute(sql)

        # View the records
        for record in results:
            building = record[2]

        # test URL: http://127.0.0.1:5000/api/point/(81402.6705,451405.4224)
        return building

# Given 2D bounding box, like (81400, 451400, 81600, 451600), return the table of object_id
class QueryByBbox(Resource):
    @classmethod
    def get(cls, coor: str):
        sql = text('SELECT * FROM cjdb.cj_object WHERE bbox && ST_MakeEnvelope'+coor)
        results = engine.execute(sql)

        # View the records
        record_list = []
        for record in results:
            record_list.append(record[2])

        # test URL: http://127.0.0.1:5000/api/bbox/(81400, 451400, 81600, 451600)
        return record_list

# Given an object_id, return the value of the footprint area
class CalculateFootprint(Resource):
    @classmethod
    def get(cls, object_id: str):
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

## in progress
class AddAttribute(Resource):
    @classmethod
    def get(cls, object_id: str, attrib: str, new_value: str):

        if object_id == "all":
            obs = session.query(CjObjectModel)

        else:
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            print("I am going through it")
            if isinstance(object.attributes, dict):
                listObj = object.attributes
                if attrib == "bbox":
                    with engine.connect() as connection:
                        area_pointer = connection.execute(object.bbox.ST_Area())

                    for row in area_pointer:
                        value = row[0]
                else:
                    value = what_type(attrib, new_value)
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

class DelAttrib(Resource):
    @classmethod
    def get(cls, object_id:str, attrib:str):

        if object_id == "all":
            obs = session.query(CjObjectModel).all()
        else:
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes
                del listObj[attrib]
                u = update(object)
                u = u.values({"attributes": listObj})
                u = u.where(CjObjectModel.object_id == object.object_id)
                engine.execute(u)

        if object_id == "all":
            show = session.query(CjObjectModel).limit(50)
            return cityjson_list_schema.dump(show)
        else:
            return cityjson_list_schema.dump(obs)

class UpdateAttrib(Resource):
    @classmethod
    def get(cls, object_id:str, attrib:str, new_value:str):
        value = what_type(attrib, new_value)

        if object_id == "all":
            obs = session.query(CjObjectModel).all()
        else:
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes
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


class CalculateVolume (Resource):
    pass

class Geometry(Resource):
    @classmethod
    def get(cls):
        all = session.query(CjObjectModel).all()

        if not all:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(all)

class CQL_query(Resource):
    @classmethod
    def get(cls):
        cql_filter = request.args.get("cql_filter") or request.args.get("CQL_FILTER")
        filters = parse_ecql(cql_filter)

        # the external library converts the CQL_filter to an sqlalchemy_filter
        sqlalchemy_filters = to_filter(filters, FIELD_MAPPING)

        # apply the filter here:
        query = session.query(CjObjectModel).filter(sqlalchemy_filters)
        # lim = query.limit(50)

        # return cityjson_list_schema.dump(cj_objects)
        return cityjson_list_schema.dump(query)
