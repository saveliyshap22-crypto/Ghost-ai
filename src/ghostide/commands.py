from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


CommandHandler = Callable[[list[str], "CommandContext"], int]


@dataclass(slots=True)
class Command:
    name: str
    help: str
    handler: CommandHandler
    aliases: tuple[str, ...] = ()


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        keys = (command.name, *command.aliases)
        for key in keys:
            self._commands[key] = command

    def resolve(self, name: str) -> Command | None:
        return self._commands.get(name.lstrip("/"))

    def names(self) -> list[str]:
        return sorted({command.name for command in self._commands.values()})

    def help_text(self) -> str:
        commands = sorted({cmd.name: cmd for cmd in self._commands.values()}.values(), key=lambda c: c.name)
        width = max((len(c.name) for c in commands), default=4)
        return "\n".join(f"/{cmd.name:<{width}}  {cmd.help}" for cmd in commands)


class CommandContext:  # pragma: no cover - protocol-like runtime container
    pass

