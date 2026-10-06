"""Bounded arithmetic and unit conversion; no code evaluation."""
import ast
import math
import operator
import re

UNITS = {
    "m": ("length", 1, 0), "km": ("length", 1000, 0), "cm": ("length", .01, 0),
    "mm": ("length", .001, 0), "mi": ("length", 1609.344, 0), "mile": ("length", 1609.344, 0),
    "miles": ("length", 1609.344, 0), "ft": ("length", .3048, 0), "in": ("length", .0254, 0),
    "kg": ("mass", 1, 0), "g": ("mass", .001, 0), "lb": ("mass", .45359237, 0),
    "oz": ("mass", .028349523125, 0), "s": ("time", 1, 0), "min": ("time", 60, 0),
    "h": ("time", 3600, 0), "l": ("volume", 1, 0), "ml": ("volume", .001, 0),
    "c": ("temperature", 1, 273.15), "f": ("temperature", 5/9, 255.3722222222222),
    "k": ("temperature", 1, 0),
}


def calculate(expression: str):
    """Bounded arithmetic AST; no eval, calls, variables or exponentiation."""
    if len(expression) > 150:
        raise ValueError("Expression is too long")
    tree = ast.parse(expression.strip(), mode="eval")
    if len(list(ast.walk(tree))) > 60:
        raise ValueError("Expression is too complex")
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                  ast.Div: operator.truediv, ast.Mod: operator.mod}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            result = float(node.value)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            result = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in operations:
            result = operations[type(node.op)](visit(node.left), visit(node.right))
        else:
            raise ValueError("Use numbers and + - * / % only")
        if not math.isfinite(result) or abs(result) > 1e100:
            raise ValueError("Result is outside the supported range")
        return result
    return visit(tree.body)


def conversion(query: str):
    match = re.fullmatch(r"\s*([-+]?\d+(?:\.\d+)?)\s*([a-z]+)\s+(?:to|in)\s+([a-z]+)\s*", query.lower())
    if not match:
        return None
    value, source, destination = match.groups()
    if source not in UNITS or destination not in UNITS:
        raise ValueError("Unknown unit")
    first, second = UNITS[source], UNITS[destination]
    if first[0] != second[0]:
        raise ValueError("Choose units of the same kind")
    result = (float(value) * first[1] + first[2] - second[2]) / second[1]
    if not math.isfinite(result) or abs(result) > 1e100:
        raise ValueError("Result is outside the supported range")
    return f"{result:.10g} {destination}"

