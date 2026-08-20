from typing import Any

import psycopg2
from sqlalchemy import create_engine

from cjdb.resources import object_types

# PostgreSQL jsonb columns have a hard size limit of ~256 MB (268435455
# bytes). CJDB stores the fully-resolved geometry as jsonb, so a very detailed
# geometry (many vertices resolved to inline coordinates) can exceed it.
MAX_GEOMETRY_JSON_SIZE = 268_435_455


def _estimate_jsonb_size(value: Any) -> int:
    """Estimate the size of ``value`` once stored as PostgreSQL jsonb.

    jsonb stores numbers as binary ``Numeric`` and prefixes every array/object
    element with a 4/8-byte ``JEntry``, so it is typically larger than the JSON
    text produced by ``json.dumps``. This is only an estimate, used to fail
    early with a clear message instead of hitting PostgreSQL's cryptic error.
    """
    if isinstance(value, bool):
        return 8
    if value is None:
        return 4
    if isinstance(value, str):
        return 4 + len(value.encode("utf-8")) + 1
    if isinstance(value, (int, float)):
        return 4 + 24
    if isinstance(value, dict):
        size = 8
        for key, val in value.items():
            size += _estimate_jsonb_size(key) + _estimate_jsonb_size(val)
        return size
    if isinstance(value, (list, tuple)):
        size = 8
        for item in value:
            size += _estimate_jsonb_size(item)
        return size
    return 32


def geometry_jsonb_size(geometry: Any) -> int:
    """Return the estimated jsonb size in bytes for a geometry value."""
    return _estimate_jsonb_size(geometry)


def geometry_too_large(geometry: Any) -> bool:
    """Return True when the geometry would exceed the jsonb size limit."""
    return geometry_jsonb_size(geometry) > MAX_GEOMETRY_JSON_SIZE


def is_valid_file(filepath: str) -> bool:
    # TODO: this check sounds pretty easy to fulfil
    return bool(filepath.endswith(".jsonl"))


def get_db_engine(db_user, db_password, db_host, db_port, db_name, echo=False):
    conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(conn_string, echo=echo)
    return engine


def get_db_psycopg_conn(db_user, db_password, db_host, db_port, db_name):
    # conn = psycopg2.connect("dbname=cj_denhaag user=hugo")
    conn = psycopg2.connect(
        user=db_user, password=db_password, host=db_host, port=db_port, dbname=db_name
    )
    return conn


# TODO: this should take available object types from the official spec
def get_city_object_types():
    types = object_types.types

    type_list = []
    for key, val in types.items():
        type_list.append(key)
        if val:
            type_list.extend(val)

    return sorted(type_list)


def is_cityjson_object(json: dict[str, Any]) -> bool:
    """Check if the json is a cityjson object"""
    return bool(
        "version" in json
        and "transform" in json
        and "type" in json
        and json["type"] == "CityJSON"
    )


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
