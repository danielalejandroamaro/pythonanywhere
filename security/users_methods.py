from database import orm_query
from security.models import User, UserPassword
from security.tools import get_password_hash


def update_user(username, obj):
    user = orm_query(User, User.username == username, get_first=True)
    if user:
        password = obj.pop('password', None)
        if password:
            if user.password:
                orm_update(
                    UserPassword,
                    dict(
                        pasword_hash=get_password_hash(password)
                    ),
                    UserPassword.user_id == user.id
                )
            else:
                orm_update_create(
                    UserPassword(
                        pasword_hash=get_password_hash(password),
                        user=user
                    )
                )
        if len(obj):
            orm_update(
                User,
                obj,
                User.id == user.id,
                _first=True
            )
            return orm_query(User, User.username == username, get_first=True)
        return user
    raise NotFoundError("User not found")
