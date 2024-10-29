"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = User.query.all()
        if not users:
            return jsonify({"error": "No hay usuarios"}),400
        serialized_users = [user.serialize() for user in users]
        return jsonify({"users": serialized_users}),200
    except Exception as error:
        return jsonify({"error":str(error)}),400


@app.route("/user", methods=["POST"]) 
def create_user():
    request_body = request.get_json()

    email = request_body.get("email", None)
    password = request_body.get("password", None)
    is_active = request_body.get("is_active", True)

    required_fields = ["email", "password"]

    for field in required_fields:
        if field not in request_body:
            return jsonify({"error": f"Falta el campo {field}"}),400

    if email is None or password is None:
        return jsonify({"error": "No se recibió el email o la contraseña"}),400
    
    user = User(email=email, password=password, is_active=is_active)

    try:
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        return jsonify({"message": f"User {user.email} created successfully!"}),201
    
    except Exception as error:
        return jsonify({"error": f"{error}"}),500
    

@app.route("/user/<int:user_id>", methods=["GET"])
def get_user_id(user_id):
    try:
        user_id = User.query.get(user_id)
        if user_id is None:
            return jsonify({"error": "Este user_id no se encuentra"}),404
        return jsonify({"user": user_id.serialize()}),200
    except Exception as error:
        return jsonify({"error": f"falta el campo{error}"})
    
@app.route("/user/<int:user_id>", methods=["DELETE"])
def get_user_delete(user_id):
    try:
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"message":"Este usuario no se encuentra"}),400
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message":f"Este usuario {user_id} esta borrado"}),200

    except Exception as error:
        db.session.rollback()
        return jsonify({"error":f"{error}"}),500    
    
@app.route("/user/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    body = request.json

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User no se encuentra"}),404
    
    required_fields =["email", "password"]

    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        return jsonify({"error": f"Missing fields:{', '.join(missing_fields)}"}),400
    
    email = body.get("email", None)
    password = body.get("password", None)

    user.email = email
    user.password = password

    try:
        db.session.commit()
        return jsonify({"user": user.serialize()}),200
    
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}),500
        

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
