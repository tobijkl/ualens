"""Entry point for ualens TUI application."""

import argparse

from .app import UaLensApp
from .logging_config import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ualens",
        description="Terminal OPC UA explorer (TUI).",
    )
    parser.add_argument(
        "-u",
        "--url",
        metavar="URL",
        help="OPC UA server endpoint; connect on startup without opening the dialog",
    )
    parser.add_argument(
        "--username",
        help="Username for user/password authentication (use with --password)",
    )
    parser.add_argument(
        "--password",
        help="Password for user/password authentication",
    )
    return parser


def connection_from_args(args: argparse.Namespace) -> dict | None:
    if not args.url:
        return None
    url = args.url.strip()
    if not url:
        return None
    user, pwd = args.username, args.password
    if (user is not None) ^ (pwd is not None):
        raise ValueError(
            "provide both --username and --password for authentication, or neither for anonymous"
        )
    if user is not None:
        return {"url": url, "username": user, "password": pwd}
    return {"url": url, "username": None, "password": None}


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        initial = connection_from_args(args)
    except ValueError as e:
        parser.error(str(e))
    app = UaLensApp(initial_connection=initial)
    app.run()


if __name__ == "__main__":
    main()
