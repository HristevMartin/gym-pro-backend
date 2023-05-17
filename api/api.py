from flask import Blueprint, request, jsonify
from flask import g
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash

from db_models.Equipment import GymItem
from db_models.token import Token
from db_models.users import User, UserProfile
from app import db
from managers.auth import AuthManager, auth
from managers.user import verify_user
from utils.helper import modify_name, generate_unique_id

register_route = Blueprint('register', __name__)


# Create an upload set for images


# Define your register route here
@register_route.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    modify_name(data)

    data["password"] = generate_password_hash(str(data["password"]))
    try:
        saved_data = User(**data)
    except TypeError:
        return 'Check the fields and try again', 400

    db.session.add(saved_data)
    try:
        db.session.commit()
    except Exception as ex:
        raise BadRequest("Please login")
    return str(201)


@register_route.route('/login', methods=['POST'])
def login_user():
    user, user_id = verify_user()
    token = AuthManager.encode_token(user)
    return jsonify({"token": token, "_id": user_id}), 200


@register_route.route('/logout')
def user_logout():
    token = request.headers.get('Authorization').split()[1]
    token_db = Token.query.filter_by(token=token).first()

    if token_db:
        db.session.delete(token_db)
        try:
            db.session.commit()
            return 'User Deleted', 204
        except Exception as ex:
            return 'problem when deleting the token', 400
    else:
        return 'problem when deleting the token', 400


@register_route.route('/home')
@auth.login_required
def home():
    return 'Home'


@register_route.route('/gym-items', methods=['GET', 'POST'])
@auth.login_required
def gym_items():
    if request.method == 'POST':
        data = request.get_json()
        item_id = generate_unique_id()
        data['item_id'] = item_id
        data['user_id'] = auth.current_user().id
        gym_data = GymItem(**data)
        db.session.add(gym_data)
        try:
            db.session.commit()
            return 'Gym Item created', 201
        except Exception as ex:
            return 'problem when creating the gym item', 400


@register_route.route('/all-gym-items')
def all_gym_items():
    gym_items = GymItem.query.all()
    gym_items_list = []
    for gym_item in gym_items:
        gym_item_dict = {
            'id': gym_item.user_id,
            'item_id': gym_item.item_id,
            'name': gym_item.name,
            'category': gym_item.category,
            'price': gym_item.price,
            'image_url': gym_item.image_url,
        }
        gym_items_list.append(gym_item_dict)
    return jsonify(gym_items_list), 200


@register_route.route('/upload-user-image', methods=['POST'])
@auth.login_required
def upload_user_image():
    data = request.get_json()
    user = auth.current_user()
    updated_user = User.query.filter_by(id=user.id).update({'image_url': data['image_url']})
    try:
        db.session.add(updated_user)
        db.session.commit()
        return 'User image updated', 201
    except Exception as ex:
        return 'problem when updating the user image', 400


@register_route.route('/get-user-item')
@auth.login_required
def get_user_item():
    user_id = auth.current_user().id
    user_items = GymItem.query.filter_by(user_id=user_id).all()
    user_items_list = []
    for user_item in user_items:
        user_item_dict = {
            'id': user_item.id,
            'name': user_item.name,
            'category': user_item.category,
            'price': user_item.price,
            'image_url': user_item.image_url,
            'item_id': user_item.item_id,
        }
        user_items_list.append(user_item_dict)

    return user_items_list


@register_route.route('/item-detail/<item_id>', methods=['GET', 'PUT', 'DELETE'])
@auth.login_required
def item_detail(item_id):
    if request.method == 'PUT':
        data = request.get_json()
        GymItem.query.filter_by(item_id=item_id).update(data)
        try:
            db.session.commit()
            updated_item = GymItem.query.filter_by(item_id=item_id).first()
            return jsonify({
                'success': True,
                'gymItem': {
                    'id': updated_item.id,
                    'name': updated_item.name,
                    'category': updated_item.category,
                    'price': updated_item.price,
                    'image_url': updated_item.image_url,
                    'description': updated_item.description,
                }
            }), 200
        except Exception as ex:
            return jsonify({
                'success': False,
                'message': str(ex),
            }), 400
    elif request.method == 'DELETE':
        GymItem.query.filter_by(item_id=item_id).delete()
        try:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Item deleted successfully',
            }), 200
        except Exception as ex:
            return jsonify({
                'success': False,
                'message': str(ex),
            }), 400
    else:
        item = GymItem.query.filter_by(item_id=item_id).first()
        item_dict = {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'price': item.price,
            'image_url': item.image_url,
            'description': item.description,
        }
        return jsonify(item_dict), 200


@register_route.route('/get-category/<category>')
# @auth.login_required
def get_category(category):
    items = GymItem.query.filter_by(category=category).all()
    items_list = []
    for item in items:
        item_dict = {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'price': item.price,
            'image_url': item.image_url,
        }
        items_list.append(item_dict)

    return jsonify(items_list), 200


@register_route.route('/profile-image', methods=['GET', 'POST'])
@auth.login_required
def get_profile_image():
    user_id = g.flask_httpauth_user.id
    if request.method == 'GET':
        user = UserProfile.query.filter_by(user_id=user_id).first()
        print(user)
        print(user)
        return jsonify({
            'id': user.id,
            'user_id': user.user_id,
            'name': user.name,
            'hobby': user.hobby,
            'location': user.location,
        }), 200
    elif request.method == 'POST':
        user_data = UserProfile.query.filter_by(user_id=user_id).first()
        if user_data:
            # Update existing user profile data
            user_data.name = request.form.get('name')
            user_data.hobby = request.form.get('hobby')
            user_data.location = request.form.get('location')
            try:
                db.session.commit()
                return 'User profile updated', 201
            except Exception as ex:
                return 'Problem when updating the user profile', 400
        else:
            # Create a new user profile entry
            user_data = UserProfile(
                user_id=user_id,
                name=request.form.get('name'),
                hobby=request.form.get('hobby'),
                location=request.form.get('location')
            )
            db.session.add(user_data)
            try:
                db.session.commit()
                return 'User profile created', 201
            except Exception as ex:
                return 'Problem when creating the user profile', 400
