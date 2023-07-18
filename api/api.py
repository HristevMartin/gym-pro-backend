import jwt
from flask import g, Blueprint, render_template
from flask import send_from_directory
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash
from argparse import ArgumentParser
from app import db, app
from db_models.Equipment import GymItem
from db_models.forum import Forum, Reaction, View, Comment
from db_models.token import Token
from db_models.users import User, UserProfile
from managers.auth import AuthManager, auth
from managers.user import verify_user
from utils.helper import modify_name, check_if_image_is_valid, UPLOAD_FOLDER, generate_unique_id, \
    send_registration_email, send_reset_email

register_route = Blueprint('register', __name__)


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
        send_registration_email(saved_data.email)
    except Exception as ex:
        raise BadRequest("Please login")

    return '', 201


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
        return 'problem when deleting the token', 204


@register_route.route('/home')
@auth.login_required
def home():
    return 'Home'


@register_route.route('/gym-items', methods=['GET', 'POST'])
@auth.login_required
def gym_items():
    user_id = g.flask_httpauth_user.id

    filename = check_if_image_is_valid(request)
    if filename:
        data = request.form.to_dict()

        data['image_url_path'] = filename

        item_id = generate_unique_id()
        data['item_id'] = item_id
        data['user_id'] = user_id

        saved_data = GymItem(**data)
        db.session.add(saved_data)
        try:
            db.session.commit()
            return 'Gym Item created', 201
        except Exception as ex:
            return 'problem when creating the gym item', 400
    else:
        return 'problem when creating the gym item', 400


@register_route.route('/all-gym-items')
def all_gym_items():

    project = request.args.get('project')

    if project != 'local':
        gym_items = GymItem.query.all()
        gym_items_list = []
        for gym_item in gym_items:
            gym_item_dict = {
                'primary_id': gym_item.id,
                'id': gym_item.user_id,
                'item_id': gym_item.item_id,
                'name': gym_item.name,
                'category': gym_item.category,
                'price': gym_item.price,
                'image_url': gym_item.image_url,
                'image_url_path': gym_item.image_url_path,
            }
            gym_items_list.append(gym_item_dict)
        return jsonify(gym_items_list), 200

    gym_items = GymItem.query.all()
    gym_items_list = []
    for gym_item in gym_items:
        gym_item_dict = {
            'primary_id': gym_item.id,
            'id': gym_item.user_id,
            'item_id': gym_item.item_id,
            'name': gym_item.name,
            'category': gym_item.category,
            'price': gym_item.price,
            'image_url': gym_item.image_url,
            'image_url_path': gym_item.image_url_path,
        }
        gym_items_list.append(gym_item_dict)
    return jsonify(gym_items_list), 200

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
            'image_url_path': user_item.image_url_path,
            'item_id': user_item.item_id,
        }
        user_items_list.append(user_item_dict)

    return user_items_list


@register_route.route('/item-detail/<item_id>', methods=['GET', 'POST', 'DELETE'])
@auth.login_required
def item_detail(item_id):
    if request.method == 'POST':
        data = request.form.to_dict()
        if 'image_file' in request.files:
            filename = check_if_image_is_valid(request)
            if filename:
                data['image_url_path'] = filename
            else:
                return jsonify({'failure': 'image is not valid'}), 400
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
                    'image_url_path': updated_item.image_url_path,

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
            'image_url_path': item.image_url_path,
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

        if user:
            return jsonify({
                'id': user.id,
                'user_id': user.user_id,
                'name': user.name,
                'hobby': user.hobby,
                'location': user.location,
                'image': user.image_filename,
            }), 200
        else:
            return jsonify({
                'message': 'User profile not found',
            }), 404
    elif request.method == 'POST':

        filename = ''

        if request.files:
            filename = check_if_image_is_valid(request)

        user_data = UserProfile.query.filter_by(user_id=user_id).first()

        form_data = request.form.to_dict()

        if user_data:
            # Update existing user profile data
            user_data.name = form_data['name'] if form_data['name'] else user_data.name
            user_data.hobby = form_data['hobby'] if form_data['hobby'] else user_data.hobby
            user_data.location = form_data['location'] if form_data['location'] else user_data.location
            user_data.image_filename = filename if filename else user_data.image_filename

            try:
                db.session.commit()
                return filename, 201
            except Exception as ex:
                return 'Problem when updating the user profile', 400
        elif not user_data:
            # Create new user profile data

            new_user_profile = UserProfile(
                user_id=user_id,
                name=form_data['name'] if form_data['name'] else '',
                hobby=form_data['hobby'] if form_data['hobby'] else '',
                location=form_data['location'] if form_data['location'] else '',
                image_filename=filename if filename else '',
            )
            try:
                db.session.add(new_user_profile)
                db.session.commit()
                return 'User profile created', 201
            except Exception as ex:
                return 'Problem when creating the user profile', 400


