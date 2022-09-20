import os
from modules.arg_parser import Parser, validate_args
from modules.importer import Importer


def main():
    parser = Parser()
    args = parser.parse_args()
    validation_result, validation_msg = validate_args(args)
    
    if validation_result:
        with Importer(args) as imp:
            imp.run_import()
    else:
        raise Exception(validation_msg)


main()