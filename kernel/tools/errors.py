class ToolError(Exception):
    """Base tool-system error."""


class ToolNotFoundError(ToolError):
    """Raised when a tool is not registered."""


class ToolPermissionError(ToolError):
    """Raised when an agent is not allowed to use a tool."""


class ToolRateLimitError(ToolError):
    """Raised when a tool exceeds its allowed call rate."""
