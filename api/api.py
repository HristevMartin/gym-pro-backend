import jwt
from flask import g, Blueprint, render_template
from flask import send_from_directory
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash

from app import db, app
from db_models.Equipment import GymItem, Rating, CommentItem, Like
from db_models.forum import Forum, Reaction, View, Comment
from db_models.token import Token
from db_models.users import User, UserProfile, UserActivity
from managers.auth import AuthManager, auth
from managers.user import verify_user
from utils.helper import modify_name, check_if_image_is_valid, UPLOAD_FOLDER, generate_unique_id, \
    send_registration_email, send_reset_email
import logging

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
        return "Please login", 401

    return '', 201


@register_route.route('/login', methods=['POST'])
def login_user():
    user, user_id = verify_user()
    token = AuthManager.encode_token(user)

    from datetime import datetime

    login_time = datetime.now()

    # Create a new UserActivity record for login
    activity = UserActivity(user_id=user_id, login_time=login_time, last_seen=login_time)
    db.session.add(activity)
    db.session.commit()

    return jsonify({"token": token, "_id": user_id}), 200


from datetime import datetime


@register_route.route('/logout')
def user_logout():
    token = request.headers.get('Authorization').split()[1]
    token_db = Token.query.filter_by(token=token).first()

    if token_db:
        user_id = token_db.user_id

        latest_activity = UserActivity.query.filter_by(user_id=user_id, logout_time=None).order_by(
            UserActivity.login_time.desc()).first()

        if latest_activity:
            logout_time = datetime.now()

            latest_activity.logout_time = logout_time

            try:
                db.session.delete(token_db)
                db.session.commit()
                return 'User logged out successfully', 204
            except Exception as ex:
                return 'Problem when logging out', 500
        else:
            return 'User is not currently active', 404
    else:
        return 'Invalid token', 401


@register_route.route('/home')
def home():
    return 'Home'

@register_route.route('/check-env')
def check_env():
    # Fetch the values of the environment variables
    gcp_service_account = os.getenv('GCP_SERVICE_ACCOUNT', 'Not Set')
    your_env_var = os.getenv('YOUR_ENV_VAR', 'Not Set')
    print('gcp_service_account', gcp_service_account)
    print('your_env_var', your_env_var)

    logging.info('gcp_service_account', gcp_service_account)
    logging.info('your_env_var', your_env_var)

    # Return the values in JSON format
    return jsonify({
        'GCP_SERVICE_ACCOUNT': gcp_service_account,
        'YOUR_ENV_VAR': your_env_var
    }), 200

@register_route.route('/gym-items', methods=['GET', 'POST'])
@auth.login_required
def gym_items():
    user_id = g.flask_httpauth_user.id

    filename = check_if_image_is_valid(request)
    logging.info('filename is', filename)
    logging.info('filename is2', filename)
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
            logging.error(f"Error while creating gym item: {ex}")
            return 'problem when creating the gym item', 400
    else:
        return 'problem when creating the gym item', 400


@register_route.route('/single-gym-item/<item_id>', methods=['GET'])
def get_single_gym_item(item_id):
    gym_item = GymItem.query.filter_by(item_id=item_id).first()
    gym_item_dict = {
        'image_url_path': gym_item.image_url_path,
    }
    return jsonify(gym_item_dict), 200


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
                'location': gym_item.location,
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
        data.pop('', None)
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
                    'seller': updated_item.seller,
                    'quantity': updated_item.quantity,
                    'location': updated_item.location,
                    'mobile_number': updated_item.mobile_number,

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
            'seller': item.seller,
            'quantity': item.quantity,
            'location': item.location,
            'mobile_number': item.mobile_number,
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

frontend_host = os.environ.get('FRONTEND_URL', 'none')
frontend_url = frontend_host + '/login'


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
        print(f"Received payload: {data}")
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
    elif request.method == 'PUT':
        data = request.get_json()
        forum.title = data['title']
        forum.description = data['description']
        db.session.commit()
        return jsonify({
            'message': 'Forum updated'}), 200
    elif request.method == 'DELETE':
        if not forum:
            return jsonify({"message": "Forum not found"}), 404

        view_delete = View.query.filter_by(forum_id=forum.id, user_id=user_id).first()
        if view_delete:
            db.session.delete(view_delete)

        db.session.delete(forum)
        db.session.commit()

        return jsonify({'message': 'Forum deleted'}), 200


