from flask import request, json, Response, Blueprint
from ..models.UserModel import UserModel, UserSchema
from ..shared.Authentication import Auth
from flask import jsonify, g

user_api = Blueprint('users', __name__)
user_schema = UserSchema()

@user_api.route('/', methods=['POST'])
def create():
  req_data = request.get_json()
  data = user_schema.load(json.loads(json.dumps(req_data)))
  
  user_in_db = UserModel.get_user_by_email(data.get('email'))
  if user_in_db:
    message = {'error': 'User already exist, please supply another email address'}
    return custom_response(message, 400)
  
  user = UserModel(data)
  user.save()

  ser_data = user_schema.dump(user)

  token = Auth.generate_token(ser_data.get('id'))

  return custom_response({'jwt_token': token}, 201)

@user_api.route('/login', methods=['POST'])
def login():
  req_data = request.get_json()

  data = user_schema.load(json.loads(json.dumps(req_data)), partial=True)
  
  if not data.get('email') or not data.get('password'):
    return custom_response({'error': 'you need email and password to sign in'}, 400)
  
  user = UserModel.get_user_by_email(data.get('email'))

  if not user:
    return custom_response({'error': 'invalid credentials'}, 400)
  
  if not user.check_hash(data.get('password')):
    return custom_response({'error': 'invalid credentials'}, 400)
  
  ser_data = user_schema.dump(user)
  
  auth_return = Auth.generate_token(ser_data.get('id'))

  if isinstance(auth_return, Response):
    return auth_return
  else:
    return custom_response({'jwt_token': auth_return}, 200)

@user_api.route('/', methods=['GET'])
@Auth.auth_required
def get_all():
  users = UserModel.get_all_users()
  ser_users = user_schema.dump(users, many=True)
  return custom_response(ser_users, 200)

@user_api.route('/<int:user_id>', methods=['GET'])
@Auth.auth_required
def get_a_user(user_id):
  user = UserModel.get_one_user(user_id)
  if not user:
    return custom_response({'error': 'user not found'}, 404)
  
  ser_user = user_schema.dump(user).data
  return custom_response(ser_user, 200)

@user_api.route('/me', methods=['PUT'])
@Auth.auth_required
def update():
  req_data = request.get_json()

  data = user_schema.load(json.loads(json.dumps(req_data)), partial=True)

  user = UserModel.get_one_user(g.user.get('id'))
  user.update(data)
  ser_user = user_schema.dump(user)
  return custom_response(ser_user, 200)

@user_api.route('/me', methods=['DELETE'])
@Auth.auth_required
def delete():
  user = UserModel.get_one_user(g.user.get('id'))
  user.delete() 
  return custom_response({'message': 'deleted'}, 204)

@user_api.route('/me', methods=['GET'])
@Auth.auth_required
def get_me():
  user = UserModel.get_one_user(g.user.get('id'))
  ser_user = user_schema.dump(user)
  return custom_response(ser_user, 200)
  

def custom_response(res, status_code):
  return Response(
    mimetype="application/json",
    response=json.dumps(res),
    status=status_code
  )