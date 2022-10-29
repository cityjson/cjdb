import argparse
import os
from getpass import getpass
from cj2pgsql.resources.strings import *

def Parser():
    parser = argparse.ArgumentParser(description='Import CityJSONL to a PostgreSQL database')

    parser.add_argument('filepath', nargs='?', default='stdin', 
                        type=str, metavar="file_or_directory",
                        help=filepath_help)
    parser.add_argument('-H', '--host', type=str, default='localhost',
                        help=host_help, dest="db_host")
    parser.add_argument('-p', '--port', type=int, default=5432,
                        help=port_help, dest="db_port")
    parser.add_argument('-U', '--user', type=str, required=True,
                        help=user_help, dest="db_user")
    parser.add_argument('-W', '--password', type=str, 
                        default=os.getenv("PGPASSWORD", None),
                        help=password_help, dest="db_password")
    parser.add_argument('-d', '--database', type=str, required=True,
                        help=database_help, dest="db_name")
    parser.add_argument('-s', '--schema', type=str, default='public',
                        help=schema_help, dest="db_schema")
    parser.add_argument('-I', '--srid', type=int, default=None,
                    help=srid_help, dest="target_srid")
    parser.add_argument('-x', '--attr-index', type=str,
                    action='append', default=[],
                    help=index_help, 
                    dest="indexed_attributes")
    parser.add_argument('-a', '--append', default=False,
                action='store_const', const=True,
                help=append_help,
                dest="append_mode")
    parser.add_argument('-o', '--overwrite', default=False,
                action='store_const', const=True,
                help=overwrite_help, 
                dest="overwrite")
    parser.add_argument('-g', '--ignore-repeated-file', default=False,
                action='store_const', const=True,
                help=ignore_file_help,
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