import argparse
import os
from getpass import getpass


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
    parser.add_argument('-W', '--password', type=str, 
                        default=os.getenv("PGPASSWORD", None),
                        help='Target database schema', dest="db_password")
    parser.add_argument('-d', '--database', type=str, required=True,
                        help='PostgreSQL database name', dest="db_name")
    parser.add_argument('-s', '--schema', type=str, default='public',
                        help='Target database schema', dest="db_schema")
    parser.add_argument('-I', '--srid', type=int, default=None,
                    help='Target coordinate system', dest="target_srid")
    parser.add_argument('-A', '--append', default=False,
                action='store_const', const=True,
                help='Run in append mode (as opposed to default create mode). \
                This assumes the database structure exists already and new data is to be appended', 
                dest="append_mode")

    return parser


# todo validate args
# perform some other checks for validity
def validate_args(args):
    if not args.db_password:
        args.db_password = getpass(prompt=f'Password for user "{args.db_user}": ')
        
    return True, ""