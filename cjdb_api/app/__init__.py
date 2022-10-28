from cjdb_api.app.vars import DEBUG, SQLALCHEMY_DATABASE_URI
from cjdb_api.app.db import db
from cjdb_api.app.ma import ma
from cjdb_api.app.routes import api_blueprint
from flask import Flask


def make_app():
    flask_app = Flask(__name__)
    flask_app.config["DEBUG"] = DEBUG
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    flask_app.config['JSON_SORT_KEYS'] = False

    db.init_app(flask_app)
    ma.init_app(flask_app)

    flask_app.register_blueprint(api_blueprint, url_prefix="/api")

    return flask_app


