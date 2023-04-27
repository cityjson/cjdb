import click
from cjdb.logger import logger

from cjdb import __version__
from cjdb.modules.importer import Importer
from cjdb.modules.exporter import Exporter
from cjdb.modules.utils import get_db_engine, get_db_psycopg_conn
from cjdb.resources import strings as s


@click.group()
@click.version_option(
    __version__,
    "-v",
    "--version",
    prog_name="cjdb",
    message="cjdb " + __version__,
    help=s.version_help,
)
@click.pass_context
def cjdb(ctx):
    logger.info("CJDB Importer/Exporter!")


@cjdb.command(name="import")
@click.argument("filepath", type=str, default="stdin")
@click.option("--host", "-H", type=str, default="localhost", help=s.host_help)
@click.option("--port", "-p", type=int, default=5432, help=s.port_help)
@click.option("--user", "-U", type=str, required=True, help=s.user_help)
@click.password_option(
    help=s.password_help,
    prompt="Password for database user",
    confirmation_prompt=False
)
@click.option("--database", "-d",
              type=str,
              required=True,
              help=s.database_help)
@click.option("--schema", "-s", type=str, default="cjdb", help=s.schema_help)
@click.option("--append", "-a", type=bool, default=False, help=s.append_help)
@click.option("--srid", "-I", "target_srid",
              type=int,
              default=None,
              help=s.srid_help)
@click.option(
    "--attr-index", "-x",
    "indexed_attributes",
    type=str,
    multiple=True,
    help=s.index_help
)
@click.option(
    "--partial-attr-index",
    "-px",
    "partial_indexed_attributes",
    type=str,
    multiple=True,
    help=s.partial_index_help,
)
@click.option(
    "--ignore-repeated-file",
    "-g",
    "ignore_repeated_file",
    type=bool,
    is_flag=True,
    default=False,
    help=s.ignore_file_help,
)
@click.option(
    "--update-existing",
    "update_existing",
    is_flag=True,
    default=False,
    help=s.update_existing,
)
def import_cj(
    filepath,
    host,
    port,
    user,
    password,
    database,
    schema,
    append,
    target_srid,
    indexed_attributes,
    partial_indexed_attributes,
    ignore_repeated_file,
    update_existing,
):
    """Import CityJSONL files to a PostgreSQL database."""
    engine = get_db_engine(user, password, host, port, database)
    with Importer(
        engine,
        filepath,
        append,
        schema,
        target_srid,
        indexed_attributes,
        partial_indexed_attributes,
        ignore_repeated_file,
        update_existing,
    ) as imp:
        imp.run_import()


@cjdb.command(name="export")
@click.argument("query", type=str)
@click.option("--host", "-H", type=str, default="localhost", help=s.host_help)
@click.option("--port", "-p", type=int, default=5432, help=s.port_help)
@click.option("--user", "-U", type=str, default="postgres", help=s.user_help)
@click.password_option(
    help=s.password_help,
    prompt="Password for database user",
    confirmation_prompt=False
)
@click.option("--database", "-d",
              type=str,
              required=True,
              help=s.database_help)
@click.option("--schema", "-s", type=str, default="cjdb", help=s.schema_help)
def export_cj(query, host, port, user, password, database, schema):
    """Export a CityJSONL stream to stdout."""
    conn = get_db_psycopg_conn(user, password, host, port, database)
    with Exporter(
        conn,
        schema,
        query,
    ) as exp:
        exp.run_export()


if __name__ == "__main__":
    cjdb()
