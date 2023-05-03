import io

import pytest
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.orm import Session

from cjdb.modules.exceptions import (InvalidCityJSONObjectException,
                                     InvalidMetadataException,
                                     MissingCRSException)
from cjdb.modules.importer import Importer
from cjdb.modules.exporter import Exporter


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


def test_directory_import(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/cjfiles",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        update_existing=False,
    ) as importer:
        importer.run_import()


def test_single_import_with_extensions(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/extension.city.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        update_existing=False,
    ) as importer:
        importer.run_import()

    cj_metadata = Table(
        "cj_metadata", MetaData(),
        schema="cjdb",
        autoload_with=engine_postgresql
    )

    query_cj_metadata = (
        select(cj_metadata)
        .where(cj_metadata.c.extensions.isnot(None))
        .where(cj_metadata.c.source_file == "extension.city.jsonl")
    )

    with Session(engine_postgresql) as session:
        row = session.execute(query_cj_metadata).first()
        assert (
            row.extensions["Noise"]["url"]
            == "https://www.cityjson.org/tutorials/files/noise.ext.json"
        )
        assert row.extensions["Noise"]["version"] == "1.1.0"


def test_single_import_with_geometry_template(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/geomtemplate.city.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        update_existing=False,
    ) as importer:
        importer.run_import()

    cj_metadata = Table(
        "cj_metadata", MetaData(),
        schema="cjdb",
        autoload_with=engine_postgresql
    )

    query_cj_metadata = (
        select(cj_metadata)
        .where(cj_metadata.c.geometry_templates.isnot(None))
        .where(cj_metadata.c.source_file == "geomtemplate.city.jsonl")
    )

    with Session(engine_postgresql) as session:
        row = session.execute(query_cj_metadata).first()

        assert row.geometry_templates["templates"][0]["lod"] == "1"
        assert row.geometry_templates["templates"][0]["type"] == "MultiSurface"

        assert row.geometry_templates["vertices-templates"] == [
            [0, 0, 5],
            [10, 0, 5],
            [10, 10, 5],
            [0, 10, 5],
            [0, 0, 15],
            [10, 0, 15],
            [10, 10, 15],
            [0, 10, 15],
        ]


def test_single_import_without_metadata(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/no_metadata.city.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        update_existing=False,
    ) as importer:
        with pytest.raises(InvalidMetadataException):
            importer.run_import()


def test_single_import_without_cityjson_obj_in_first_line(
    engine_postgresql, monkeypatch
):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/no_cityjson_obj.city.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        update_existing=False,
    ) as importer:
        with pytest.raises(InvalidCityJSONObjectException):
            importer.run_import()
