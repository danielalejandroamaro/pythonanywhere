import re

from fastapi import Request

from tools import get_query_params
from tools.types import (
    get_first_if_collection_of_one,
    check_collection,
    check_types
)
from .tools import BuilderReservedParams as r_params


def stack(_filter_obj: dict, keys, filter_value, overwrite=False):
    _filter_obj = {} if _filter_obj is None else _filter_obj

    key_path = keys.split('.') if check_types(keys, str) else keys
    root_key = key_path.pop(0)
    _value = _filter_obj.pop(root_key, None)

    if len(key_path) == 0:
        if _value is None or overwrite:
            return {
                **_filter_obj,
                root_key: filter_value
            }
        else:
            if not check_types(filter_value, list):
                filter_value = [filter_value]
            if not check_types(_value, list):
                _value = [_value]

            return {
                **_filter_obj,
                root_key: [
                    *_value, *filter_value
                ]
            }

    return {
        **_filter_obj,
        root_key: stack(
            _value, key_path, filter_value
        )
    }


class ApiQueryParamsBase:

    # region properties ...

    @property
    def scope_user(self):
        return self.__scope_user

    @property
    def filters(self):
        return {
            k: v
            for k, v in self.__filters.items()
            if (
                    not isinstance(v, dict)  # esto es para las agregaciones de los complex_filters
                    and not k.startswith('agg__')  # esto es para las agregaciones de los groupby
            )
        }

    @property
    def agg_filters(self):
        return {
            re.sub('^agg__', '', k): v
            for k, v in self.__filters.items()
            if k.startswith('agg__')
        }

    @property
    def complex_filters(self):
        return {
            k: v
            for k, v in self.__filters.items()
            if isinstance(v, dict)
        }

    @property
    def params(self):
        return self.__query_params

    # endregion properties ...

    def __init__(self):
        self.__filters = {
            # aqui agregamos filtros por defecto si algún dia los necesitamos
        }
        self.__scope_user = {
            # aqui agregamos filtros de scope
        }

        self.__query_params = {

        }

    # region methods ...

    def __load_init(self, _qp):
        _limit = r_params.LIMIT

        limit = get_query_params(
            _limit, _qp, int,
            ['', lambda x: x < 0],
            -1,
            flat=True
        )
        if limit is None:
            return  # if not limit, return
        if limit == 0:
            self.__query_params.update({
                _limit: 0
            })
            return

        _offset = r_params.OFFSET
        _page = r_params.PAGE

        offset = get_query_params(
            _offset, _qp, int,
            ['', lambda x: x < 0],
            0, flat=True
        )

        self.__query_params.update({
            _limit: limit,
            _offset: offset
        })

        page = get_query_params(
            _page, _qp, int, ['', lambda x: x <= 0]
        )

        if page and len(page):
            self.__query_params.update({
                _offset: (page[_page] - 1) * limit,
            })

    def add_scope(self, params, overwrite=True):
        for key in (qParams := params).keys():
            if isinstance(qParams, dict):
                rl = v if check_collection(v := qParams[key]) else [v]
            else:
                rl = qParams.getlist(key)
            filter_value = get_first_if_collection_of_one(rl)

            self.__scope_user = stack(
                self.__scope_user,
                key,
                filter_value,
                overwrite
            )

    def add_filters(self, params, overwrite=True):
        self.__load_init(params)

        for key in (qParams := params).keys():
            if isinstance(qParams, dict):
                rl = v if check_collection(v := qParams[key]) else [v]
            else:
                rl = qParams.getlist(key)
            filter_value = get_first_if_collection_of_one(rl)

            if key in self.PROCESS_ON_INIT:
                continue
            if key in self.RESERVED_PARAMS:
                # en algunos casos es comodo siempre tratarlo como lista
                if key in self.ALLWAYS_COLLECION:
                    base = self.__query_params.get(key, [])
                    self.__query_params[key] = [*base, *rl]
                else:
                    base = self.__query_params.get(key, None)
                    if base is None:
                        self.__query_params[key] = filter_value
                    elif check_collection(base):
                        if check_collection(filter_value):
                            self.__query_params[key] = [*base, *filter_value]
                        else:
                            self.__query_params[key] = [*base, filter_value]
                    else:
                        if check_collection(filter_value):
                            self.__query_params[key] = [base, *filter_value]
                        else:
                            self.__query_params[key] = [base, filter_value]
                continue

            self.__filters = stack(
                self.__filters,
                key,
                filter_value,
                overwrite
            )
        return self

    def get(self, param, _default=None):
        from_filter = self.__filters.get(param, _default)
        return self.__query_params.get(param, from_filter)

    def pop(self, param, _default=None):
        from_filter = self.__filters.pop(param, _default)
        return self.__query_params.pop(param, from_filter)

    # endregion methods ...

    # region attributes ....

    PROCESS_ON_INIT = [
        r_params.OFFSET,  # ✅ DONE
        r_params.PAGE,  # ✅ DONE
        r_params.LIMIT,  # ✅ DONE
    ]

    RESERVED_PARAMS = {
        r_params.LIKE,  # ✅ DONE
        r_params.LIKE_COLS,  # ✅ DONE
        r_params.VALUES_LIST,  # ✅ DONE
        r_params.GROUPBY,  # ✅ DONE
        r_params.DISTINCT,  # ✅ DONE
        r_params.ORDERBY,  # ✅ DONE
        r_params.FORMAT,  # ✅ DONE ['xlsx','csv']
        r_params.EXTEND,  # ✅ DONE
        r_params.NESTED,  # ✅ DONE
        r_params.NESTED_HOW,  # ✅ DONE
        r_params.EXTEND_HOW,  # ✅ DONE
        r_params.DEFAULT_SQL_OPERATORS  # 🟧 trying
    }

    ALLWAYS_COLLECION = {
        r_params.VALUES_LIST,
        r_params.GROUPBY,
        r_params.EXTEND,
        r_params.NESTED,
        r_params.LIKE_COLS,
        r_params.ORDERBY,
        r_params.NESTED_HOW,
        r_params.EXTEND_HOW
    }

    # endregion attributes ....


class ApiQueryParams(ApiQueryParamsBase):

    # region properties ...
    @property
    def method(self):
        return self.request.method

    @property
    async def obj(self):
        return await self.request.json()

    # endregion properties ...

    def __init__(self,
                 request: Request,
                 params_source=None,

                 ):
        # [ID0001 paso 3]
        # agrega un valor por defecto en caso de que no venga en la consulta
        super().__init__()
        self.request = request
        qp = request.query_params

        if params_source:
            self.add_filters(params_source)

        self.add_filters(qp)
