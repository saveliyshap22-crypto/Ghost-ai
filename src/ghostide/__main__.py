from .cli import GhostIDE


def main() -> int:
    return GhostIDE().run()


if __name__ == "__main__":
    raise SystemExit(main())

