from abc import ABC, abstractmethod

from . import User
from .dependencies import UserApiQueryParams


class ScopeValidator(ABC):
    def __init__(self):
        self.__table__ = User.__table__

    @property
    def userTable(self):
        return self.__table__

    @staticmethod
    def isMe(common_parameter: UserApiQueryParams):
        username = common_parameter.get(User.username.key, None)
        if username and username == common_parameter.username:
            return True
        return False

    @staticmethod
    def isSuperUser(common_parameter):
        if common_parameter.current_user.is_superuser:
            return True
        return False

    @abstractmethod
    def __call__(self, table_name, common_parameter, obj=None):
        pass


class IsSuperUser(ScopeValidator):
    def __call__(self, table_name, common_parameter: UserApiQueryParams, obj=None):
        return self.isSuperUser(common_parameter)
