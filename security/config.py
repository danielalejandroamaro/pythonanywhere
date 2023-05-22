from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from tools.config import get_not_empty_config

SECRET_KEY = get_not_empty_config('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = get_not_empty_config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
