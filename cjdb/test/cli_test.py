import os
import subprocess
import sys
from cjdb.main import run
from cjdb.modules.arg_parser import Parser
import pytest


def test_single_import(arguments):
    parser = Parser()
    args = parser.parse_args(arguments)
    print("Args: ", " ".join(arguments))
    run(args)
    # todo - add data tests post import
