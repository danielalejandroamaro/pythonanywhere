from decouple import config


def get_not_null_config(key, default=None, cast=None):
    kwargs = {} if cast is None else {"cast": cast}
    value = config(key, default, **kwargs)
    if value is None:
        raise Exception(f'Missing {key} on .env')
    return value


def get_not_empty_config(key, default=None, cast=None):
    value = get_not_null_config(key, cast=cast, default=default)
    if value == "":
        raise Exception(f'{key} not allow empty value in .env')
    return value


def get_kwargs_or_dotenv(kwargs, key, key_dotenv=None, not_empty=False, not_null=False):
    getter = dict(
        not_empty=get_not_empty_config,
        not_null=get_not_null_config,
        simple=config
    ).get(
        'not_empty' if not_empty
        else 'not_null' if not_null
        else 'simple'
    )

    return kwargs.get(
        key,
        getter(key_dotenv if key_dotenv is not None else key)
    )
