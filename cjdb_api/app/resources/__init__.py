from cjdb_api.app.schemas import CjObjectSchema
from cjdb_api.app.db import session, engine
from model.sqlalchemy_models import CjObjectModel, FamilyModel, ImportMetaModel

import ast

# time stamp
import calendar
import time
from datetime import datetime


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
        tp = ast.literal_eval(new_value)
        FIELD_MAPPING[attrib] = type(tp)
        return tp


def in_database(object_id):
    in_db = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).all()
    if not in_db:
        return {"message": "This object is not in the database " + object_id}, 404


def parse_json(data, datatype='multiple'):
    # to be added: children, parents
    if datatype == 'single':
        type_name = 'Feature'
    elif datatype == 'multiple':
        type_name = 'Feature collection'
  
    current_GMT = time.gmtime()
    timestamp = calendar.timegm(current_GMT)
    date_time = datetime.fromtimestamp(timestamp)
    str_date_time = date_time.strftime("%d-%m-%Y, %H:%M:%S")
    
    output = {
        'type': type_name,
        'links': [],
        'numberReturned': len(data),
        'timeStamp': str_date_time,
        'feature': data,
    }
    return output
