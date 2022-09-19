import os
from dotenv import load_dotenv

# this is the file for application-wide parameters
# for example if it should be launched in debug mode
print(os.getcwd())
load_dotenv(".env")

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
