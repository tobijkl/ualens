"""Attribute inspector widget: displays node attributes (NodeId, BrowseName, etc.)."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable


class AttributeInspector(Vertical):
    """Displays NodeId, BrowseName, Value, DataType, AccessLevel, etc. for the selected node."""

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        self.border_title = "Node Attributes (select a node)"
        self._setup_table()

    def _setup_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_column("Attribute", key="attr")
        table.add_column("Value", key="val")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_header = False

    def show_attributes(self, attrs: dict) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_column("Attribute", key="attr")
        table.add_column("Value", key="val")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_header = False
        for name, value in attrs.items():
            table.add_row(name, str(value), key=name)
        self.border_title = "Node Attributes"

    def clear_attributes(self) -> None:
        self._setup_table()
        self.border_title = "Node Attributes (select a node)"
