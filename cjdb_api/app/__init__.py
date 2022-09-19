from app.vars import DEBUG, SQLALCHEMY_DATABASE_URI
from app.db import db
from app.ma import ma
from flask import Flask
from app.routes import api_blueprint

def make_app():
    flask_app = Flask(__name__)
    flask_app.config["DEBUG"] = DEBUG
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

    db.init_app(flask_app)
    ma.init_app(flask_app)

    flask_app.register_blueprint(api_blueprint, url_prefix="/api")

    return flask_app


