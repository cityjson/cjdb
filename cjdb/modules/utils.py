from typing import Any, Dict

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine

from cjdb.resources import object_types


def is_valid_file(filepath: str) -> bool:
    if filepath.endswith('.jsonl'):
        return True
    return False


def get_db_engine(db_user, db_password, db_host, db_port, db_name, echo=False):
    conn_string = (
        f"postgresql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    engine = create_engine(conn_string, echo=echo)

    return engine


def open_connection(db_user, db_host, db_port, db_name):
    conn = psycopg2.connect(
        database=db_name,
        host=db_host,
        user=db_user,
        port=db_port,
        cursor_factory=RealDictCursor,
    )

    return conn


# todo - this should take available object types from the official spec
def get_city_object_types():
    types = object_types.types

    type_list = []
    for key, val in types.items():
        type_list.append(key)
        if val:
            for v in val:
                type_list.append(v)

    return sorted(type_list)


def is_cityjson_object(json: Dict[str, Any]) -> bool:
    """Check if the json is a cityjson object"""
    if (
        "version" in json
        and "transform" in json
        and "type" in json
        and json["type"] == "CityJSON"
    ):
        return True
    return False


# find extended properties
def find_extra_properties(json_obj):
    property_names = []
    for key in json_obj:
        if key.startswith("+"):
            property_names.append(key)

    return property_names


# Sqlalchemy model as dict
def to_dict(model):
    d = dict(model.__dict__)
    d.pop("_sa_instance_state", None)
    return d
