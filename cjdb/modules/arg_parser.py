import argparse
import os
from getpass import getpass

from cjdb import __version__
from cjdb.resources import strings as s


def Parser():
    parser = argparse.ArgumentParser(
        description="Import CityJSONL to a PostgreSQL database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "filepath",
        nargs="?",
        default="stdin",
        type=str,
        metavar="file_or_directory",
        help=s.filepath_help,
    )

    parser.add_argument(
        "--version",
        action="version",
        version='%(prog)s ' + __version__,
        help=s.version_help,
    )

    db = parser.add_argument_group(title="Database connection arguments")

    db.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost",
        help=s.host_help,
        dest="db_host"
    )

    db.add_argument(
        "-p",
        "--port",
        type=int,
        default=5432,
        help=s.port_help,
        dest="db_port"
    )

    db.add_argument(
        "-U",
        "--user",
        type=str,
        required=True,
        help=s.user_help,
        dest="db_user"
    )

    db.add_argument(
        "-W",
        "--password",
        type=str,
        default=os.getenv("PGPASSWORD", None),
        help=s.password_help,
        dest="db_password",
    )

    db.add_argument(
        "-d",
        "--database",
        type=str,
        required=True,
        help=s.database_help,
        dest="db_name",
    )

    db.add_argument(
        "-s",
        "--schema",
        type=str,
        default="cjdb",
        help=s.schema_help,
        dest="db_schema",
    )

    parser.add_argument(
        "-I",
        "--srid",
        type=int,
        default=None,
        help=s.srid_help,
        dest="target_srid"
    )

    parser.add_argument(
        "-x",
        "--attr-index",
        type=str,
        action="append",
        default=[],
        help=s.index_help,
        dest="indexed_attributes",
    )

    parser.add_argument(
        "-px",
        "--partial-attr-index",
        type=str,
        action="append",
        default=[],
        help=s.partial_index_help,
        dest="partial_indexed_attributes",
    )

    parser.add_argument(
        "-g",
        "--ignore-repeated-file",
        default=False,
        action="store_const",
        const=True,
        help=s.ignore_file_help,
        dest="ignore_repeated_file",
    )

    mode = parser.add_mutually_exclusive_group()

    mode.add_argument(
        "-a",
        "--append",
        default=False,
        action="store_const",
        const=True,
        help=s.append_help,
        dest="append_mode",
    )

    mode.add_argument(
        "-o",
        "--overwrite",
        default=False,
        action="store_const",
        const=True,
        help=s.overwrite_help,
        dest="overwrite",
    )

    parser.add_argument(
        "-u",
        "--update-existing",
        default=False,
        action="store_const",
        const=True,
        help=s.update_existing,
        dest="update_existing",
    )

    return parser


# perform some other checks for validity
def validate_args(args):
    result = True
    msg = ""
    if not args.db_password:
        args.db_password = getpass(
            prompt=f'Password for user "{args.db_user}": '
        )  # noqa

    return result, msg
