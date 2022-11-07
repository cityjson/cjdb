from flask_sqlalchemy import SQLAlchemy as BaseSQLAlchemy
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from cjdb_api.app.vars import CONN_STRING

# naming_convention = {
#     "ix": "ix_%(column_0_label)s",
#     "uq": "uq_%(column_0_label)s",
#     "ix": "ix_%(column_0_label)s",
#     "ix": "ix_%(column_0_label)s",
#     "ix": "ix_%(column_0_label)s",
# }
metadata = MetaData(schema='public')


db = BaseSQLAlchemy(metadata=metadata)
engine = create_engine(CONN_STRING, client_encoding="utf8")
session = db.session
