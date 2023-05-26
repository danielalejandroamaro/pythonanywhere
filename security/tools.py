from datetime import timedelta, datetime
from typing import Optional

from fastapi import Depends
from jose import jwt, JWTError

from database import orm_query
from security.config import SECRET_KEY, ALGORITHM, pwd_context, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme
from security.exceptions import expired_credentials_exception
from security.models import User
from tools.types import first


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(plain_password):
    return pwd_context.hash(plain_password)


def authenticate_user(username: str, plain_password: str):
    _user: User = first(
        orm_query(
            User,
            User.username == username
        ), raise_on_empty=False
    )
    if not _user:
        return None
    if not verify_password(plain_password, _user.password.pasword_hash):
        return None
    return _user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, secret_key=None):
    secret_key = secret_key or SECRET_KEY
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def token_decode(token: str, secret_key=None):
    secret_key = secret_key or SECRET_KEY
    try:
        decode = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        """During decode if exp is current in token it is already validated but can't be cases thant was it deleted"""
        if decode.get("exp") is None:
            raise expired_credentials_exception
        return decode
    except JWTError as err:
        raise expired_credentials_exception


async def validate_token(token: str = Depends(oauth2_scheme)) -> str:
    """return username"""
    return validate_token_core(token)


def validate_token_core(token: str,secret_key=None) -> str:
    """return username"""
    payload = token_decode(token,secret_key)
    username: str = payload.get("sub")
    if username is None:
        raise expired_credentials_exception
    return username
