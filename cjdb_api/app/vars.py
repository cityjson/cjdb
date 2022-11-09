import os
from dotenv import load_dotenv
from model.sqlalchemy_models import ImportMetaModel, CjObjectModel, FamilyModel
from cjdb_api.app.arg_parser import Parser


parser = Parser()
args = parser.parse_args()

DEBUG = args.debug_mode
CONN_STRING = args.conn_string or os.environ.get("CJDB_CONN_STRING")
DB_SCHEMA = args.db_schema
PORT = args.port

ImportMetaModel.__table__.schema = DB_SCHEMA
CjObjectModel.__table__.schema = DB_SCHEMA
FamilyModel.__table__.schema = DB_SCHEMA

