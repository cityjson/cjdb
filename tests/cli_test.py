from click.testing import CliRunner
from cjdb.cli import cjdb
from cjdb import __version__


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(cjdb, ["--version"])
    assert result.exit_code == 0
    assert result.output == 'cjdb ' + __version__ + "\n"


def test_import_help():
    runner = CliRunner()
    result = runner.invoke(cjdb, ["import", "--help"])
    assert result.exit_code == 0


def test_export_help():
    runner = CliRunner()
    result = runner.invoke(cjdb, ["export", "--help"])
    assert result.exit_code == 0
