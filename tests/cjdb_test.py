import io
from argparse import Namespace

import pytest
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import create_engine

from cjdb.modules.exceptions import (InvalidCityJSONObjectException,
                                     InvalidMetadataException)
from cjdb.modules.importer import Importer


@pytest.fixture(scope="session")
def engine_postgresql(postgresql_proc):
    with DatabaseJanitor(
        postgresql_proc.user,
        postgresql_proc.host,
        postgresql_proc.port,
        postgresql_proc.dbname,
        postgresql_proc.version,
        password=postgresql_proc.password,
    ):
        yield create_engine(
            f"postgresql+psycopg2://{postgresql_proc.user}:"
            f"{postgresql_proc.password}@{postgresql_proc.host}:"
            f"{postgresql_proc.port}/{postgresql_proc.dbname}"
        )


def test_single_import(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/vienna.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        overwrite=False,
        update_existing=False,
    )
    with Importer(engine=engine_postgresql, args=args) as imp:
        imp.run_import()


def test_single_import_with_extentions(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/extension2.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        overwrite=False,
        update_existing=False,
    )
    with Importer(engine=engine_postgresql, args=args) as imp:
        imp.run_import()


def test_single_import_without_srid(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/vienna.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        overwrite=False,
        update_existing=False,
    )
    with pytest.raises(InvalidMetadataException) as excinfo:
        with Importer(engine=engine_postgresql, args=args) as imp:
            imp.run_import()


def test_single_import_with_target_srid(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/vienna.jsonl",
        db_schema="cjdb",
        target_srid="7415",
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        overwrite=False,
        update_existing=False,
    )
    with Importer(engine=engine_postgresql, args=args) as imp:
        imp.run_import()


def test_single_import_without_metadata(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/no_metadata.city.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        overwrite=False,
        update_existing=False,
    )
    with pytest.raises(InvalidMetadataException) as excinfo:
        with Importer(engine=engine_postgresql, args=args) as imp:
            imp.run_import()


def test_single_import_without_cityjson_obj_in_first_line(
    engine_postgresql, monkeypatch
):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/no_cityjson_obj.city.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        overwrite=False,
        update_existing=False,
    )
    with pytest.raises(InvalidCityJSONObjectException) as excinfo:
        with Importer(engine=engine_postgresql, args=args) as imp:
            imp.run_import()
