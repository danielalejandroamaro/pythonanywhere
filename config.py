import os
from tools.config import get_not_null_config

is_debug = get_not_null_config("DEBUG", False, cast=bool)
APP_NAME = get_not_null_config("APP_NAME", "app", cast=str)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

PRIMARY_KEY_USER = get_not_null_config("PRIMARY_KEY_USER", 'user_account.id', cast=str)

_primary_key_user = PRIMARY_KEY_USER.split('.')  # ['user_account','id']
USER_TABLE_NAME = _primary_key_user.pop(0)  # 'user_account'
USER_KEY_IDENTIFIER = _primary_key_user.pop(0)  # 'id'
USER_PROTECTED_FILED = [USER_KEY_IDENTIFIER, 'is_superuser']  # ['id', 'is_superuser']
