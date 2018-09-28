"""
IPOL Evaluator wrapper
"""

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
        node = ast.parse(str(expression), mode='eval')
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
    elif isinstance(node, ast.BinOp):
        return _operate(node.op, _evaluate(node.left), _evaluate(node.right))
    elif isinstance(node, ast.UnaryOp):
        return _unary_operate(node.op, _evaluate(node.operand))
    
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
        raise IPOLEvaluateError("Binary operation {} not supported".format(type(operation)))

def _unary_operate(operation, operand):
    """
    Performs the unary operation
    """
    if isinstance(operation, ast.UAdd):
        return + operand
    elif isinstance(operation, ast.USub):
        return - operand
    else:
        raise IPOLEvaluateError("Unary operation {} not supported".format(type(operation)))
