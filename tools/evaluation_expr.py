from sqlalchemy import or_, and_, DATE, TIMESTAMP, DATETIME, not_
from sqlalchemy.sql.operators import ilike_op

from .types import check_types, fix_pattern, first, check_collection

precedence = {'+': 1, '*': 1}
_special_char = {*precedence.keys(), '(', ')'}


def shunting_yard(expr):
    # Diccionario para asociar la precedencia de los operadores

    # Colas de salida y operadores
    output_queue = []
    operator_stack = []

    token = ''

    # Recorrer la expresión
    for _iter in expr:
        # Si el token es un número, agregarlo a la cola de salida
        if _iter.isspace():
            continue
        if _iter not in _special_char:
            token += _iter
        else:
            if len(token) > 0:
                output_queue.append(token)
            token = _iter

            # Si el token es un operador
            if token in precedence:
                # Sacar de la pila todos los operadores con mayor o igual precedencia
                while (
                        operator_stack
                        and operator_stack[-1] != '('
                        and precedence[operator_stack[-1]] >= precedence[token]
                ):
                    output_queue.append(operator_stack.pop())
                # Agregar el operador a la pila
                operator_stack.append(token)
            # Si el token es un paréntesis izquierdo, agregarlo a la pila
            elif token == '(':
                operator_stack.append(token)
            # Si el token es un paréntesis derecho
            elif token == ')':
                # Sacar de la pila todos los operadores hasta encontrar el paréntesis izquierdo correspondiente
                while operator_stack and operator_stack[-1] != '(':
                    output_queue.append(operator_stack.pop())
                # Sacar el paréntesis izquierdo de la pila
                operator_stack.pop()
            else:
                raise ValueError(f"invalid token {token}")

            token = ''

    # Sacar de la pila todos los operadores restantes
    while operator_stack:
        item = operator_stack.pop()
        output_queue.append(item)

    return output_queue


def evaluate_postfix(postfix, table, filters, map_operators, operator):
    # Pila para almacenar los operandos
    operand_stack = []

    # Recorrer la expresión postfix
    for token in postfix:

        # Si el token es un operador conocido
        if token in precedence:

            # Sacar los dos últimos operandos de la pila y sumarlos
            op1 = operand_stack.pop()
            op2 = operand_stack.pop()

            left_operator = get_sql_operator(
                filters.pop(op1),
                map_operators,
                op1,
                table,
                operator
            ) if check_types(op1, str) else op1
            right_operator = get_sql_operator(
                filters.pop(op2),
                map_operators,
                op2,
                table,
                operator
            ) if check_types(op2, str) else op2

            if token == '+':
                result = or_(left_operator, right_operator)
            elif token == '*':
                result = and_(left_operator, right_operator)
            else:
                raise ValueError(f"operation not found {token}")

            # Agregar el resultado a la pila
            operand_stack.append(result)
        else:
            # Si el token es un número, agregarlo a la pila
            operand_stack.append(token)

    # El resultado final debe estar en la cima de la pila
    return operand_stack.pop()


def get_sql_operator(params, map_operators, col_name, table, operator):
    col = getattr(table.selected_columns, col_name, None)

    if col is None:

        __pre_filter = None
        __not = "__not"
        if col_name.endswith(__not):
            col_name = col_name[:-len(__not)]
            __pre_filter = not_

        op = first(
            op
            for op in map_operators.keys()
            if col_name.endswith(op)
        )
        _new_filter = map_operators.get(op)(table, col_name, params)
        new_filter = _new_filter if __pre_filter is None else __pre_filter(_new_filter)
    else:
        if isinstance(params, dict):
            if col.type.python_type is dict:
                filters_ = None
                for key, value in params.items():
                    if (_like := '__like') and key.endswith(_like):
                        like_ = col[key[:-len(_like)]].astext
                        new_filter = fix_ilike_operation(like_, value)
                    else:
                        new_filter = col[key].astext == value
                    filters_ = new_filter if filters_ is None else operator(
                        new_filter,
                        filters_
                    )
                new_filter = filters_
            else:
                raise ValueError("NOT IMPLEMENTD JSON")
        else:
            new_filter = basic_filter(col, params)

    return new_filter


def fix_ilike_operation(like_, value):
    if check_collection(value):
        new_filter = or_(*(
            ilike_op(
                like_,
                fix_pattern(sub_value)
            ) for sub_value in value
        ))
    else:
        new_filter = ilike_op(
            like_,
            fix_pattern(value)
        )
    return new_filter


def basic_filter(col, params):
    if check_collection(params):
        new_filter = col.in_(params)
    else:
        if (params == '' or params is None) and check_types(col.type, TIMESTAMP, DATE, DATETIME):
            new_filter = col.is_(None)
        else:
            new_filter = col == params
    return new_filter
