import argparse

def Parser():
    parser = argparse.ArgumentParser(description='Import CityJSON to a PostgreSQL database')

    parser.add_argument('filepath', nargs='?', default='stdin', 
                        type=str, metavar="file_or_directory",
                        help='Source CityJSONL file or a directory with CityJSONL files. STDIN if not specified.')
    parser.add_argument('-H', '--host', type=str, default='localhost',
                        help='PostgreSQL database host', dest="db_host")
    parser.add_argument('-p', '--port', type=int, default=5432,
                        help='PostgreSQL database port', dest="db_port")
    parser.add_argument('-U', '--user', type=str, required=True,
                        help='PostgreSQL database user name', dest="db_user")
    parser.add_argument('-d', '--database', type=str, required=True,
                        help='PostgreSQL database name', dest="db_name")
    parser.add_argument('-s', '--schema', type=str, default='public',
                        help='Target database schema', dest="db_schema")

    return parser

# todo validate args
def validate_args(args):
    return True, ""