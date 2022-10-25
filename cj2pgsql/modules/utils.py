import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
import os
import yaml
from pathlib import Path


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
                            cursor_factory=RealDictCursor
                            )
    
    return conn


def execute_sql(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)

    conn.commit()

def fetch_query(conn, query):
    result = None
    with conn.cursor() as cur:
        cur.execute(query)
        if cur.rowcount > 0:
            result = cur.fetchall()

    conn.commit()
    return result

# todo - this should take available object types from the official spec
def get_cj_object_types():
    cur_path = Path(__file__).parent
    obj_type_path = os.path.join(cur_path.parent, "resources/object_types.yml")

    with open(obj_type_path, "r") as f:
        try:
            types = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
            raise

    type_list = []
    for key, val in types.items():
        type_list.append(key)
        if val:
            for v in val:
                type_list.append(v)

    return sorted(type_list)


def find_extra_properties(json_obj):
    property_names = []
    for key in json_obj:
        if key.startswith("+"):
            property_names.append(key)

    return property_names