@register_route.route('/get_forum_messages/<forum_id>', methods=['GET', 'DELETE'])
def get_forum_messages(forum_id):
    if request.method == 'GET':
        forum_id = forum_id
        forum = Forum.query.get(forum_id)

        if forum is None:
            return 'Forum post not found', 404

        forum_messages = forum.comments
        # print('forum messages', forum_messages[0].to_dict())

        return [x.to_dict() for x in forum_messages], 200
    elif request.method == 'DELETE':
        forum = Forum.query.get(forum_id)
        if forum is None:
            return 'Forum not found', 404

        forum_comments = forum.comments
        for comment in forum_comments:
            db.session.delete(comment)

        db.session.commit()
        return jsonify({
            'message': 'Comments associated with the forum deleted'
        }), 200


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
        # increment comments count by 1
        forum = Forum.query.filter_by(id=forum_id).first()

        forum.comments_num = len(Comment.query.filter_by(forum_id=forum_id).all()) + 1

        db.session.add(forum)
        db.session.commit()

        data = request.get_json()
        data['user_id'] = user_id
        data['forum_id'] = forum_id
        saved_data = Comment(**data)
        db.session.add(saved_data)
        try:
            db.session.commit()

            # Increment the comment count for the corresponding forum

            return jsonify({
                'message': 'Comment created'}), 201
        except Exception as ex:
            print('show me the ex', ex)
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
    forum_id = request.args.get('forum_id')
    delete_comment = Comment.query.get(comment_id)

    if delete_comment:
        db.session.delete(delete_comment)
        db.session.commit()
        print('show me the forum_IDDDDD', forum_id)
        if forum_id:
            print('here')
            forum = Forum.query.get(forum_id)
            forum.comments_num -= 1
            db.session.commit()

        return jsonify({
            'message': 'Comment deleted'}), 200
    else:
        return jsonify({
            'message': 'Comment not found'}), 404


@register_route.route('/get-active-users', methods=['GET'])
def get_active_users():
    from datetime import datetime, timedelta

    current_time = datetime.now()
    active_threshold = timedelta(hours=6)  # Changed from minutes to hours

    active_users_activities = UserActivity.query.filter(UserActivity.last_seen >= current_time - active_threshold, UserActivity.logout_time == None).all()

    active_user_ids = list(set([activity.user_id for activity in active_users_activities]))

    user_profile_pictures = {user.user_id: user.image_filename for user in UserProfile.query.all()}

    user_profiles_list = []

    users = User.query.filter(User.id.in_(active_user_ids)).all()

    for user_data in active_user_ids:
        user_info = {}
        user_id = user_data

        user_info['user_image'] = user_profile_pictures.get(user_id, None)

        for user in users:
            if user.id == user_id:
                user.email = user.email.split('@')[0]
                user_info['user_name'] = user.email
                user_profiles_list.append(user_info)

    if len(user_profiles_list) == 0:
        return jsonify({
            'message': 'No active users found'
        }), 404

    return jsonify(user_profiles_list), 200


@register_route.route('/ping', methods=['POST'])
@auth.login_required
def ping():
    # Identify the user
    user_id = g.flask_httpauth_user.id
    print('been here')
    # Get the UserActivity record for this user
    activity = UserActivity.query.filter_by(user_id=user_id).first()

    # If there's no activity record for this user, something is wrong.
    # In a production environment, you'd probably want to handle this case differently.
    if not activity:
        return jsonify({'error': 'No activity record found for this user'}), 404

    # Update the last_seen time and commit the changes
    activity.last_seen = datetime.now()
    db.session.commit()

    # Return a success status
    return jsonify({'status': 'success'}), 200


@register_route.route('/remove-emoji', methods=['POST'])
@auth.login_required
def remove_emoji():
    user_id = g.flask_httpauth_user.id
    try:
        data = request.get_json()
        id = data['id']
        emoji = data['emoji']

        reaction = Reaction.query.filter_by(
            comment_id=id,
            emoji=emoji,
            user_id=user_id
        ).first()

        if not reaction:
            return jsonify({'message': 'Reaction not found'}), 400

        db.session.delete(reaction)

        forum_likes = Forum.query.get(data['forum_id'])
        forum_likes.likes -= 1
        db.session.commit()

        return jsonify({'message': 'Reaction removed successfully'}), 200

    except Exception as e:
        print(e)
        return jsonify({'message': 'Server error'}), 500


@register_route.route('/save-rating', methods=['POST'])
@auth.login_required
def save_rating():
    user_id = g.flask_httpauth_user.id
    try:
        # Get data from the request's JSON body
        data = request.get_json()
        if user_id:
            data['user_email'] = User.query.filter_by(id=user_id).first().email

        item_id = data['itemId']
        star_rating = data['rating']

        # Check if the user has already rated the item
        existing_rating = Rating.query.filter_by(user_id=user_id, item_id=item_id).first()

        if existing_rating:
            if star_rating != existing_rating.star_rating:
                # If there's an existing rating, update it
                existing_rating.star_rating = star_rating
                db.session.commit()
                user_response = {
                    'user_rating': existing_rating.star_rating,
                    'user_id': user_id,
                }
                return jsonify(user_response), 200
            elif star_rating == existing_rating.star_rating:
                db.session.delete(existing_rating)
                db.session.commit()

                return jsonify({'message': 'Rating deleted successfully!'}), 204
        else:
            new_rating = Rating(user_id=user_id, item_id=item_id, star_rating=star_rating)
            db.session.add(new_rating)
            db.session.commit()
            user_response = {
                'user_rating': new_rating.star_rating,
                'user_id': user_id,
            }
            return jsonify(user_response), 201

    except Exception as e:
        return jsonify({'message': 'An error occurred while saving the rating.', 'error': str(e)}), 500

from sqlalchemy import func, text


