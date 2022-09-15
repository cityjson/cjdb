import os
from modules.arg_parser import Parser, validate_args
from modules.importer import run_import


def main():
    parser = Parser()
    args = parser.parse_args()
    validation_result = validate_args(args)
    run_import(args)
    print(args)


main()