"""Tests for app flow and integration."""

import pytest
from textual.widgets import DataTable, Footer, Header, Tree

from ualens.app import UaLensApp
from ualens.messages import DataUpdate
from ualens.widgets import (
    AddressSpace,
    AttributeInspector,
    DataTableView,
    GraphView,
    LogPane,
)


# --- App composition ---


async def test_app_composes_header_footer():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(Header)
        app.query_one(Footer)


async def test_app_composes_main_widgets():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(AddressSpace)
        app.query_one(AttributeInspector)
        app.query_one(DataTableView)
        app.query_one(GraphView)
        app.query_one(LogPane)


async def test_app_initial_state():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.sub_title == "Disconnected"
        assert app.ua_client.is_connected is False
        assert app._selected_tree_node is None


# --- Key bindings / actions ---


async def test_app_connect_key_opens_modal():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.press("c")
        await pilot.pause()
        from ualens.screens.connection import ConnectionModal
        assert isinstance(app.screen, ConnectionModal)


async def test_app_escape_closes_modal_without_connecting():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.press("c")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        from ualens.screens.connection import ConnectionModal
        assert not isinstance(app.screen, ConnectionModal)
        assert not app.ua_client.is_connected


async def test_app_disconnect_when_not_connected_shows_warning():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.press("d")
        await pilot.pause()
        # Should show notification "Not connected"
        assert not app.ua_client.is_connected


# --- DataUpdate message ---


async def test_app_on_data_update_updates_table_and_graph():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        table_view = app.query_one(DataTableView)
        table = table_view.query_one(DataTable)
        table.add_row("Temp", "0", "", "ns=2;i=1", key="ns=2;i=1")
        graph_view = app.query_one(GraphView)
        graph_view.graphed_nodes.add("ns=2;i=1")
        graph_view.node_names["ns=2;i=1"] = "Temp"

        app.post_message(DataUpdate("ns=2;i=1", 99.5))
        await pilot.pause()

        row = table.get_row("ns=2;i=1")
        assert row[1] == "99.5"
        assert "ns=2;i=1" in graph_view.data_history
        assert len(graph_view.data_history["ns=2;i=1"]) == 1


# --- Integration: connect to real server ---


async def test_app_connect_and_refresh_tree(opcua_server):
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.handle_connection({
            "url": "opc.tcp://127.0.0.1:48401/freeopcua/server/",
            "username": None,
            "password": None,
        })
        await pilot.pause()

        assert app.ua_client.is_connected
        assert app.sub_title == "Connected to opc.tcp://127.0.0.1:48401/freeopcua/server/"
        tree = app.query_one(AddressSpace).query_one(Tree)
        assert len(list(tree.root.children)) > 0


async def test_app_disconnect_clears_state(opcua_server):
    app = UaLensApp()
    async with app.run_test() as pilot:
        await app.handle_connection({
            "url": "opc.tcp://127.0.0.1:48401/freeopcua/server/",
            "username": None,
            "password": None,
        })
        await pilot.pause()
        assert app.ua_client.is_connected

        await pilot.press("d")
        await pilot.pause()

        assert not app.ua_client.is_connected
        assert app.sub_title == "Disconnected"
        assert app._selected_tree_node is None
        table = app.query_one(DataTableView).query_one(DataTable)
        assert table.row_count == 0
        tree = app.query_one(AddressSpace).query_one(Tree)
        # After disconnect the tree shows exactly one "not connected" hint leaf
        children = list(tree.root.children)
        assert len(children) == 1
        assert "Not connected" in str(children[0].label)


async def test_app_refresh_tree_when_not_connected():
    app = UaLensApp()
    async with app.run_test() as pilot:
        await pilot.press("r")
        await pilot.pause()
        assert not app.ua_client.is_connected


async def test_app_reconnect_disconnects_first(opcua_server):
    """Connecting while already connected should cleanly disconnect the old session."""
    app = UaLensApp()
    async with app.run_test() as pilot:
        await app.handle_connection({
            "url": "opc.tcp://127.0.0.1:48401/freeopcua/server/",
            "username": None,
            "password": None,
        })
        await pilot.pause()
        assert app.ua_client.is_connected

        # Connect again to the same server — should succeed without resource leak
        await app.handle_connection({
            "url": "opc.tcp://127.0.0.1:48401/freeopcua/server/",
            "username": None,
            "password": None,
        })
        await pilot.pause()
        assert app.ua_client.is_connected
