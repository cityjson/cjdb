import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
import os


def get_db_engine(args):
    conn_string = f"postgresql://{args.db_user}:{args.db_password}"\
        f"@{args.db_host}:{args.db_port}/{args.db_name}"

    engine = create_engine(conn_string)

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
