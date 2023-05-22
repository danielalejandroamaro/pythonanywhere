from fastapi import status, HTTPException

# DON'T TOUCH !!
RE_LOGIN_STR = 'please re-login'
LOGIN_STR = 'please login'

missing_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing Bearer credentials, " + LOGIN_STR,
    headers={"WWW-Authenticate": "Bearer"},
)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password"
)

unauthorized_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="permission denied",
    headers={"WWW-Authenticate": "Bearer"},
)

expired_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Your access was expired " + RE_LOGIN_STR,
    headers={"WWW-Authenticate": "Bearer"},
)

Operation_not_permitted = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Operation not permitted"
)

Inactive_user_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Inactive user"
)


def access_violation_exception(details):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"access violation exception\n{details}",
        headers={"WWW-Authenticate": "Bearer"},
    )


def missing_arguments_required(*arguments):
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Missing Arguments Required {arguments}"
    )


def run_raise(exception):
    def decorator():
        raise exception

    return decorator


def async_run_raise(exception):
    async def decorator():
        raise exception

    return decorator


class InvalidOperationError(Exception):
    pass