@register_route.route('/upload_profile_images/<filename>')
def serve_profile_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@register_route.route('/delete_all_gym_items', methods=['DELETE'])
def delete_gym_items():
    GymItem.query.delete()
    db.session.commit()
    return 'All gym items deleted', 200


@register_route.route('/delete_email_address', methods=['DELETE'])
def delete_email_address():
    email = request.args.get('email')
    email = User.query.filter_by(email=email).first()
    db.session.delete(email)
    db.session.commit()
    return 'All email addresses deleted', 200


@register_route.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        token = AuthManager.encode_password_reset_token(user)
        sent_email = send_reset_email(user, token)
        if sent_email:
            return jsonify({
                'success': True,
                'message': 'Password reset email sent',
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Problem sending password reset email',
            }), 404
    else:
        return jsonify({
            'success': False,
            'message': 'Email address not found',
        }), 404


import os

frontend_host = os.environ.get('FRONTEND_URL')
frontend_url = frontend_host + '/login'
app.logger.info(f'show me the frontend urlllllllll: {frontend_url}')


@register_route.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'GET':
        try:
            user_id = AuthManager.decode_password_reset_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Expired token'}), 400
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 400

        # Find the user with the provided ID
        user = User.query.get(user_id)
        if not user:
            return render_template('reset_password_error.html', error='User not found')

        return render_template('reset_password_form.html', token=token)

    if request.method == 'POST':
        pw = request.form.get('new_password')
        pw2 = request.form.get('new_password_repeated')
        if pw != pw2:
            return render_template('reset_password_error.html', error='Passwords do not match')
        else:
            try:
                user_id = AuthManager.decode_password_reset_token(token)
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Expired token'}), 400
            except jwt.InvalidTokenError:
                return jsonify({'message': 'Invalid token'}), 400

            # Find the user with the provided ID
            user = User.query.get(user_id)
            if not user:
                return render_template('reset_password_error.html', error='User not found')

            user.password = generate_password_hash(pw)
            db.session.commit()

            app.logger.info(f'show me the frontend url: {frontend_url}')

            return render_template('reset_password_success.html', frontend_url=frontend_url)


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'An error occurred: {str(e)}')
    return str(e), 500


@register_route.route('/forum-data', methods=['GET', 'POST'])
@auth.login_required
def get_users():
    user_id = g.flask_httpauth_user.id

    if request.method == 'GET':
        forum_data = Forum.query.all()
        forum_data = [forum.to_dict() for forum in forum_data]
        return jsonify(forum_data), 200
    elif request.method == 'POST':
        data = request.get_json()
        forum = Forum(
            title=data['title'],
            description=data['description'],
            user_id=user_id,
        )
        db.session.add(forum)
        try:
            db.session.commit()
        except Exception as ex:
            return jsonify({
                'message': 'Problem when creating the forum'}), 400

        return jsonify({
            'message': 'Forum created'}), 201


@register_route.route('/forum-data/<forum_id>', methods=['GET', 'PUT', 'DELETE'])
@auth.login_required
def get_forum_message(forum_id):
    user_id = g.flask_httpauth_user.id

    forum = Forum.query.get(forum_id)

    if request.method == 'GET':
        if forum:
            existing_view = View.query.filter_by(user_id=user_id, forum_id=forum_id).first()
            if not existing_view:
                view = View(
                    user_id=user_id,
                    forum_id=forum_id,
                )
                db.session.add(view)
                db.session.commit()

                Forum.query.filter_by(id=forum_id).update({'views': Forum.views + 1})
                db.session.commit()
            elif Forum.query.filter_by(id=forum_id).all()[0].views == 0:
                Forum.query.filter_by(id=forum_id).update({'views': Forum.views + 1})
                db.session.commit()
        forum_data = forum.to_dict()
        return jsonify(forum_data), 200


