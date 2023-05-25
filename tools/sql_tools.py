from sqlalchemy.dialects import mysql
from sqlalchemy.sql import functions, selectable
from sqlalchemy.sql.expression import (
    and_,
    select,
    or_,
    desc,
    asc
)

from database import get_table, rows2dict
from engine import set_connection
from .const import (joinType, BuilderReservedParams as r_params)
from .evaluation_expr import shunting_yard, evaluate_postfix, get_sql_operator, fix_ilike_operation
from .types import (
    check_collection,
    first,
    list_to_dict,
    check_types,
    get_obj_name,
    convert_to_valid_boolean,
    full
)


class NotFoundError(Exception):
    pass


def pprint(items):
    return items.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})


TABLE_HIT = {}


class Query:
    __query: selectable

    def __init__(
            self,
            table,
            filters=None,
            complex_filters=None,
            params=None,
            agg_filters=None,
            scope_user=None,
    ):
        filters = filters or {}
        scope_user = scope_user or {}
        agg_filters = agg_filters or {}
        self.params = params or {}
        complex_filters = complex_filters or {}

        _operator = self.params.get(
            r_params.DEFAULT_SQL_OPERATORS,
            'and'
        )

        _table = table
        if len(scope_user) > 0:
            table = select(
                table,
                create_where_stmt(
                    table,
                    scope_user,
                    operator='or')
            )

        cols_to_return = table.c

        tables_name = self.params.get(r_params.EXTEND, [])
        tables_name = list_to_dict(tables_name)
        _exist_filters = {
            k: v
            for k, v in filters.items() if
            k.endswith('__isnull') and (
                col_name := k[:-len('__isnull')]
            ) in tables_name and not hasattr(
                table.c, col_name
            )
        }
        cols_name = self.params.get(r_params.NESTED)

        root_table_filter = {
            **{
                k: v
                for k, v in filters.items() if k not in _exist_filters
            },
            **{
                k: v
                for k, v in filters.items() if k in table.c
            }
        }

        if len(root_table_filter) > 0:
            table = select(
                table,
                create_where_stmt(
                    table,
                    root_table_filter,
                    operator=_operator
                )
            )
            cols_to_return = table.c

        extend_how = self.params.get(r_params.EXTEND_HOW, [])
        nested_how = self.params.get(r_params.NESTED_HOW, [])

        if tables_name or cols_name:
            if len(tables_name) > 0:  # extend
                isouter = not (joinType.INNER in extend_how)
                _full = 'full' in extend_how
                # tables_name = list_to_dict(tables_name)
                # TODO todavia no se puede extender a si mismo
                tables = [
                    get_table(table_name) for table_name in tables_name.keys()
                ]
                for _rigth_table, table_name in zip(tables, tables_name.keys()):
                    _isouter = isouter
                    if _rigth_table is None:
                        _rigth_table = first(_table.c.get(table_name).foreign_keys).column.table
                        left_cols = [_table.c.get(table_name)]
                        rigth_col = first(_rigth_table.primary_key)
                    else:
                        left_cols, rigth_col = get_cols_join(_table, _rigth_table)
                    for index, left_col in enumerate(left_cols):
                        rigth_table = select(_rigth_table)
                        if _filter := complex_filters.get(table_name):
                            rigth_table = rigth_table.where(
                                create_where_stmt(rigth_table, _filter, operator=_operator)
                            )
                            _isouter = False
                        if _filter := complex_filters.get(left_col.key):
                            rigth_table = rigth_table.where(
                                create_where_stmt(rigth_table, _filter, operator=_operator)
                            )
                            _isouter = False

                        sub_q = rigth_table.subquery(name=f'{left_col.key}_sub')
                        cols = tables_name[table_name]
                        if cols == '*':
                            cols = [*sub_q.c]
                        else:
                            cols = [getattr(sub_q.c, col) for col in cols]

                        new_cols = [
                            col.label(f'{left_col.key}.{col.key}')
                            if len(left_cols) > 1
                            else col.label(f'{table_name}.{col.key}')
                            for col in cols
                        ]
                        k_subq = first(
                            col for col in sub_q.c if rigth_col.key == col.key
                        )
                        onclause = first(
                            col for col in table.c if left_col.key == col.key
                        ) == k_subq
                        _where = []
                        if _exist := _exist_filters.get(f'{table_name}__isnull', None):
                            _where = [k_subq.is_(None)
                                      if convert_to_valid_boolean(_exist)
                                      else k_subq.isnot(None)]
                        table = select(
                            *table.c,
                            *new_cols,
                            *_where
                        ).join_from(
                            table,
                            sub_q,
                            onclause=onclause,
                            isouter=_isouter,
                            full=_full
                        )

                    cols_to_return = table.c

            if cols_name:
                cols = {
                    col_name: getattr(_table.c, col_name)
                    for col_name in cols_name
                    if hasattr(_table.c, col_name)
                }
                isouter = not (joinType.INNER in nested_how)
                _full = 'full' in nested_how
                for col_name, col in cols.items():
                    _isouter = isouter
                    if len(fkeys := col.foreign_keys) == 0:
                        continue  # implicit foreign

                    _rigth_table = first(fkeys).column.table
                    new_col_name = get_obj_name(col_name, col)
                    rigth_table = select(_rigth_table)
                    if _filter := complex_filters.get(new_col_name):
                        rigth_table = rigth_table.where(
                            create_where_stmt(rigth_table, _filter, operator=_operator)
                        )
                        _isouter = False
                    sub_q = rigth_table.subquery(f'{col_name}_sub')

                    new_cols = [
                        col.label(f'{col_name}.{col.key}')
                        for col in sub_q.c
                    ]
                    onclause = getattr(table.c, col_name) == first(
                        col for col in sub_q.c
                        if col.key == first(_rigth_table.primary_key).key
                    )
                    # esto es importante porque el join se hace sobre table no sobre la tabla original

                    table = select(
                        [*table.c, *new_cols]
                    ).join_from(
                        table,
                        sub_q,
                        onclause,
                        isouter=_isouter,
                        full=_full
                    )

                    cols_to_return = table.c  # !!! ❌ important
                    # estas filas no van en el return,
                    # pero se capturan más aldelate por eso no se pueden quitar

        cols_to_return = {
            str(col.key): col for col in cols_to_return
        }

        if values_list := self.params.get(r_params.VALUES_LIST):
            cols_to_return = {
                k: cols_to_return[k] for k in values_list
            }

        items = select(*cols_to_return.values())

        _like = self.params.get(r_params.LIKE)
        _like_cols = self.params.get(r_params.LIKE_COLS)

        if _like and _like_cols:
            items = items.where(
                fix_ilike_operation(
                    functions.concat(
                        *[cols_to_return[k] for k in _like_cols]
                    ),
                    _like
                )
            )
        elif _like or _like_cols:
            raise Exception("")

        _groupby_columns = self.params.get(r_params.GROUPBY)
        if _groupby_columns and len(agg_filters):
            cols_to_return = {str(col.key): col for col in items.c}
            cols = [cols_to_return[k] for k in _groupby_columns]
            agg_cols = []
            for k, v in agg_filters.items():
                if check_collection(v):
                    for _v in v:
                        agg_cols.append(
                            getattr(functions, _v)(
                                cols_to_return[k]
                            ).label(f'{k}__{_v}')
                        )
                elif check_types(v, dict):
                    for sub_k, operator in v.items():
                        agg_cols.append(
                            getattr(functions, operator)(
                                cols_to_return[f"{k}.{sub_k}"]
                            ).label(f'{k}.{sub_k}__{operator}')
                        )
                else:
                    agg_cols.append(
                        getattr(functions, v)(
                            cols_to_return[k]
                        ).label(f'{k}__{v}')
                    )
            items = select(
                *cols, *agg_cols
            ).group_by(
                *cols
            )

        elif _groupby_columns or len(agg_filters):
            raise Exception("")

        _orders_by = self.params.get(r_params.ORDERBY)
        if _orders_by:
            items = items.order_by(*[
                desc(col[1:]) if col.startswith('-') else asc(col)
                for col in _orders_by
            ])

        if self.params.get(r_params.DISTINCT):
            items = items.distinct()

        self.__query = items

    @set_connection
    def run(self, conn=None):
        cols = self.__query.c
        r = conn.execute(self.__query)
        result = rows2dict(r)

        if cols_name := self.params.get(r_params.NESTED):
            cols_name = list_to_dict(cols_name)
            for col_name in cols_name.keys():
                cols = [c for c in cols if not c.key.startswith(f'{col_name}.')]
                new_result = []
                col = getattr(self.table.c, col_name, None)
                new_col_name = get_obj_name(col_name, col)
                if not (col is None):
                    if len(col.foreign_keys):  # ¡esto es para cuando hay foreign_keys!!!
                        new_result = [
                            stack(row, col.key, new_col_name) for row in result
                        ]
                    else:
                        # TODO: hacer usando la tabla secure_table
                        pass
                    result = new_result
                elif col_name in Engine.get_engine().table_names():
                    sub_table = get_table(col_name)
                    col_in_sub_table = first(
                        filter(
                            lambda _col_sub_table: _col_sub_table.column.table == self.table or any(
                                filter(
                                    lambda _col_pk_table: _col_pk_table.column is _col_sub_table.column,
                                    first(self.table.primary_key.columns).foreign_keys
                                )
                            ),
                            sub_table.foreign_keys
                        )
                    ).parent
                    col_name_in_sub_table = col_in_sub_table.key
                    # col = getattr(sub_table.c, col_name_in_sub_table)
                    table_pk_col = first(self.table.primary_key)
                    ids_to_find = [*set([r[table_pk_col.key] for r in result])]

                    # aqui hay que agregar los complex_filters
                    # sub_stmt = sub_table.select(col.in_(ids_to_find))
                    add_key = False
                    if cols_name[col_name] == '*':
                        params = {}
                    else:
                        values_list = set(cols_name[col_name])
                        values_list.add(col_name_in_sub_table)
                        add_key = len(values_list) != len(cols_name[col_name])
                        values_list = list(values_list)

                        params = {
                            r_params.VALUES_LIST: values_list
                        }
                    sub_stmt = create_select_query(
                        sub_table,
                        filters={
                            col_name_in_sub_table: ids_to_find,
                            **self.__complex_filters.get(col_name, {})
                        },
                        params=params
                    )

                    _result = [*conn.execute(sub_stmt)]
                    all_sub_results = {}
                    for row in _result:
                        _key = row[col_name_in_sub_table]
                        _value = all_sub_results.get(_key, [])
                        _item = {**row}
                        if add_key:
                            _item.pop(col_name_in_sub_table)

                        _value.append(_item)
                        all_sub_results[_key] = _value

                    result = [
                        {
                            **row,
                            new_col_name: all_sub_results.get(row[table_pk_col.key], [])
                        } for row in result
                    ]

        return result


