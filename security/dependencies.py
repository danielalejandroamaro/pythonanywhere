from fastapi import Request
from starlette.authentication import SimpleUser

from database import orm_query
from dependencies import ApiQueryParams
from security.exceptions import unauthorized_exception
from security.models import User


class UserApiQueryParams(ApiQueryParams):
    @property
    def current_user(self) -> User:
        if self.__appuser is None:
            self.__appuser = orm_query(User, User.username == self.username, get_first=True)
        return self.__appuser

    @property
    def http_method(self):
        return self.request.method

    @property
    def username(self):
        return self.__user.username

    def __init__(
            self,
            request: Request,
    ):
        super().__init__(request)
        self.__appuser = None
        self.__user: SimpleUser = getattr(request, 'user', None)
        if self.__user.is_authenticated:
            pass
        else:
            raise unauthorized_exception
