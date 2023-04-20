import io
from argparse import Namespace

import pytest
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import MetaData, Table, create_engine, select, inspect
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

    insp = inspect(engine_postgresql)
    assert insp.has_schema("cjdb")
    assert insp.has_table("cj_object", schema="cjdb")
    assert insp.has_table("import_meta", schema="cjdb")
    assert insp.has_table("family", schema="cjdb")

    cj_object = Table(
        "cj_object", MetaData(), schema="cjdb", autoload_with=engine_postgresql
    )

    import_meta = Table(
        "import_meta", MetaData(), schema="cjdb", autoload_with=engine_postgresql
    )

    query_cj_object = select(cj_object).where(
        cj_object.c.object_id == "UUID_LOD2_011491-3cd51f89-4727-44e6-b12e_6"
    )
    query_import_meta = select(import_meta)

    print(query_import_meta)

    with Session(engine_postgresql) as session:
        row = session.execute(query_cj_object).first()
        assert row.object_id == "UUID_LOD2_011491-3cd51f89-4727-44e6-b12e_6"
        assert row.attributes["roofType"] == "FLACHDACH"
        assert row.type == "BuildingPart"

        row = session.execute(query_import_meta).first()
        print(row)
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
