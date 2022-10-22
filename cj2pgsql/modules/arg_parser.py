import argparse
import os
from getpass import getpass


def Parser():
    parser = argparse.ArgumentParser(description='Import CityJSONL to a PostgreSQL database')

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
                    help='Target coordinate system SRID', dest="target_srid")
    parser.add_argument('-x', '--attr-index', type=str,
                    action='append', default=[],
                    help='CityObject attribute to be indexed. Can be specified multiple times, for each attribute once', 
                    dest="indexed_attributes")
    parser.add_argument('-a', '--append', default=False,
                action='store_const', const=True,
                help='Run in append mode (as opposed to default create mode). \
                This assumes the database structure exists already and new data is to be appended', 
                dest="append_mode")
    parser.add_argument('-o', '--overwrite', default=False,
                action='store_const', const=True,
                help='Overwrite the data that is currently in the schema. \
                    Warning: this causes the loss of what was imported before to the database schema.', 
                dest="overwrite")
    parser.add_argument('-g', '--ignore-repeated-file', default=False,
                action='store_const', const=True,
                help='Ignore repeated file names warning when importing.',
                dest="ignore_repeated_file")


    return parser


# todo validate args
# perform some other checks for validity
def validate_args(args):
    result = True
    msg = ""
    if not args.db_password:
        args.db_password = getpass(prompt=f'Password for user "{args.db_user}": ')

    if args.overwrite and args.append_mode:
        result = False
        msg += "Cannot use --overwrite/-o and --append/-a flags simultaneously.\n"
        
    return result, msg