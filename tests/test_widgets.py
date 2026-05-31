"""Tests for UI widgets."""

import pytest
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Tree

from ualens.widgets import (
    AddressSpace,
    AttributeInspector,
    DataTableView,
    GraphView,
    LogPane,
)


# --- Minimal apps to mount widgets ---


class AttributeInspectorApp(App):
    def compose(self) -> ComposeResult:
        yield AttributeInspector()


class DataTableViewApp(App):
    def compose(self) -> ComposeResult:
        yield DataTableView()


class GraphViewApp(App):
    def compose(self) -> ComposeResult:
        yield GraphView()


class LogPaneApp(App):
    def compose(self) -> ComposeResult:
        yield LogPane()


class AddressSpaceApp(App):
    def compose(self) -> ComposeResult:
        yield AddressSpace()

    def __init__(self):
        super().__init__()
        self.ua_client = None


# --- AttributeInspector ---


async def test_attribute_inspector_mount():
    app = AttributeInspectorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(AttributeInspector)
        assert inspector.border_title == "Node Attributes (select a node)"
        table = inspector.query_one(DataTable)
        assert len(table.columns) == 2


async def test_attribute_inspector_show_attributes():
    app = AttributeInspectorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(AttributeInspector)
        inspector.show_attributes({"NodeId": "ns=2;i=3", "Value": "42"})
        await pilot.pause()
        assert inspector.border_title == "Node Attributes"
        table = inspector.query_one(DataTable)
        rows = list(table.rows)
        assert len(rows) == 2


async def test_attribute_inspector_clear_attributes():
    app = AttributeInspectorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        inspector = app.query_one(AttributeInspector)
        inspector.show_attributes({"A": "1"})
        await pilot.pause()
        inspector.clear_attributes()
        await pilot.pause()
        assert inspector.border_title == "Node Attributes (select a node)"
        table = inspector.query_one(DataTable)
        assert table.row_count == 0


# --- DataTableView ---


async def test_data_table_view_mount():
    app = DataTableViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        view = app.query_one(DataTableView)
        assert view.border_title == "Subscribed Variables"
        table = view.query_one(DataTable)
        assert len(table.columns) == 4


async def test_data_table_view_update_value():
    app = DataTableViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        view = app.query_one(DataTableView)
        table = view.query_one(DataTable)
        table.add_row("Var1", "10", "", "ns=2;i=1", key="ns=2;i=1")
        view.update_value("ns=2;i=1", 99)
        await pilot.pause()
        row = table.get_row("ns=2;i=1")
        assert row[1] == "99"


async def test_data_table_view_set_graphed():
    app = DataTableViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        view = app.query_one(DataTableView)
        table = view.query_one(DataTable)
        table.add_row("V", "0", "", "ns=2;i=1", key="ns=2;i=1")
        view.set_graphed("ns=2;i=1", True)
        await pilot.pause()
        row = table.get_row("ns=2;i=1")
        assert row[2] == "✓"
        view.set_graphed("ns=2;i=1", False)
        await pilot.pause()
        row = table.get_row("ns=2;i=1")
        assert row[2] == ""


async def test_data_table_view_clear():
    app = DataTableViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        view = app.query_one(DataTableView)
        table = view.query_one(DataTable)
        table.add_row("V", "0", "", "ns=2;i=1", key="ns=2;i=1")
        view.clear()
        await pilot.pause()
        assert table.row_count == 0


# --- GraphView ---


async def test_graph_view_add_data_point():
    app = GraphViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        graph = app.query_one(GraphView)
        graph.add_data_point("ns=2;i=1", 42.5, "Temperature")
        assert "ns=2;i=1" in graph.data_history
        assert len(graph.data_history["ns=2;i=1"]) == 1
        assert graph.node_names["ns=2;i=1"] == "Temperature"


async def test_graph_view_add_data_point_non_numeric_ignored():
    app = GraphViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        graph = app.query_one(GraphView)
        graph.add_data_point("ns=2;i=1", "not_a_number", "V")
        assert graph.data_history["ns=2;i=1"] == graph.data_history["ns=2;i=1"]  # deque
        assert len(graph.data_history["ns=2;i=1"]) == 0


