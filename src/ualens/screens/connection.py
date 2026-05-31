"""Connection modal screen."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from ..favorites import add_favorite, load_favorites


class ConnectionModal(ModalScreen[dict]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="connection-dialog"):
            yield Static("Connect to OPC UA Server", id="dialog-title")
            yield Label("Favorites", classes="input-label")
            yield Select(
                self._favorite_options(),
                prompt="Load favorite...",
                id="favorites-select",
            )
            yield Label("Server URL", classes="input-label")
            yield Input(
                value="opc.tcp://127.0.0.1:4840/freeopcua/server/",
                placeholder="opc.tcp://hostname:4840/path/",
                id="url-input",
            )
            yield Checkbox("Anonymous (no authentication)", value=True, id="anonymous-checkbox")
            yield Label("Username", classes="input-label", id="username-label")
            yield Input(placeholder="Username", id="username-input")
            yield Label("Password", classes="input-label", id="password-label")
            yield Input(placeholder="Password", password=True, id="password-input")
            with Container(id="dialog-buttons-container"):
                with Horizontal(id="dialog-buttons"):
                    yield Button("Connect", variant="primary", id="connect-btn")
                    yield Button("Save Favorite", variant="default", id="save-favorite-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")

    def _favorite_options(self) -> list[tuple[str, str]]:
        favorites = load_favorites()
        if not favorites:
            return [("(no favorites saved)", "")]
        return [(f.get("label", f["url"]), f["url"]) for f in favorites]

    def _favorite_by_url(self, url: str) -> dict | None:
        for f in load_favorites():
            if f.get("url") == url:
                return f
        return None

    def on_mount(self) -> None:
        self._set_auth_fields_enabled(False)
        fav_select = self.query_one("#favorites-select", Select)
        fav_select.set_options(self._favorite_options())

    def _set_auth_fields_enabled(self, enabled: bool) -> None:
        self.query_one("#username-input", Input).disabled = not enabled
        self.query_one("#password-input", Input).disabled = not enabled
        self.query_one("#username-label", Label).styles.opacity = 1.0 if enabled else 0.4
        self.query_one("#password-label", Label).styles.opacity = 1.0 if enabled else 0.4

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value and event.value != Select.BLANK and event.value != "":
            fav = self._favorite_by_url(str(event.value))
            if fav:
                self.query_one("#url-input", Input).value = fav["url"]
                username = fav.get("username")
                if username:
                    self.query_one("#anonymous-checkbox", Checkbox).value = False
                    self.query_one("#username-input", Input).value = username
                    self._set_auth_fields_enabled(True)
                else:
                    self.query_one("#anonymous-checkbox", Checkbox).value = True
                    self.query_one("#username-input", Input).value = ""
                    self._set_auth_fields_enabled(False)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "anonymous-checkbox":
            self._set_auth_fields_enabled(not event.value)

    def action_submit(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            self.notify("Please enter a server URL", severity="warning")
            return
        is_anonymous = self.query_one("#anonymous-checkbox", Checkbox).value
        username = None if is_anonymous else self.query_one("#username-input", Input).value
        password = None if is_anonymous else self.query_one("#password-input", Input).value
        self.dismiss({"url": url, "username": username, "password": password})

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "connect-btn":
            self.action_submit()
        elif event.button.id == "save-favorite-btn":
            url = self.query_one("#url-input", Input).value.strip()
            if not url:
                self.notify("Enter a URL first", severity="warning")
                return
            is_anonymous = self.query_one("#anonymous-checkbox", Checkbox).value
            username = None if is_anonymous else self.query_one("#username-input", Input).value
            add_favorite(url, label=url, username=username)
            self.notify("Saved as favorite")
            fav_select = self.query_one("#favorites-select", Select)
            fav_select.set_options(self._favorite_options())
        else:
            self.action_cancel()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_submit()
