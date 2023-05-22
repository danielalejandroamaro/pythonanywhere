from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from config import PRIMARY_KEY_USER

from engine import Base

name_table_user, id_table_user = (_split := PRIMARY_KEY_USER.split('.'))[0], _split[1]

_user_base = type("UserBaseClass", (), {
    id_table_user: Column(Integer, primary_key=True)
})


class User(Base, _user_base):
    __tablename__ = name_table_user

    username = Column(String(256), unique=True, nullable=False)
    email = Column(String(256))
    phone_number = Column(String(30), unique=True)
    is_superuser = Column(Boolean, nullable=False, server_default='false')

    # region  relationship

    password = relationship('UserPassword', back_populates="user", uselist=False, innerjoin=True, lazy='immediate')

    # endregion  relationship

    def toJson(self):
        return dict(
            id=self.id,
            username=self.username,
            email=self.email,
            phone_number=self.phone_number,
            is_superuser=self.is_superuser,
        )
