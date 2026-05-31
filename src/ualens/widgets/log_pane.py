"""Log pane widget."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import RichLog


class LogPane(Vertical):
    """Log pane for connection events and errors."""

    def compose(self) -> ComposeResult:
        yield RichLog(max_lines=100, highlight=True)

    def on_mount(self) -> None:
        self.border_title = "Log"

    @property
    def rich_log(self) -> RichLog:
        return self.query_one(RichLog)

    def write(self, text: str) -> None:
        try:
            self.rich_log.write(text)
        except Exception:
            pass
