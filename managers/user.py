from flask import request
from werkzeug.exceptions import BadRequest
from werkzeug.security import check_password_hash

from db_models.users import User


def verify_user():
    data = request.get_json()
    user = User.query.filter_by(
        email=data["email"]
    ).first()
    if not user:
        raise BadRequest("User not found")
    if not check_password_hash(user.password, data['password']):
        raise BadRequest("Wrong password")
    return user, user.id
