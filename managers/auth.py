from datetime import datetime, timedelta

import jwt
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import BadRequest

from db_models.token import Token
from main import db


class AuthManager:
    @staticmethod
    def encode_token(user):
        payload = {
            "sub": user.id,
            "exp": datetime.utcnow() + timedelta(days=100),
            "role": user.__class__.__name__,
        }
        token = jwt.encode(payload, key='verysecrettoken', algorithm="HS256")

        new_token = Token(
            token=token,
            user_id=user.id,
            role=user.__class__.__name__,
            expiration_time=payload["exp"]
        )
        db.session.add(new_token)
        db.session.commit()

        return token

    @staticmethod
    def decode_token(token):
        try:
            data = jwt.decode(token, key='verysecrettoken', algorithms=["HS256"])
            return data["sub"], data["role"]

        except jwt.ExpiredSignatureError:
            raise BadRequest("Token expired")

        except jwt.InvalidTokenError:
            raise BadRequest("Invalid token")


auth = HTTPTokenAuth(scheme="Bearer")


@auth.verify_token
def verify_token(token):
    from db_models.users import User
    user_id, role = AuthManager.decode_token(token)

    # retrieve the token from the database
    token_entry = Token.query.filter_by(token=token).first()
    if token_entry is None:
        return None

    # check if the token has expired
    if token_entry.expiration_time < datetime.utcnow():
        return None

    user = eval(f"{role}.query.filter_by(id={user_id}).first()")
    return user
