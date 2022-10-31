import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
import os
from pathlib import Path
from cj2pgsql.resources import object_types


def get_db_engine(args, echo=False):
    conn_string = f"postgresql://{args.db_user}:{args.db_password}"\
        f"@{args.db_host}:{args.db_port}/{args.db_name}"

    engine = create_engine(conn_string, echo=echo)

    return engine


def open_connection(args):
    conn = psycopg2.connect(database=args.db_name,
                            host=args.db_host,
                            user=args.db_user,
                            port=args.db_port,
                            cursor_factory=RealDictCursor)
    
    return conn


# todo - this should take available object types from the official spec
def get_cj_object_types():
    types = object_types.types

    type_list = []
    for key, val in types.items():
        type_list.append(key)
        if val:
            for v in val:
                type_list.append(v)

    return sorted(type_list)


# find extended properties
def find_extra_properties(json_obj):
    property_names = []
    for key in json_obj:
        if key.startswith("+"):
            property_names.append(key)

    return property_names