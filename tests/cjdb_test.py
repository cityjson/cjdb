import io

import pytest
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.orm import Session

from cjdb.modules.exceptions import (InconsistentCRSException,
                                     InvalidCityJSONObjectException,
                                     InvalidMetadataException,
                                     MissingCRSException,
                                     NoSchemaSridException)
from cjdb.modules.exporter import Exporter
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


def test_single_import_missing_srid(engine_postgresql):
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        with pytest.raises(MissingCRSException):
            importer.run_import()


def test_single_import_with_srid_flag(engine_postgresql):
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=4326,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        importer.run_import()


def test_repeated_file_with_ignore_repeated_file(engine_postgresql):
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=4326,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=True,
        overwrite=False,
        transform=False
    ) as importer:
        importer.run_import()


def test_db_model_before_overwrite(engine_postgresql):
    insp = inspect(engine_postgresql)
    assert insp.has_schema("vienna")
    assert insp.has_table("city_object", schema="vienna")
    assert insp.has_table("cj_metadata", schema="vienna")
    assert insp.has_table("city_object_relationships", schema="vienna")

    city_object = Table(
        "city_object", MetaData(), schema="vienna",
        autoload_with=engine_postgresql
    )

    cj_metadata = Table(
        "cj_metadata", MetaData(), schema="vienna",
        autoload_with=engine_postgresql
    )

    query_city_object = select(city_object).where(
        city_object.c.object_id == "UUID_LOD2_011491-3cd51f89-4727-44e6-b12e_6"
    )
    query_cj_metadata = select(cj_metadata).where(
        cj_metadata.c.source_file == "vienna.jsonl"
    )

    query_missing_city_object = select(city_object).where(
        city_object.c.object_id == "UUID_LOD2_011515-87eee19d-0f72-4c25-99d1"
    )

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

        row = session.execute(query_missing_city_object).first()
        assert row is not None


def test_repeated_file_with_overwrite(engine_postgresql):
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna_modified/vienna.jsonl",
        db_schema="vienna",
        input_srid=4326,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=True,
        transform=False
    ) as importer:
        importer.run_import()


def test_db_model_after_overwrite(engine_postgresql):
    cj_metadata = Table(
        "cj_metadata", MetaData(),
        schema="vienna",
        autoload_with=engine_postgresql
    )

    query_cj_metadata = select(cj_metadata).where(
        cj_metadata.c.source_file == "vienna.jsonl"
    )

    city_object = Table(
        "city_object", MetaData(),
        schema="vienna",
        autoload_with=engine_postgresql
    )

    query_missing_city_object = select(city_object).where(
        city_object.c.object_id == "UUID_LOD2_011599-c429e388-91c6-4438-b244"
    )

    query_existing_city_object = select(city_object).where(
        city_object.c.object_id == "UUID_LOD2_011978-eb576db6-7fb3-427d-afe3"
    )

    with Session(engine_postgresql) as session:
        row = session.execute(query_missing_city_object).first()
        assert row is None
        row = session.execute(query_cj_metadata).first()
        assert row.source_file == "vienna.jsonl"
        assert row.version == "1.1"
        assert row.transform["scale"] == [0.001, 0.001, 0.001]
        assert row.transform["translate"] == [986.77, 340531.81, 29.09]
        row = session.execute(query_existing_city_object).first()
        assert row.id == 593


def test_repeated_file_with_prompt_to_continue(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=4326,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        importer.run_import()


def test_repeated_file_with_prompt_to_skip_file(engine_postgresql,
                                                monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("n"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=4326,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        importer.run_import()


def test_db_model(engine_postgresql):
    insp = inspect(engine_postgresql)
    assert insp.has_schema("vienna")
    assert insp.has_table("city_object", schema="vienna")
    assert insp.has_table("cj_metadata", schema="vienna")
    assert insp.has_table("city_object_relationships", schema="vienna")


def test_export_all(engine_postgresql):
    conn = engine_postgresql.raw_connection()
    with Exporter(
        connection=conn,
        schema="vienna",
        sqlquery=None,
        output="./tests/files/ex.jsonl",
    ) as exporter:
        exporter.run_export()


def test_single_import_with_srid_flag_different_from_existing_schema(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=28992,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        with pytest.raises(InconsistentCRSException):
            importer.run_import()


def test_transform_flag_with_same_SRID_than_schema(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=4326,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=True
    ) as importer:
        importer.run_import()


def test_transform_flag_with_different_SRID_than_schema(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="vienna",
        input_srid=28992,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=True
    ) as importer:
        importer.run_import()


def test_transform_flag_to_new_schema(engine_postgresql,
                                                         monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    engine_postgresql.update_execution_options(
        schema_translate_map={"vienna": "new_schema"})
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/vienna.jsonl",
        db_schema="new_schema",
        input_srid=4326,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=True
    ) as importer:
        with pytest.raises(NoSchemaSridException):
            importer.run_import()


def test_export_one(engine_postgresql):
    conn = engine_postgresql.raw_connection()
    with Exporter(
        connection=conn,
        schema="vienna",
        sqlquery="SELECT 593 as id",
        output="./tests/files/ex.jsonl",
    ) as exporter:
        exporter.run_export()


def test_directory_import(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    engine_postgresql.update_execution_options(
        schema_translate_map={"vienna": "cjdb"})
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/cjfiles",
        db_schema="cjdb",
        input_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        importer.run_import()


def test_single_import_with_extensions(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    engine_postgresql.update_execution_options(
        schema_translate_map={"vienna": "cjdb"})
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/extension.city.jsonl",
        db_schema="cjdb",
        input_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
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


def test_single_import_without_metadata(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    engine_postgresql.update_execution_options(
        schema_translate_map={"vienna": "cjdb"})
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/no_metadata.city.jsonl",
        db_schema="cjdb",
        input_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        with pytest.raises(InvalidMetadataException):
            importer.run_import()


def test_single_import_without_cityjson_obj_in_first_line(
    engine_postgresql, monkeypatch
):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    engine_postgresql.update_execution_options(
        schema_translate_map={"vienna": "cjdb"})
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/no_cityjson_obj.city.jsonl",
        db_schema="cjdb",
        input_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        with pytest.raises(InvalidCityJSONObjectException):
            importer.run_import()


def test_single_import_with_geometry_template(engine_postgresql, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    engine_postgresql.update_execution_options(
        schema_translate_map={"vienna": "cjdb"})
    with Importer(
        engine=engine_postgresql,
        filepath="./tests/files/geomtemplate.city.jsonl",
        db_schema="cjdb",
        input_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False
    ) as importer:
        importer.run_import()

    insp = inspect(engine_postgresql)
    assert insp.has_schema("cjdb")
    assert insp.has_table("city_object", schema="cjdb")
    assert insp.has_table("cj_metadata", schema="cjdb")
    assert insp.has_table("city_object_relationships", schema="cjdb")

    cj_metadata1 = Table(
        "cj_metadata", MetaData(),
        schema="cjdb",
        autoload_with=engine_postgresql
    )

    query_cj_metadata = (
        select(cj_metadata1)
        .where(cj_metadata1.c.geometry_templates.isnot(None))
        .where(cj_metadata1.c.source_file == "geomtemplate.city.jsonl")
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
