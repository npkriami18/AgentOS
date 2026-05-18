import ast
from collections.abc import Awaitable, Callable
from pathlib import Path

from kernel.tools.base import BaseTool, ToolContext

SearchClient = Callable[[str], Awaitable[list[dict[str, str]]]]


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Safely evaluates arithmetic expressions."

    async def execute(self, context: ToolContext) -> float | int:
        expression = context.arguments.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("calculator requires a non-empty expression")

        tree = ast.parse(expression, mode="eval")
        return _evaluate_node(tree.body)


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Reads UTF-8 text files within a configured workspace root."

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()

    async def execute(self, context: ToolContext) -> str:
        relative_path = context.arguments.get("path")
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("file_reader requires a non-empty path")

        target = (self.base_path / relative_path).resolve()
        if self.base_path not in target.parents and target != self.base_path:
            raise PermissionError("file_reader path escapes the configured base path")
        if not target.is_file():
            raise FileNotFoundError(f"file_reader could not find file: {relative_path}")

        return target.read_text(encoding="utf-8")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Performs web search through an injected search client."

    def __init__(self, search_client: SearchClient) -> None:
        self.search_client = search_client

    async def execute(self, context: ToolContext) -> list[dict[str, str]]:
        query = context.arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("web_search requires a non-empty query")
        return await self.search_client(query)


def _evaluate_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value

    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        operator = node.op

        if isinstance(operator, ast.Add):
            return left + right
        if isinstance(operator, ast.Sub):
            return left - right
        if isinstance(operator, ast.Mult):
            return left * right
        if isinstance(operator, ast.Div):
            return left / right
        if isinstance(operator, ast.FloorDiv):
            return left // right
        if isinstance(operator, ast.Mod):
            return left % right
        if isinstance(operator, ast.Pow):
            return left**right

    if isinstance(node, ast.UnaryOp):
        operand = _evaluate_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand

    raise ValueError("calculator only supports arithmetic expressions")
