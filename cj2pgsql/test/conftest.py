import pytest
import os

pytest_plugins = ["pytester"]


def pytest_generate_tests(metafunc):
    if "arguments" in metafunc.fixturenames:

        # prepare input cityjson files
        test_files_dir = "cj2pgsql/test/files"
        files = []
        for entry in os.scandir(test_files_dir):
            if entry.is_file():
                files.append(entry.path)

        # prepare sets of arguments for the CLI
        test_arguments_file = "cj2pgsql/test/inputs/arguments"
        argument_sets = []
        ids = []
        with open(test_arguments_file) as f:
            for i, line in enumerate(f.readlines(), start=1):
                stripped = line.rstrip("\n")
                if stripped and stripped[0] != '#':
                    arglist = stripped.split(" ")

                    for f in files:
                        argument_sets.append(arglist + [f])
                        ids.append(f"ARGSET_{i}:FILE_{os.path.basename(f)}")

        # parameterize tests
        metafunc.parametrize("arguments", argument_sets, ids=ids)
