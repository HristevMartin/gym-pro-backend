from flask import request
from werkzeug.exceptions import BadRequest

from db_models.users import User

def verify_user():
    data = request.get_json()
    user = User.query.filter_by(
        email=data["email"]
    ).first()
    if not user:
        raise BadRequest("User not found")
    return user, user.id