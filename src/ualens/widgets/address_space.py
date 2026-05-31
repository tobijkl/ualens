"""Address space tree widget with lazy loading."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Tree

from ..ua_client import UaClient
from .attribute_inspector import AttributeInspector

# Rich markup labels by node class: expandable nodes get a folder icon,
# Variables get a value indicator to distinguish them from containers.
_NODE_LABEL = {
    "Object": "[bold blue]○[/] {}",
    "Folder": "[bold blue]▶[/] {}",
    "Variable": "[green]◆[/] {}",
    "Method": "[yellow]ƒ[/] {}",
}
_NODE_LABEL_DEFAULT = "{}"


def _make_label(node_class: str, display_name: str) -> str:
    template = _NODE_LABEL.get(node_class, _NODE_LABEL_DEFAULT)
    return template.format(display_name)


class AddressSpace(Vertical):
    """Address space tree with lazy-loaded children."""

    def compose(self) -> ComposeResult:
        yield Tree("Root")

    def on_mount(self) -> None:
        self.border_title = "Address Space"
        ua_client = getattr(self.app, "ua_client", None)
        if ua_client is not None and not ua_client.is_connected:
            tree = self.query_one(Tree)
            tree.root.add_leaf("Not connected — press C to connect")
            tree.root.expand()

    async def refresh_tree(self, ua_client: UaClient) -> None:
        tree = self.query_one(Tree)
        tree.clear()

        children = await ua_client.get_children()
        for child in children:
            label = _make_label(child["node_class"], child["display_name"])
            if child["node_class"] in ["Object", "Folder"]:
                node = tree.root.add(label, data=child, expand=False)
                node.add("loading...")
            else:
                tree.root.add_leaf(label, data=child)

        tree.root.expand()

    async def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        node = event.node
        if not node.data:
            return

        if len(node.children) == 1 and str(node.children[0].label) == "loading...":
            node.remove_children()

            ua_client = self.app.ua_client
            if not ua_client.is_connected:
                return
            children = await ua_client.get_children(node.data["node_id"])
            for child in children:
                label = _make_label(child["node_class"], child["display_name"])
                if child["node_class"] in ["Object", "Folder"]:
                    new_node = node.add(label, data=child, expand=False)
                    new_node.add("loading...")
                else:
                    node.add_leaf(label, data=child)

    async def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        node = event.node
        if not node.data:
            return

        self.app._selected_tree_node = node.data

        ua_client = self.app.ua_client
        if ua_client.is_connected:
            attrs = await ua_client.get_node_attributes(node.data["node_id"])
            inspector = self.app.query_one(AttributeInspector)
            inspector.show_attributes(attrs)

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node = event.node
        if not node.data:
            return

        self.app._selected_tree_node = node.data

        ua_client = self.app.ua_client
        if ua_client.is_connected:
            attrs = await ua_client.get_node_attributes(node.data["node_id"])
            inspector = self.app.query_one(AttributeInspector)
            inspector.show_attributes(attrs)
