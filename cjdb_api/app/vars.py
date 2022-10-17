import os
from dotenv import load_dotenv
from model.sqlalchemy_models import ImportMetaModel, CjObjectModel

# this is the file for application-wide parameters
# for example if it should be launched in debug mode
print(os.getcwd())
load_dotenv("../.env")

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
DB_SCHEMA = os.environ.get("DB_SCHEMA", "cjdb")

ImportMetaModel.__table__.schema = DB_SCHEMA
CjObjectModel.__table__.schema = DB_SCHEMA

