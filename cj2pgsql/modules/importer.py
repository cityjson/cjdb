from modules.utils import open_connection, execute_sql, get_db_engine
import os
import json
import sys
from sqlalchemy.orm import Session
from model.sqlalchemy_models import ImportMetaModel, CjFeatureModel, CjObjectModel
from sqlalchemy import func

class Importer():
    def __init__(self, args):
        self.args = args
        self.import_meta = None # meta read from the file

    def __enter__(self):
        self.engine = get_db_engine(self.args)
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def run_import(self):
        self.prepare_database()
        self.parse_cityjson()
        self.save_to_db()

    def prepare_database(self):
        with open("model/model.sql") as f:
            cmd = f.read().format(schema=self.args.db_schema)
        self.engine.execute(cmd)

    def parse_cityjson(self):
        source_path = self.args.filepath

        if source_path.lower() == "stdin":
            for line in sys.stdin:
                self.process_line(line.rstrip("\n"))

        elif os.path.isfile(source_path):
            self.process_file(source_path)

        elif os.path.isdir(source_path):
            pass
            # process_directory(source_path)

        else:
            raise Exception(f"Path: '{source_path}' not found")
        
    def process_line(self, line):
        line_json = json.loads(line)
        if 'metadata' in line_json:
            import_meta = ImportMetaModel(
                source_file=os.path.basename(self.args.filepath),
                version=line_json["version"],
                transform=line_json["transform"],
                meta=line_json["metadata"]
            )

            import_meta.__table__.schema = self.args.db_schema
            self.import_meta = import_meta
            self.session.add(import_meta)
            self.session.commit()
        else:
            cj_feature = CjFeatureModel(
                feature_id = line_json["id"],
                vertices = line_json["vertices"]
            )

            cj_feature.__table__.schema = self.args.db_schema
            cj_feature.import_meta = self.import_meta
            self.session.add(cj_feature)

            for obj_id, cityobject in line_json["CityObjects"].items():
                cj_object = CjObjectModel(
                    object_id=obj_id,
                    object=cityobject
                )

                cj_object.__table__.schema = self.args.db_schema
                cj_object.cj_feature = cj_feature
                self.session.add(cj_object)


    def process_file(self, filepath):
        with open(filepath) as f:
            for line in f.readlines():
                self.process_line(line)

        self.import_meta.finished_at = func.now()
        self.session.commit()

# todo
# def process_directory(dir_path):
#     ext = (".json", ".cityjson")
#     for f in os.scandir(dir_path):
#         if f.path.endswith(ext):
#             process_file(f.path)