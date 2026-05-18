from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolContext:
    agent_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(self, context: ToolContext) -> Any:
        """Run the tool with validated context."""
