from cjdb.modules.arg_parser import Parser, validate_args
from cjdb.modules.importer import Importer
from cjdb.modules.utils import get_db_engine


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
    engine = get_db_engine(args)
    with Importer(engine, args) as imp:
        imp.run_import()


def main():
    args = get_args()
    run(args)


if __name__ == "__main__":
    main()
