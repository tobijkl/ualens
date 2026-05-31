"""Tests for CLI entry point."""

import pytest

from ualens.main import build_parser, connection_from_args, main


def test_connection_from_args_no_url():
    args = build_parser().parse_args([])
    assert connection_from_args(args) is None


def test_connection_from_args_url_only():
    args = build_parser().parse_args(["--url", "opc.tcp://127.0.0.1:4840/"])
    assert connection_from_args(args) == {
        "url": "opc.tcp://127.0.0.1:4840/",
        "username": None,
        "password": None,
    }


def test_connection_from_args_short_flag():
    args = build_parser().parse_args(["-u", "opc.tcp://host:4840/path"])
    assert connection_from_args(args) == {
        "url": "opc.tcp://host:4840/path",
        "username": None,
        "password": None,
    }


def test_connection_from_args_with_credentials():
    args = build_parser().parse_args(
        ["-u", "opc.tcp://x:1/", "--username", "user", "--password", "secret"]
    )
    assert connection_from_args(args) == {
        "url": "opc.tcp://x:1/",
        "username": "user",
        "password": "secret",
    }


def test_connection_from_args_strips_url():
    args = build_parser().parse_args(["--url", "  opc.tcp://a:1/  "])
    assert connection_from_args(args) == {
        "url": "opc.tcp://a:1/",
        "username": None,
        "password": None,
    }


def test_connection_from_args_username_only_raises():
    args = build_parser().parse_args(
        ["--url", "opc.tcp://x/", "--username", "u"]
    )
    with pytest.raises(ValueError, match="both --username and --password"):
        connection_from_args(args)


def test_connection_from_args_password_only_raises():
    args = build_parser().parse_args(
        ["--url", "opc.tcp://x/", "--password", "p"]
    )
    with pytest.raises(ValueError, match="both --username and --password"):
        connection_from_args(args)


def test_main_rejects_partial_credentials():
    with pytest.raises(SystemExit) as exc_info:
        main(["--url", "opc.tcp://x/", "--username", "u"])
    assert exc_info.value.code == 2
