from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.authentication import SimpleUser

from database import orm_update_create, row2dict, orm_query
from ..access import get_current_user
from ..api_version import v1
from ..dependencies import UserApiQueryParams
from ..exceptions import (
    credentials_exception,
    unauthorized_exception,
    missing_arguments_required
)
from ..models import User, UserPassword
from ..tools import authenticate_user, create_access_token, get_password_hash
from ..users_methods import update_user


class UserModel(BaseModel):
    password: str
    username: str
    email: Optional[str]
    phone_number: Optional[str]


@v1.post("/signup")
async def singup(
        user: UserModel = Depends()
):
    print(user)
    new_user_obj = {
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
    }
    password = user.password

    new_user = User(
        **new_user_obj
    )
    if password:
        password = UserPassword(
            pasword_hash=get_password_hash(password),
            user=new_user
        )
    orm_update_create(new_user, password, now=True)
    return row2dict(new_user)


async def put_user(
        common_parameter: UserApiQueryParams
):
    username = common_parameter.get(User.username.key)
    if username is None:
        raise missing_arguments_required(User.username.key)
    if common_parameter.current_user.is_superuser:
        pass
    elif common_parameter.username == username:
        pass
    else:
        raise unauthorized_exception

    user_updated = update_user(
        username, await common_parameter.obj
    )
    return row2dict(user_updated)


@v1.get('/me')
async def get_me(
        user: SimpleUser = Depends(get_current_user)
):
    from security.models import User
    _user = orm_query(
        User,
        User.username == user.username,
        get_first=True,
        raise_on_not_found=True
    )
    return row2dict(_user)


class Token(BaseModel):
    access_token: str
    token_type: str


@v1.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise credentials_exception
    access_token = create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}

#
# def load_routes():
#     is_superuser_user = IsSuperUser()
#     factory_routes(
#         v1,
#         User.__tablename__,
#         methods_allowed=HTTPMethod.all_as_dict(
#             is_superuser_user
#         ).update({
#             HTTPMethod.GET: None
#         }),
#         methods={
#             HTTPMethod.PUT: put_user,
#             HTTPMethod.POST: async_run_raise(
#                 Operation_not_permitted
#             )  # remove post option
#         })
#
#
# load_routes()
