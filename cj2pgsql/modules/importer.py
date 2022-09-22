from modules.utils import open_connection, execute_sql
import os
import json
import sys
import fileinput

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
        with open("model/model.sql") as f:
            cmd = f.read().format(schema=self.args.db_schema)
        execute_sql(self.connection, cmd)

    def parse_cityjson(self):
        source_path = self.args.filepath

        if source_path.lower() == "stdin":
            for line in sys.stdin:
                process_line(line.rstrip("\n"))

        elif os.path.isfile(source_path):
            process_file(source_path)

        elif os.path.isdir(source_path):
            process_directory(source_path)

        else:
            raise Exception(f"Path: '{source_path}' not found")

    def save_to_db(self):
        pass

def read_file(filepath):
    with open(filepath) as f:
        json_content = json.load(f)

    return json_content

def process_line(line):
    try:
        line_json = json.loads(line)
        if 'metadata' in line_json:
            pass

    except:
        print(len(line))
        print(line)
        raise


def process_file(filepath):
    with open(filepath) as f:
        for line in f.readlines():
            process_line(line)

def process_directory(dir_path):
    ext = (".json", ".cityjson")
    for f in os.scandir(dir_path):
        if f.path.endswith(ext):
            process_file(f.path)