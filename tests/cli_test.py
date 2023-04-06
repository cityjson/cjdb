from cjdb.main import run
from cjdb.modules.arg_parser import Parser
import pytest

arguments = ['-H', 'localhost', '-U', 'postgres', '-d', 'postgres']


def test_single_import():
    current_arguments = arguments.copy()
    current_arguments.append("./tests/files/extension2.jsonl")
    parser = Parser()
    args = parser.parse_args(current_arguments)
    print("Args: ", " ".join(current_arguments))
    run(args)


def test_single_import_withour_srid():
    current_arguments = arguments.copy()
    current_arguments.append("./tests/files/vienna.jsonl")
    parser = Parser()
    args = parser.parse_args(current_arguments)
    print("Args: ", " ".join(current_arguments))
    with pytest.raises(SystemExit) as excinfo:
        run(args)

    assert excinfo.value.code == 1


def test_single_import_with_target_srid():
    current_arguments = arguments.copy()
    current_arguments.append("./tests/files/vienna.jsonl")
    current_arguments.append("-I")
    current_arguments.append("7415")
    parser = Parser()
    args = parser.parse_args(current_arguments)
    print("Args: ", " ".join(current_arguments))
    run(args)
    
    # TODO: Add tests for other flags. 
    # TODO: Add data tests post import
    # TODO: Add test to postgres with testing.postgres

