import io
from argparse import Namespace

import pytest
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.orm import Session

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


def test_single_import(engine_postgresql):
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


def test_repeated_file_with_ignore_repeated_file(engine_postgresql):
    args = Namespace(
        filepath="./tests/files/vienna.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=True,
        append_mode=False,
        overwrite=False,
        update_existing=False,
    )
    with Importer(engine=engine_postgresql, args=args) as imp:
        imp.run_import()


def test_repeated_file_with_update_existing(engine_postgresql):
    args = Namespace(
        filepath="./tests/files/vienna.jsonl",
        db_schema="cjdb",
        target_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        append_mode=False,
        overwrite=False,
        update_existing=True,
    )
    with Importer(engine=engine_postgresql, args=args) as imp:
        imp.run_import()


def test_repeated_file_with_prompt_to_skip(engine_postgresql, monkeypatch):
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


def test_repeated_file_with_prompt_to_exit(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("n"))
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
    with pytest.raises(SystemExit):
        with Importer(engine=engine_postgresql, args=args) as imp:
            imp.run_import()


def test_directory_import(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/cjfiles",
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


def test_db_model(engine_postgresql):
    insp = inspect(engine_postgresql)
    assert insp.has_schema("cjdb")
    assert insp.has_table("city_object", schema="cjdb")
    assert insp.has_table("cj_metadata", schema="cjdb")
    assert insp.has_table("city_object_relationship", schema="cjdb")

    city_object = Table(
        "city_object",
        MetaData(),
        schema="cjdb",
        autoload_with=engine_postgresql
    )

    cj_metadata = Table(
        "cj_metadata",
        MetaData(),
        schema="cjdb",
        autoload_with=engine_postgresql
    )

    query_city_object = select(city_object).where(
        city_object.c.object_id == "UUID_LOD2_011491-3cd51f89-4727-44e6-b12e_6"
    )
    query_cj_metadata = select(cj_metadata).where(
        cj_metadata.c.source_file == "vienna.jsonl")

    with Session(engine_postgresql) as session:
        row = session.execute(query_city_object).first()
        assert row.object_id == "UUID_LOD2_011491-3cd51f89-4727-44e6-b12e_6"
        assert row.attributes["roofType"] == "FLACHDACH"
        assert row.type == "BuildingPart"

        row = session.execute(query_cj_metadata).first()
        assert row.source_file == "vienna.jsonl"
        assert row.version == "1.1"
        assert row.transform["scale"] == [0.001, 0.001, 0.001]
        assert row.transform["translate"] == [983.16, 340433.878, 27.861]
        assert row.metadata["geographicalExtent"] == [
            983.16,
            340433.878,
            27.861,
            1510.432,
            341048.5,
            84.987,
        ]


def test_single_import_with_extensions(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    args = Namespace(
        filepath="./tests/files/extension.city.jsonl",
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
    args = Namespace(
        filepath="./tests/files/geomtemplate.city.jsonl",
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
    with pytest.raises(InvalidMetadataException):
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
    with pytest.raises(InvalidMetadataException):
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
    with pytest.raises(InvalidCityJSONObjectException):
        with Importer(engine=engine_postgresql, args=args) as imp:
            imp.run_import()
