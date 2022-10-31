import pytest
import os

pytest_plugins = ["pytester"]


def pytest_generate_tests(metafunc):
    if "arguments" in metafunc.fixturenames:

        # prepare input cityjson files
        test_files_dir = "cj2pgsql/test/files"
        files = []
        for entry in os.scandir(test_files_dir):
            files.append(entry.path)

        # prepare sets of arguments for the CLI
        test_arguments_file = "cj2pgsql/test/inputs/arguments"
        argument_sets = []
        ids = []
        arg_set_cnt = 0
        with open(test_arguments_file) as f:
            for line in f.readlines():
                stripped = line.rstrip("\n")
                if stripped and stripped[0] != '#':
                    arg_set_cnt += 1
                    arglist = stripped.split(" ")

                    for f in files:
                        argument_sets.append(arglist + [f])
                        ids.append(f"ARGSET_{arg_set_cnt}:FILE_{os.path.basename(f)}")

        # parameterize tests
        metafunc.parametrize("arguments", argument_sets, ids=ids)
