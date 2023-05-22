from fastapi import Depends, Request, HTTPException
from starlette.authentication import AuthenticationBackend, AuthCredentials, AuthenticationError, SimpleUser

from database import orm_query
from security.config import oauth2_scheme
from security.exceptions import Inactive_user_exception
from security.models import User
from security.tools import validate_token


#  Base from documentation https://www.starlette.io/authentication/
# class BasicAuthBackend(AuthenticationBackend):
#     async def authenticate(self, conn):
#         if "Authorization" not in conn.headers:
#             return
#
#         auth = conn.headers["Authorization"]
#         try:
#             scheme, credentials = auth.split()
#             if scheme.lower() != 'basic':
#                 return
#             decoded = base64.b64decode(credentials).decode("ascii")
#         except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
#             raise AuthenticationError('Invalid basic auth credentials')
#
#         username, _, password = decoded.partition(":")
#         # TODO: You'd want to verify the username and password here.
#         return AuthCredentials(["authenticated"]), SimpleUser(username)

class BearerAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        if "Authorization" not in conn.headers:
            return

        try:
            token = await oauth2_scheme(conn)
            username = await validate_token(token)
        except (ValueError, UnicodeDecodeError) as exc:
            raise AuthenticationError('Invalid bearer auth credentials')
        except HTTPException as exc:
            raise AuthenticationError(exc)

        return AuthCredentials(["authenticated"]), SimpleUser(username)


async def get_current_user(
        request: Request,
        username: str = Depends(validate_token)
):
    user = getattr(request, 'user')
    if user:
        return user
    return orm_query(User, User.username == username, get_first=True)


async def get_current_active_user(user=Depends(get_current_user)):
    if user is None or user.disabled:
        raise Inactive_user_exception
    return user


def isSuperUser(user: Depends(get_current_user)):
    return user.is_superuser
