"""Data table widget for subscribed variables."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable


def _short_node_id(node_id) -> str:
    """Format an asyncua NodeId as compact OPC UA notation (e.g. 'ns=2;i=3')."""
    try:
        ns = node_id.NamespaceIndex
        return f"i={node_id.Identifier}" if ns == 0 else f"ns={ns};i={node_id.Identifier}"
    except Exception:
        return str(node_id)


class DataTableView(Vertical):
    """Table of subscribed variables with live values."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._node_ids: dict = {}  # str(node_id) → original node_id object

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        self.border_title = "Subscribed Variables"
        self._setup_table()

    def _setup_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_column("Node Name", key="name")
        table.add_column("Value", key="value")
        table.add_column("Graph", key="graph")
        table.add_column("ID", key="id")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def add_subscription_row(self, display_name: str, value, node_id) -> None:
        """Add a subscribed variable row with a compact node ID display."""
        key = str(node_id)
        self._node_ids[key] = node_id
        self.query_one(DataTable).add_row(
            display_name,
            str(value) if value is not None else "N/A",
            "",
            _short_node_id(node_id),
            key=key,
        )

    def get_node_id(self, row_key):
        """Return the original node_id object for a row key (RowKey or str)."""
        key = row_key.value if hasattr(row_key, "value") else str(row_key)
        return self._node_ids.get(key)

    def update_value(self, node_id, value) -> None:
        table = self.query_one(DataTable)
        try:
            table.update_cell(str(node_id), "value", str(value))
        except Exception:
            pass

    def set_graphed(self, node_id, is_graphed: bool) -> None:
        table = self.query_one(DataTable)
        marker = "✓" if is_graphed else ""
        try:
            table.update_cell(str(node_id), "graph", marker)
        except Exception:
            pass

    def clear(self) -> None:
        self._node_ids.clear()
        self._setup_table()
