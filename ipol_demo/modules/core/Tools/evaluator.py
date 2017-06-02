import ast


class IPOLEvaluateError(Exception):
    """
    IPOLEvaluateError
    """
    pass


def evaluate(expression):
    """
    Evaluates a math expression
    """
    try:
        node = ast.parse(expression, mode='eval')
        if isinstance(node.body, ast.Num):
            return float(node.body.n)
        return _evaluate(node)
    except Exception:
        raise IPOLEvaluateError(expression)


def _evaluate(node):
    """
     Iterates the Abstract Syntax Tree
    """
    if isinstance(node, ast.Num):
        return float(node.n)

    if isinstance(node, ast.BinOp):
        return _operate(node.op, _evaluate(node.left), _evaluate(node.right))

    return _evaluate(node.body)


def _operate(operation, left, right):
    """
    Performs the operation
    """
    if isinstance(operation, ast.Add):
        return left + right
    elif isinstance(operation, ast.Sub):
        return left - right
    elif isinstance(operation, ast.Mult):
        return left * right
    elif isinstance(operation, ast.Div):
        return left / right
    elif isinstance(operation, ast.Pow):
        return left ** right
    elif isinstance(operation, ast.Mod):
        return left % right
    else:
        print "operation {} not supported".format(type(operation))
