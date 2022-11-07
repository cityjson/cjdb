import argparse
import os

def Parser():
    parser = argparse.ArgumentParser(description='Run cjdb_api')

    required = parser.add_argument_group(title="Required arguments")
    required.add_argument('-C', '--conn-string', type=str, required=True,
                default=os.getenv("CJDB_CONN_STRING"),
                help="Database connection string in the form of: " + \
                "postgresql://<user>:<password>@<host>:<port>/<database>", 
                dest="conn_string")

    optional = parser.add_argument_group(title="Optional arguments")
    optional.add_argument('-p', '--port', type=int, default=8080,
                        help="Web application port", dest="port")

    optional.add_argument('-s', '--schema', type=str, default='public',
                        help="Database schema, where the CityObjects are kept.", 
                        dest="db_schema")

    optional.add_argument('-d', '--debug', default=False,
                action='store_const', const=True,
                help="Run in debug mode.",
                dest="debug_mode")

    return parser