@register_route.route('/get_forum_messages/<forum_id>', methods=['GET'])
def get_forum_messages(forum_id):
    forum_id = forum_id
    forum = Forum.query.get(forum_id)

    if forum is None:
        return 'Forum post not found', 404

    forum_messages = forum.comments
    # print('forum messages', forum_messages[0].to_dict())

    return [x.to_dict() for x in forum_messages], 200


@register_route.route('/save-emoji', methods=['POST'])
@auth.login_required
def save_emoji():
    try:
        user_id = g.flask_httpauth_user.id
        data = request.get_json()
        data['user_id'] = user_id
        existing_reaction = Reaction.query.filter_by(comment_id=data['id'], user_id=user_id).first()

        if existing_reaction:
            if existing_reaction.emoji == data['emoji']:
                # If the user already reacted with the same emoji, do nothing
                return jsonify({
                    'message': 'Reaction already exists',
                }), 200
            else:
                # If the user already reacted but with a different emoji, update the reaction
                existing_reaction.emoji = data['emoji']
                db.session.commit()
                return jsonify({
                    'message': 'Reaction updated',
                }), 200
        else:
            # If the user has not yet reacted, create a new reaction
            reaction = Reaction(user_id=user_id, comment_id=data['id'], emoji=data['emoji'])
            db.session.add(reaction)
            db.session.commit()
            forum_likes = Forum.query.get(data['forum_id'])
            if forum_likes:
                forum_likes.likes += 1
                db.session.commit()
            else:
                print(f'been here')
                pass
            return jsonify({
                'message': 'Reaction created',
                '_id': reaction.id
            }), 201

    except Exception as ex:
        return jsonify({
            'message': 'Problem when creating the reaction'}), 400


@register_route.route('/get-emoji/<int:comment_id>', methods=['GET'])
@auth.login_required
def get_emoji(comment_id):
    reactions = Reaction.query.filter_by(comment_id=comment_id).all()
    reaction_data = [{'user_id': reaction.user_id, 'emoji': reaction.emoji} for reaction in reactions]
    return jsonify(reaction_data), 200


from flask import request, jsonify


@register_route.route('/get-usernames', methods=['POST'])
def get_usernames():
    user_ids = request.get_json()

    users = User.query.filter(User.id.in_(user_ids)).all()

    usernames = {user.id: user.email.split('@')[0] for user in users}

    return jsonify(usernames), 200


@register_route.route('/save-comment/<int:forum_id>', methods=['POST'])
@auth.login_required
def save_comment(forum_id):
    user_id = g.flask_httpauth_user.id

    if request.method == 'POST':
        data = request.get_json()
        data['user_id'] = user_id
        data['forum_id'] = forum_id
        saved_data = Comment(**data)
        db.session.add(saved_data)
        try:
            db.session.commit()
            return jsonify({
                'message': 'Comment created'}), 201
        except Exception as ex:
            return jsonify({
                'message': 'Problem when creating the comment'}), 400


@register_route.route('/edit-delete-comment/<int:comment_id>', methods=['PUT', 'DELETE'])
def edit_delete_comment(comment_id):
    comment = Comment.query.get(comment_id)

    if request.method == 'PUT':
        data = request.get_json()
        comment.content = data['content']
        db.session.commit()
        data_return = comment.to_dict()
        return jsonify(data_return), 201
    elif request.method == 'DELETE':
        db.session.delete(comment)
        db.session.commit()
        return jsonify({
            'message': 'Comment deleted'}), 200

@register_route.route('/delete_comment/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    delete_comment = Comment.query.get(comment_id)
    if delete_comment:
        db.session.delete(delete_comment)
        db.session.commit()
        return jsonify({
            'message': 'Comment deleted'}), 200
    else:
        return jsonify({
            'message': 'Comment not found'}), 404
