import argparse

def Parser():
    parser = argparse.ArgumentParser(description='Import CityJSON to a PostgreSQL database')

    parser.add_argument('file', type=str,
                        help='source CityJSON file')
    parser.add_argument('-H', '--host',
                        help='PostgreSQL database host')
    parser.add_argument('-p', '--port',
                        help='PostgreSQL database port')
    parser.add_argument('-U', '--user',
                        help='PostgreSQL database user name')
    parser.add_argument('-d', '--database',
                        help='PostgreSQL database name')
    parser.add_argument('-t', '--table',
                        help='Target database table')

    return parser


def validate_args(args):
    pass