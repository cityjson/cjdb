from flask import render_template, make_response, jsonify
from flask_restful import Resource

class Home(Resource):
    @classmethod
    def get(cls):
        return make_response(render_template("home.html"))

class Swagger(Resource):
    @classmethod
    def get(cls):
        return make_response(render_template("swagger.html"))