def get_cols_join(left, rigth):
    if left is rigth:
        _rigth = full(
            (
                col
                for col in rigth.c
                if any(_col.column.table is left
                       for _col in col.foreign_keys)
            ), raise_on_empty=False
        )
        if len(_rigth) > 0:
            return [first(left.primary_key)], _rigth[0]

    left_cols = full(
        (
            col
            for col in left.c
            if any(_col.column.table is rigth
                   for _col in col.foreign_keys)
        ), raise_on_empty=False
    )
    rigth_col = first(
        rigth.primary_key
    )
    if len(left_cols) == 0:
        left_cols = [first(left.primary_key)]
        rigth_col = first(
            (col for col in rigth.c if any(
                _col.column.table is left for _col in col.foreign_keys
            )), raise_on_empty=False
        )
        if rigth_col is None:
            rigth_col = first(
                rigth.primary_key
            )
            col_index = go_in_deep([*left.c], rigth_col)
            if col_index < 0:
                raise ValueError
            return [[*left.c][col_index]], rigth_col

    return left_cols, rigth_col


def go_in_deep(lefts, right):
    while not (right is None):
        _lefts = lefts
        while any(not (c is None) for c in _lefts):
            for index, c in enumerate(_lefts):
                if c is None:
                    continue
                f_key = first(c.foreign_keys, False)
                if f_key is None:
                    continue
                if f_key.column.table is right.table:
                    return index
            f_keys_lefts = [None if c is None else first(c.foreign_keys, False) for c in _lefts]
            _lefts = [None if c is None else c.column for c in f_keys_lefts]
        f_key_right = first(right.foreign_keys, False)
        if f_key_right is None:
            break
        right = f_key_right.column
    return -1


