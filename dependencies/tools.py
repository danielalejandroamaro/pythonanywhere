class BuilderReservedParams:
    LIMIT = 'limit'
    OFFSET = 'offset'
    PAGE = 'page'
    LIKE = 'like'
    LIKE_COLS = 'like_cols'
    VALUES_LIST = 'values_list'
    DISTINCT = 'distinct'
    ORDERBY = 'order_by'
    GROUPBY = 'group_by'
    FORMAT = 'format'
    EXTEND = 'extend'
    DEFAULT_SQL_OPERATORS = '_operator_'
    NESTED = 'nested'  # este comando se usa para traer de otra tabla todos los elementos que tengan un foreing key
    EXTEND_HOW = 'extend_how'
    NESTED_HOW = 'nested_how'

    USING_PANDAS = 'using_pandas'


class joinType:
    INNER = 'inner'
    LEFT = 'left'
    OUTER = 'outer'
