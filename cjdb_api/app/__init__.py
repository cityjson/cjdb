from cjdb_api.app.vars import DEBUG, CONN_STRING
from cjdb_api.app.db import db
from cjdb_api.app.ma import ma
from cjdb_api.app.routes import api_blueprint
from cjdb_api.app.routes.v1 import v1_api_blueprint
from flask import Flask


def make_app():
    flask_app = Flask(__name__)
    flask_app.config["DEBUG"] = DEBUG
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = CONN_STRING
    flask_app.config['JSON_SORT_KEYS'] = False

    db.init_app(flask_app)
    ma.init_app(flask_app)

    flask_app.register_blueprint(api_blueprint, url_prefix="/")
    flask_app.register_blueprint(v1_api_blueprint, url_prefix="/v1")
    
    return flask_app
