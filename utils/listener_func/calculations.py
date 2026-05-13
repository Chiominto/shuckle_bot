import ast
import operator
import re

import discord

from constants.celestial_constants import CELESTIAL_SERVER_ID


def parse_number(s):
    s = s.lower().replace(",", "").strip()
    match = re.match(r"^(\d*\.?\d+)([km]?)$", s)
    if not match:
        raise ValueError("Invalid number format")
    num, suffix = match.groups()
    num = float(num)
    if suffix == "k":
        num *= 1_000
    elif suffix == "m":
        num *= 1_000_000
    return num


def parse_expression(expr):
    # Replace suffixes with their numeric values
    def repl(m):
        return str(parse_number(m.group()))

    # Improved regex: match numbers with k/m suffix, not part of a larger word
    expr = re.sub(r"(?<![\w.])(\d*\.?\d+[km])(?![\w])", repl, expr)
    # Also match plain numbers (no suffix)
    expr = re.sub(r"(?<![\w.])(\d*\.?\d+)(?![\w])", repl, expr)

    allowed_binops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    allowed_unaryops = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_binops:
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Pow):
                if not isinstance(right, (int, float)) or right != int(right):
                    raise ValueError("Exponent must be an integer")
                if abs(int(right)) > 1000:
                    raise ValueError("Exponent too large")
            return allowed_binops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unaryops:
            return allowed_unaryops[type(node.op)](eval_node(node.operand))
        raise ValueError("Unsupported expression")

    tree = ast.parse(expr, mode="eval")
    return eval_node(tree)


def is_valid_math_equation(expr):
    try:
        parse_expression(expr)
        return True
    except Exception:
        return False


async def computation_listener(message: discord.Message) -> None:
    """
    Listens for messages that contain mathematical expressions and replies with the computed result.
    """
    # Only process messages in the Infusion server
    if message.guild and message.guild.id != CELESTIAL_SERVER_ID:
        return

    # Ignore bot messages
    if message.author.bot:
        return

    content = message.content.strip()
    if content.lower().startswith("cal"):
        content = content[3:].strip()

    if not content:
        return

    # Only process if the message contains only digits, math symbols (+, -, *, /), parentheses, periods, spaces, and commas
    # If it contains any letters, ignore it
    if re.search(r"[a-zA-Z]", content):
        return

    # Only process if it contains at least one math symbol (+, -, *, /)
    if not re.search(r"[+\-*/]", content):
        return

    # Check if the entire message is a valid math expression
    if is_valid_math_equation(content):
        try:
            result = parse_expression(content)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            reply = f"🤖 The result is: `{result:,}`"
            await message.reply(reply, mention_author=False)
        except Exception:
            pass  # In case of any error, do nothing