@register_route.route('/get-ratings/<item_id>', methods=['GET'])
@auth.login_required
def get_ratings(item_id):
    try:
        # Aggregate ratings for the given item_id
        average_rating = db.session.query(func.avg(Rating.star_rating)).filter_by(item_id=item_id).scalar()
        total_ratings = Rating.query.filter_by(item_id=item_id).count()

        # If there's no rating, default average to 0
        average_rating = float(average_rating) if average_rating else 0
        user_rating = Rating.query.filter_by(item_id=item_id, user_id=g.flask_httpauth_user.id).first()

        user_raiting = user_rating.star_rating if user_rating else 0

        print('successfull', user_raiting)

        item = {
            'item_id': item_id,
            'user_rating': user_raiting,
            'average_rating': round(average_rating, 2),
            'total_ratings': total_ratings
        }
        print('show me item', item)
        return jsonify(item), 200

    except Exception as e:
        return jsonify({'message': 'An error occurred while fetching the ratings.', 'error': str(e)}), 500
    
@register_route.route('/save-comment', methods=['POST'])
@auth.login_required
def save_comment_item():
    if request.method == 'POST':
        user_id = g.flask_httpauth_user.id
        data = request.get_json()
        comment_content = data.get('comment')
        item_id = data.get('itemId')

        if not comment_content or not user_id:
            return jsonify({"message": "Comment and UserID are required!"}), 400


        new_comment = CommentItem(content=comment_content, user_id=user_id, gym_id=item_id)
        db.session.add(new_comment)
        db.session.commit()

        return jsonify({"message": "Comment saved successfully!"}), 201


@register_route.route('/get-comments/<item_id>', methods=['GET'])
@auth.login_required
def get_comments(item_id):
    try:
        comments = CommentItem.query.filter_by(gym_id=item_id).all()

        if not comments:
            return jsonify({"message": "No comments found!"}), 404

        comments_list = []
        for comment in comments:
            comment_data = {}
            comment_data['comment_id'] = comment.id
            comment_data['comment'] = comment.content
            comment_data['user_id'] = comment.user_id
            comment_data['gym_id'] = comment.gym_id

            comments_list.append(comment_data)

        return jsonify({"comments": comments_list}), 200

    except Exception as e:
        return jsonify({'message': 'An error occurred while fetching the comments.', 'error': str(e)}), 500

@register_route.route('/modify-comment/<comment_id>', methods=['PUT', 'DELETE'])
@auth.login_required
def modify_comment(comment_id):
    if request.method == 'PUT':
        user_id = g.flask_httpauth_user.id
        data = request.get_json()
        comment_content = data.get('edited_comment')
        item_id = data.get('item_id')

        if not comment_content or not user_id:
            return jsonify({"message": "Comment and UserID are required!"}), 400

        comment = CommentItem.query.filter_by(id=comment_id).first()

        if not comment:
            return jsonify({"message": "Comment not found!"}), 404

        comment.content = comment_content
        comment.user_id = user_id
        comment.gym_id = item_id

        try:
            db.session.commit()
        except Exception as e:
            return jsonify({"message": "An error occurred while updating the comment.", "error": str(e)}), 500
        return jsonify({"message": comment.content}), 200
    elif request.method == 'DELETE':
        comment = CommentItem.query.filter_by(id=comment_id).first()

        if not comment:
            return jsonify({"message": "Comment not found!"}), 404

        try:
            db.session.delete(comment)
            db.session.commit()

            return jsonify({"message": "Comment deleted successfully!"}), 204
        except Exception as e:
            return jsonify({"message": "An error occurred while deleting the comment.", "error": str(e)}), 500

@register_route.route('/likes/<comment_id>', methods=['GET', 'POST'])
@auth.login_required
def manage_likes(comment_id):
    if request.method == 'GET':
        comment_likes = Like.query.filter_by(comment_id=comment_id).all()

        # Aggregate total likes
        total_likes = sum([comment_like.like_count for comment_like in comment_likes])

        user_has_liked = any(comment_like.user_id == g.flask_httpauth_user.id for comment_like in comment_likes)
        print('show me user has liked', user_has_liked)
        print('show me user_id', g.flask_httpauth_user.id)
        return jsonify({"like_count": total_likes, "user_has_liked": user_has_liked})

    elif request.method == 'POST':
        user_id = g.flask_httpauth_user.id
        data = request.get_json()
        # Check if user has already liked the comment
        existing_like = Like.query.filter_by(comment_id=comment_id, user_id=user_id).first()
        if existing_like:
            # If user has already liked the comment, unlike it
            db.session.delete(existing_like)
            db.session.commit()
            total_like_per_comment = len([x.comment_id for x in Like.query.filter_by(comment_id=comment_id).all()])
            return jsonify({"action": "unliked", "success": True, 'like_count': total_like_per_comment}), 200

        else:
            comment_like = Like(comment_id=comment_id, like_count=1, item_id=data['itemId'], user_id=user_id)
            db.session.add(comment_like)
            db.session.commit()
            like_count = len([x.comment_id for x in Like.query.filter_by(comment_id=comment_id).all()])
            return jsonify({"success": True, "like_count": like_count}), 201
