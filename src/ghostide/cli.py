from __future__ import annotations

import logging
import shlex
from dataclasses import dataclass
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter, WordCompleter, merge_completers
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer

from .ai import LocalAIAssistant
from .commands import Command, CommandRegistry
from .config import AppConfig, HISTORY_PATH
from .files import safe_path, tree
from .logging_utils import configure_logging
from .plugins import load_plugins
from .scaffold import available_templates, build_project
from .search import SearchEngine
from .terminal import run_shell


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeContext:
    registry: CommandRegistry
    config: AppConfig
    project_root: Path
    ai: LocalAIAssistant
    search: SearchEngine
    should_exit: bool = False


class GhostCompleter(Completer):
    def __init__(self, registry: CommandRegistry, project_root: Path) -> None:
        self.registry = registry
        self.project_root = project_root

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            yield from WordCompleter([f"/{name}" for name in self.registry.names()], ignore_case=True).get_completions(
                document, complete_event
            )
            return
        yield from PathCompleter(expanduser=True).get_completions(document, complete_event)


class GhostIDE:
    def __init__(self, project_root: Path | None = None) -> None:
        configure_logging()
        self.config = AppConfig.load()
        root = project_root or Path(self.config.active_project or Path.cwd()).expanduser().resolve()
        self.registry = CommandRegistry()
        self.context = RuntimeContext(
            registry=self.registry,
            config=self.config,
            project_root=root,
            ai=LocalAIAssistant(),
            search=SearchEngine(),
        )
        self._register_builtin_commands()
        loaded = load_plugins(self.registry, root)
        if loaded:
            LOGGER.info("loaded plugins: %s", loaded)

    def run(self) -> int:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        bindings = KeyBindings()

        @bindings.add("c-q")
        def _(event) -> None:
            event.app.exit(result="/exit")

        session = PromptSession(
            history=FileHistory(str(HISTORY_PATH)),
            completer=GhostCompleter(self.registry, self.context.project_root),
            lexer=PygmentsLexer(BashLexer),
            key_bindings=bindings,
            complete_while_typing=True,
        )
        print("Ghost IDE — type /help, /exit or Ctrl-Q. Shell commands run directly.")
        while not self.context.should_exit:
            try:
                raw = session.prompt(HTML(f"<ansicyan>{self.context.project_root.name}</ansicyan> › "))
            except (KeyboardInterrupt, EOFError):
                print()
                break
            self.execute(raw)
        self.config.save()
        return 0

    def execute(self, raw: str) -> int:
        raw = raw.strip()
        if not raw:
            return 0
        LOGGER.info("command: %s", raw)
        if raw.startswith("/"):
            return self._execute_slash(raw)
        return run_shell(raw, self.context.project_root)

    def _execute_slash(self, raw: str) -> int:
        try:
            tokens = shlex.split(raw)
        except ValueError as exc:
            print(f"Parse error: {exc}")
            return 2
        if not tokens:
            return 0
        command = self.registry.resolve(tokens[0])
        if command is None:
            print(f"Unknown command: {tokens[0]}. Type /help.")
            return 1
        return command.handler(tokens[1:], self.context)

    def _register_builtin_commands(self) -> None:
        self.registry.register(Command("help", "Show command help.", self._cmd_help, aliases=("?",)))
        self.registry.register(Command("exit", "Exit Ghost IDE.", self._cmd_exit, aliases=("quit",)))
        self.registry.register(Command("ai", "Ask the local offline AI assistant: /ai <question>.", self._cmd_ai))
        self.registry.register(Command("search", "Search project files and GitHub: /search <query>.", self._cmd_search))
        self.registry.register(Command("build", "Scaffold a project: /build <web|cli|library|api> [name].", self._cmd_build))
        self.registry.register(Command("files", "Show project file tree: /files [depth].", self._cmd_files))
        self.registry.register(Command("open", "Print a file with syntax highlighting: /open <path>.", self._cmd_open))
        self.registry.register(Command("projects", "List, add, or switch projects.", self._cmd_projects))
        self.registry.register(Command("cd", "Change active project directory: /cd <path>.", self._cmd_cd))

    def _cmd_help(self, args: list[str], ctx: RuntimeContext) -> int:
        print(ctx.registry.help_text())
        print("\nCustom commands: put Python plugins in ~/.ghostide/plugins or .ghostide/plugins with setup(registry).")
        return 0

    def _cmd_exit(self, args: list[str], ctx: RuntimeContext) -> int:
        ctx.should_exit = True
        return 0

    def _cmd_ai(self, args: list[str], ctx: RuntimeContext) -> int:
        if not args:
            print("Usage: /ai <question>")
            return 2
        print(ctx.ai.ask(" ".join(args), ctx.project_root))
        return 0

    def _cmd_search(self, args: list[str], ctx: RuntimeContext) -> int:
        if not args:
            print("Usage: /search <query>")
            return 2
        results = ctx.search.search(" ".join(args), ctx.project_root)
        if not results:
            print("No results.")
            return 0
        for result in results:
            print(f"[{result.source}] {result.title}\n  {result.detail}")
        return 0

    def _cmd_build(self, args: list[str], ctx: RuntimeContext) -> int:
        if not args:
            print(f"Usage: /build <{'|'.join(available_templates())}> [name]")
            return 2
        kind = args[0]
        name = args[1] if len(args) > 1 else f"ghost-{kind}-app"
        try:
            created = build_project(kind, name, ctx.project_root)
        except Exception as exc:
            print(f"Build failed: {exc}")
            return 1
        print(f"Created {ctx.project_root / name}")
        for path in created:
            print(f"  {path.relative_to(ctx.project_root / name)}")
        return 0

    def _cmd_files(self, args: list[str], ctx: RuntimeContext) -> int:
        depth = int(args[0]) if args else 3
        print(tree(ctx.project_root, depth))
        return 0

    def _cmd_open(self, args: list[str], ctx: RuntimeContext) -> int:
        if not args:
            print("Usage: /open <path>")
            return 2
        try:
            path = safe_path(ctx.project_root, args[0])
            print(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception as exc:
            print(f"Open failed: {exc}")
            return 1
        return 0

    def _cmd_projects(self, args: list[str], ctx: RuntimeContext) -> int:
        if not args or args[0] == "list":
            for project in ctx.config.projects:
                marker = "*" if project == str(ctx.project_root) else " "
                print(f"{marker} {project}")
            return 0
        if args[0] == "add":
            path = Path(args[1] if len(args) > 1 else ".").expanduser().resolve()
            if str(path) not in ctx.config.projects:
                ctx.config.projects.append(str(path))
            ctx.config.active_project = str(path)
            ctx.project_root = path
            ctx.config.save()
            print(f"Added and switched to {path}")
            return 0
        if args[0] == "switch" and len(args) > 1:
            path = Path(args[1]).expanduser().resolve()
            if not path.exists():
                print(f"Project does not exist: {path}")
                return 1
            ctx.project_root = path
            ctx.config.active_project = str(path)
            if str(path) not in ctx.config.projects:
                ctx.config.projects.append(str(path))
            ctx.config.save()
            print(f"Switched to {path}")
            return 0
        print("Usage: /projects [list|add <path>|switch <path>]")
        return 2

    def _cmd_cd(self, args: list[str], ctx: RuntimeContext) -> int:
        if not args:
            print(ctx.project_root)
            return 0
        path = Path(args[0]).expanduser()
        if not path.is_absolute():
            path = ctx.project_root / path
        path = path.resolve()
        if not path.exists() or not path.is_dir():
            print(f"Directory does not exist: {path}")
            return 1
        ctx.project_root = path
        ctx.config.active_project = str(path)
        if str(path) not in ctx.config.projects:
            ctx.config.projects.append(str(path))
        ctx.config.save()
        return 0