async def test_graph_view_toggle_node_graph():
    app = GraphViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        graph = app.query_one(GraphView)
        out = graph.toggle_node_graph("ns=2;i=1", "Var1")
        assert out is True
        assert "ns=2;i=1" in graph.graphed_nodes
        out = graph.toggle_node_graph("ns=2;i=1")
        assert out is False
        assert "ns=2;i=1" not in graph.graphed_nodes


async def test_graph_view_clear_node_data():
    app = GraphViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        graph = app.query_one(GraphView)
        graph.add_data_point("ns=2;i=1", 1.0, "V")
        graph.graphed_nodes.add("ns=2;i=1")
        graph.clear_node_data("ns=2;i=1")
        assert "ns=2;i=1" not in graph.data_history
        assert "ns=2;i=1" not in graph.graphed_nodes


async def test_graph_view_clear_all():
    app = GraphViewApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        graph = app.query_one(GraphView)
        graph.add_data_point("ns=2;i=1", 1.0, "V1")
        graph.graphed_nodes.add("ns=2;i=1")
        graph.clear_all()
        assert len(graph.data_history) == 0
        assert len(graph.graphed_nodes) == 0
        assert len(graph.node_names) == 0


# --- LogPane ---


async def test_log_pane_write():
    app = LogPaneApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        log_pane = app.query_one(LogPane)
        log_pane.write("test message")
        await pilot.pause()
        # RichLog content is in its renderable; we just check write doesn't raise
        assert log_pane.rich_log is not None


async def test_log_pane_border_title():
    app = LogPaneApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        log_pane = app.query_one(LogPane)
        assert log_pane.border_title == "Log"


# --- AddressSpace ---


async def test_address_space_mount():
    app = AddressSpaceApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        space = app.query_one(AddressSpace)
        assert space.border_title == "Address Space"
        tree = space.query_one(Tree)
        assert tree is not None


async def test_address_space_highlighted_updates_selected_node():
    """Arrow-key navigation (NodeHighlighted) must update _selected_tree_node."""
    app = AddressSpaceApp()

    class MockClient:
        is_connected = False  # disconnected: skips attribute loading, no AttributeInspector needed

        async def get_children(self, node_id=None):
            return [
                {"node_id": "i=1", "display_name": "VarA", "node_class": "Variable"},
                {"node_id": "i=2", "display_name": "VarB", "node_class": "Variable"},
            ]

    app.ua_client = MockClient()
    async with app.run_test() as pilot:
        space = app.query_one(AddressSpace)
        await space.refresh_tree(app.ua_client)
        await pilot.pause()
        tree = space.query_one(Tree)
        node_a = list(tree.root.children)[0]
        space.post_message(Tree.NodeHighlighted(node_a))
        await pilot.pause()
        assert app._selected_tree_node is not None
        assert app._selected_tree_node["display_name"] == "VarA"


async def test_address_space_refresh_tree():
    """Refresh tree with mock client populates tree from get_children."""
    app = AddressSpaceApp()

    class MockClient:
        is_connected = True

        async def get_children(self, node_id=None):
            if node_id is None:
                return [
                    {
                        "node_id": "i=84",
                        "display_name": "Objects",
                        "node_class": "Object",
                    },
                    {
                        "node_id": "i=85",
                        "display_name": "MyVar",
                        "node_class": "Variable",
                    },
                ]
            return []

    app.ua_client = MockClient()
    async with app.run_test() as pilot:
        await pilot.pause()
        space = app.query_one(AddressSpace)
        await space.refresh_tree(app.ua_client)
        await pilot.pause()
        tree = space.query_one(Tree)
        # Root is expanded; we have Objects (with placeholder) and MyVar as leaf
        assert len(list(tree.root.children)) >= 2
        labels = [str(c.label) for c in tree.root.children]
        # Labels now include icon prefixes (e.g. "○ Objects", "◆ MyVar")
        assert any("Objects" in lbl for lbl in labels)
        assert any("MyVar" in lbl for lbl in labels)
