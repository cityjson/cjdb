import argparse
import os
from getpass import getpass
from cj2pgsql.resources import strings as s

def Parser():
    parser = argparse.ArgumentParser(description='Import CityJSONL to a PostgreSQL database')

    parser.add_argument('filepath', nargs='?', default='stdin', 
                        type=str, metavar="file_or_directory",
                        help=s.filepath_help)
    parser.add_argument('-H', '--host', type=str, default='localhost',
                        help=s.host_help, dest="db_host")
    parser.add_argument('-p', '--port', type=int, default=5432,
                        help=s.port_help, dest="db_port")
    parser.add_argument('-U', '--user', type=str, required=True,
                        help=s.user_help, dest="db_user")
    parser.add_argument('-W', '--password', type=str, 
                        default=os.getenv("PGPASSWORD", None),
                        help=s.password_help, dest="db_password")
    parser.add_argument('-d', '--database', type=str, required=True,
                        help=s.database_help, dest="db_name")
    parser.add_argument('-s', '--schema', type=str, default='public',
                        help=s.schema_help, dest="db_schema")
    parser.add_argument('-I', '--srid', type=int, default=None,
                    help=s.srid_help, dest="target_srid")
    parser.add_argument('-x', '--attr-index', type=str,
                    action='append', default=[],
                    help=s.index_help, 
                    dest="indexed_attributes")

    parser.add_argument('-g', '--ignore-repeated-file', default=False,
            action='store_const', const=True,
            help=s.ignore_file_help,
            dest="ignore_repeated_file")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-a', '--append', default=False,
                action='store_const', const=True,
                help=s.append_help,
                dest="append_mode")
    mode.add_argument('-o', '--overwrite', default=False,
                action='store_const', const=True,
                help=s.overwrite_help, 
                dest="overwrite")

    existing_action = parser.add_mutually_exclusive_group()
    existing_action.add_argument('-e', '--skip-existing', default=False,
                action='store_const', const=True,
                help=s.skip_existing,
                dest="skip_existing")
    existing_action.add_argument('-u', '--update-existing', default=False,
            action='store_const', const=True,
            help=s.update_existing,
            dest="update_existing")

    return parser


# perform some other checks for validity
def validate_args(args):
    result = True
    msg = ""
    if not args.db_password:
        args.db_password = getpass(prompt=f'Password for user "{args.db_user}": ')
        
    return result, msg