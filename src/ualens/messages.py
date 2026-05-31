"""Application messages."""

from textual.message import Message


class DataUpdate(Message):
    """Message sent when OPC UA data changes."""

    def __init__(self, node_id, value) -> None:
        super().__init__()
        self.node_id = node_id
        self.value = value
