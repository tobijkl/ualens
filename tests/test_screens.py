"""Tests for screens (ConnectionModal)."""

import pytest
from textual.widgets import Button, Checkbox, Input, Static

from ualens.app import UaLensApp
from ualens.screens.connection import ConnectionModal


async def test_connection_modal_compose():
    """Connection modal shows title, favorites select, url input, auth fields, buttons."""
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.press("c")
        await pilot.pause()
        modal = app.screen
        assert isinstance(modal, ConnectionModal)
        title = modal.query_one("#dialog-title", Static)
        assert "Connect to OPC UA Server" in str(title.render())
        assert modal.query_one("#url-input", Input) is not None
        assert modal.query_one("#anonymous-checkbox", Checkbox) is not None
        assert modal.query_one("#username-input", Input) is not None
        assert modal.query_one("#password-input", Input) is not None
        assert modal.query_one("#connect-btn", Button) is not None
        assert modal.query_one("#save-favorite-btn", Button) is not None
        assert modal.query_one("#cancel-btn", Button) is not None


async def test_connection_modal_cancel_dismisses_with_none():
    """Pressing Escape or Cancel dismisses modal with None."""
    app = UaLensApp()
    result_holder = []

    def capture_result(r):
        result_holder.append(r)

    async with app.run_test() as pilot:
        app.push_screen(ConnectionModal(), capture_result)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
    assert result_holder == [None]


async def test_connection_modal_submit_returns_connection_info():
    """Entering URL and pressing Connect dismisses with connection dict."""
    app = UaLensApp()
    result_holder = []

    def capture_result(r):
        result_holder.append(r)

    async with app.run_test() as pilot:
        app.push_screen(ConnectionModal(), capture_result)
        await pilot.pause()
        url_input = app.screen.query_one("#url-input", Input)
        url_input.value = "opc.tcp://localhost:4840/path"
        app.screen.action_submit()
        await pilot.pause()
    assert len(result_holder) == 1
    assert result_holder[0]["url"] == "opc.tcp://localhost:4840/path"
    assert result_holder[0].get("username") is None
    assert result_holder[0].get("password") is None


async def test_connection_modal_submit_with_credentials():
    """With Anonymous unchecked, username/password are included."""
    app = UaLensApp()
    result_holder = []

    def capture_result(r):
        result_holder.append(r)

    async with app.run_test() as pilot:
        app.push_screen(ConnectionModal(), capture_result)
        await pilot.pause()
        modal = app.screen
        modal.query_one("#anonymous-checkbox", Checkbox).value = False
        modal.query_one("#username-input", Input).value = "user"
        modal.query_one("#password-input", Input).value = "secret"
        modal.query_one("#url-input", Input).value = "opc.tcp://host/path"
        modal.action_submit()
        await pilot.pause()
    assert result_holder[0]["url"] == "opc.tcp://host/path"
    assert result_holder[0]["username"] == "user"
    assert result_holder[0]["password"] == "secret"


async def test_connection_modal_connect_button_submits():
    """Pressing Enter after setting URL submits the form (submit binding)."""
    app = UaLensApp()
    result_holder = []

    def capture_result(r):
        result_holder.append(r)

    async with app.run_test(size=(100, 40)) as pilot:
        app.push_screen(ConnectionModal(), capture_result)
        await pilot.pause()
        url_input = app.screen.query_one("#url-input", Input)
        url_input.value = "opc.tcp://x/y"
        url_input.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
    assert len(result_holder) == 1
    assert result_holder[0]["url"] == "opc.tcp://x/y"


async def test_connection_modal_anonymous_initial_state():
    """When Anonymous is checked (default), username/password inputs are disabled."""
    app = UaLensApp()
    async with app.run_test() as pilot:
        app.push_screen(ConnectionModal())
        await pilot.pause()
        modal = app.screen
        assert modal.query_one("#anonymous-checkbox", Checkbox).value is True
        assert modal.query_one("#username-input", Input).disabled is True
        assert modal.query_one("#password-input", Input).disabled is True