def get_op(operator_pofix):
    def decorator(fn):
        def _fn(table, col_with_filter, value):
            col_name = col_with_filter[:-len(operator_pofix)]
            attr = table.selected_columns if hasattr(table, "selected_columns") else table.c
            col = getattr(attr, col_name)
            return fn(table, col, value)

        return {
            operator_pofix: _fn
        }

    return decorator


map_operators = {
    **get_op('__gt')(lambda table, col, value: col > value),
    **get_op('__gte')(lambda table, col, value: col >= value),
    **get_op('__lt')(lambda table, col, value: col < value),
    **get_op('__lte')(lambda table, col, value: col <= value),
    **get_op('__like')(
        lambda table, col, value:
        fix_ilike_operation(
            col,
            value
        )
    ),
    **get_op('__isnull')(
        lambda table, col, value:
        col.is_(None)
        if convert_to_valid_boolean(value)
        else col.isnot(None)
    ),
}


def create_where_stmt(table, filters, filters_=None, operator=None):
    _filters = {**filters}
    if check_types(operator, str) and operator not in ['and', 'or']:
        postfix = shunting_yard(operator)
        new_filter = evaluate_postfix(
            postfix,
            table,
            _filters,
            map_operators,
            and_
        )
        filters_ = new_filter if filters_ is None else operator(
            new_filter,
            filters_
        )

        filters = _filters
        operator = 'and'

    if operator == 'and':
        operator = and_
    elif operator == 'or':
        operator = or_
    else:
        raise ValueError(f"invalid operator {operator}")

    for col_name, params in filters.items():
        new_filter = get_sql_operator(
            params,
            map_operators,
            col_name,
            table,
            operator
        )

        filters_ = new_filter if filters_ is None else operator(
            new_filter,
            filters_
        )
    return filters_
