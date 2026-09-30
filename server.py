from mcp.server import MCPServer

mcp = MCPServer("Calculator MCP Server")


@mcp.tool()
def add_numbers(number1: int, number2: int) -> int:
    """Add two integer numbers."""
    return number1 + number2


@mcp.tool()
def subtract_numbers(number1: int, number2: int) -> int:
    """Subtract the second number from the first number."""
    return number1 - number2


@mcp.tool()
def greet_user(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}! Welcome to MCP testing."