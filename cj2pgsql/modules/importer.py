from modules.utils import open_connection, execute_sql
import os
import json
import sys

class Importer():
    def __init__(self, args):
        self.args = args

    def __enter__(self):
        self.connection = open_connection(self.args)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def run_import(self):
        self.prepare_database()
        self.parse_cityjson()
        self.save_to_db()

    def prepare_database(self):
        cmd = f"create schema if not exists {self.args.db_schema}"
        execute_sql(self.connection, cmd)

    def parse_cityjson(self):
        filepath = self.args.filepath
        if filepath == "stdin":
            
            k = 0
            try:
                for line in iter(sys.stdin.readline, b''):
                    k = k + 1
                    print(line)
            except KeyboardInterrupt:
                sys.stdout.flush()
                pass

        is_file, is_dir = False, False
        if os.path.isfile(filepath):
            is_file = True
        elif os.path.isdir(filepath):
            is_dir = True

        if is_file:
            process_file(filepath)

            # reading standard cityjson will not be needed. We will probably only need a CityJSONL parser
            # cityjson = read_file(filepath)
            # self.metadata = 
            pass
        elif is_dir:
            # for every cityjsonl file in directory (read it and append)
            # todo
            pass
        else:
            raise Exception(f"Path: '{filepath}' not found")

    def save_to_db(self):
        pass

def read_file(filepath):
    with open(filepath) as f:
        json_content = json.load(f)

    return json_content

def process_line(line):


def process_file(filepath):
    with open(filepath) as f:
        for line in f.readlines():
            process_line(line)
