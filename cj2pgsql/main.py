from cj2pgsql.modules.arg_parser import Parser, validate_args
from cj2pgsql.modules.importer import Importer


def get_args():
    parser = Parser()
    args = parser.parse_args()
    validation_result, validation_msg = validate_args(args)
    
    if validation_result:
        return args
    else:
        raise Exception(validation_msg)


# organized like this to be able to call it in tests and also as CLI
def run(args):
    with Importer(args) as imp:
        imp.run_import()

def main():
    args = get_args()
    run(args)


if __name__ == "__main__":
    main()