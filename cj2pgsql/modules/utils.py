import psycopg2
from psycopg2.extras import RealDictCursor

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
