"""UaLens TUI application."""

import logging
import queue

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Tree

from .logging_config import configure_logging, log_queue
from .messages import DataUpdate
from .screens import ConnectionModal
from .ua_client import UaClient
from .widgets import (
    AddressSpace,
    AttributeInspector,
    DataTableView,
    GraphView,
    LogPane,
)

logger = logging.getLogger(__name__)


class UaLensApp(App):
    TITLE = "UaLens"
    SUB_TITLE = "Disconnected"
    CSS_PATH = "ualens.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        ("c", "show_connection_modal", "Connect"),
        ("d", "disconnect", "Disconnect"),
        ("r", "refresh_tree", "Refresh Tree"),
        ("s", "toggle_subscription", "Subscribe"),
        ("g", "toggle_graph", "Toggle Graph"),
        ("q", "quit", "Quit"),
    ]
    theme = "nord"

    def __init__(self, *, initial_connection: dict | None = None):
        super().__init__()
        self.ua_client = UaClient()
        self._selected_tree_node = None
        self._initial_connection = initial_connection

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield AddressSpace()
            with Vertical():
                yield AttributeInspector()
                with DataTableView():
                    yield DataTable()
                yield GraphView()
        yield LogPane()
        yield Footer()

    async def on_mount(self) -> None:
        self._log_drain_timer = self.set_interval(0.5, self._drain_log_queue)
        if self._initial_connection:
            await self.handle_connection(self._initial_connection)

    def _drain_log_queue(self) -> None:
        try:
            log_pane = self.query_one(LogPane)
            while True:
                try:
                    msg = log_queue.get_nowait()
                    log_pane.write(msg)
                except queue.Empty:
                    break
        except Exception:
            pass

    def on_data_update(self, message: DataUpdate) -> None:
        self.update_data_view(message.node_id, message.value)

    def update_data_view(self, node_id, value) -> None:
        try:
            table_view = self.query_one(DataTableView)
            table_view.update_value(node_id, value)

            graph_view = self.query_one(GraphView)
            table = table_view.query_one(DataTable)
            try:
                row_data = table.get_row(str(node_id))
                display_name = row_data[0] if row_data else str(node_id)
            except Exception:
                display_name = str(node_id)
            graph_view.add_data_point(node_id, value, display_name)
        except Exception:
            pass

    def action_show_connection_modal(self) -> None:
        self.push_screen(ConnectionModal(), self.handle_connection)

    async def action_disconnect(self) -> None:
        if not self.ua_client.is_connected:
            self.notify("Not connected", severity="warning")
            return
        await self.ua_client.disconnect()
        self.sub_title = "Disconnected"
        self.notify("Disconnected")
        self.query_one(AttributeInspector).clear_attributes()
        self.query_one(DataTableView).clear()
        self.query_one(GraphView).clear_all()
        address_space = self.query_one(AddressSpace)
        tree = address_space.query_one(Tree)
        tree.clear()
        tree.root.add_leaf("Not connected — press C to connect")
        self._selected_tree_node = None

    async def action_refresh_tree(self) -> None:
        if not self.ua_client.is_connected:
            self.notify("Not connected", severity="warning")
            return
        address_space = self.query_one(AddressSpace)
        await address_space.refresh_tree(self.ua_client)
        self.notify("Address space refreshed")

    async def action_toggle_subscription(self) -> None:
        if not self.ua_client.is_connected:
            self.notify("Not connected", severity="warning")
            return
        node_data = self._selected_tree_node
        if not node_data or node_data["node_class"] != "Variable":
            self.notify("Select a Variable in the Address Space tree first", severity="warning")
            return
        display_name = node_data["display_name"]
        node_id = node_data["node_id"]
        if node_id in self.ua_client.subscriptions:
            await self.ua_client.unsubscribe(node_id)
            table = self.query_one(DataTableView).query_one(DataTable)
            try:
                table.remove_row(str(node_id))
            except Exception:
                pass
            self.query_one(GraphView).clear_node_data(node_id)
            self.notify(f"Unsubscribed from {display_name}")
        else:
            def on_data_change(node_obj, val, data):
                self.post_message(DataUpdate(node_id, val))

            await self.ua_client.subscribe(node_id, on_data_change)
            val = await self.ua_client.read_node_value(node_id)
            self.query_one(DataTableView).add_subscription_row(display_name, val, node_id)
            self.notify(f"Subscribed to {display_name}")

    def action_toggle_graph(self) -> None:
        try:
            data_table_view = self.query_one(DataTableView)
            table = data_table_view.query_one(DataTable)

            if table.row_count == 0:
                self.notify("No variables subscribed yet", severity="warning")
                return

            cursor_index = table.cursor_row
            if cursor_index is None:
                self.notify("No row selected", severity="warning")
                return

            rows_list = list(table.rows)
            if cursor_index < 0 or cursor_index >= len(rows_list):
                self.notify(f"Invalid cursor position: {cursor_index}", severity="error")
                return

            row_key = rows_list[cursor_index]
            row_data = table.get_row(row_key)
            if len(row_data) < 4:
                self.notify(f"Row has {len(row_data)} columns, expected 4", severity="error")
                return

            display_name = row_data[0]
            node_id = self.query_one(DataTableView).get_node_id(row_key)

            graph_view = self.query_one(GraphView)
            is_graphed = graph_view.toggle_node_graph(node_id, display_name)

            table_view = self.query_one(DataTableView)
            table_view.set_graphed(node_id, is_graphed)

            if is_graphed:
                self.notify(f"Added {display_name} to graph")
            else:
                self.notify(f"Removed {display_name} from graph")

        except Exception as e:
            logger.error("Error in action_toggle_graph: %s", e, exc_info=True)
            self.notify(f"Error: {str(e)}", severity="error")

    async def handle_connection(self, connection_info: dict | None) -> None:
        if not connection_info:
            return

        if self.ua_client.is_connected:
            await self.ua_client.disconnect()

        url = connection_info["url"]
        username = connection_info.get("username")
        password = connection_info.get("password")

        self.sub_title = f"Connecting to {url}..."
        success, message = await self.ua_client.connect(url, username, password)

        if success:
            self.sub_title = f"Connected to {url}"
            self.notify("Connected successfully!")
            self._selected_tree_node = None
            self.query_one(AttributeInspector).clear_attributes()
            self.query_one(DataTableView).clear()
            self.query_one(GraphView).clear_all()
            address_space = self.query_one(AddressSpace)
            await address_space.refresh_tree(self.ua_client)
        else:
            self.sub_title = "Disconnected"
            self.notify(f"Connection failed: {message}", severity="error")
