# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Entwicklungsumgebung einrichten
uv sync --group dev

# App starten
uv run ualens

# App mit direkter Verbindung starten
uv run ualens --url opc.tcp://127.0.0.1:4840/freeopcua/server/

# Mock-OPC-UA-Server starten (für manuelle Tests)
uv run ualens-mock-server
uv run ualens-mock-server --username user --password secret

# Alle Tests ausführen
uv run pytest

# Einzelnen Test ausführen
uv run pytest tests/test_app.py::test_app_composes_header_footer

# Paket bauen
uv build
```

## Architektur

**ualens** ist ein Terminal-OPC-UA-Explorer, der auf [Textual](https://textual.textualize.io/) aufbaut und `asyncua` als OPC-UA-Client-Bibliothek nutzt. Die gesamte App läuft im asyncio-Event-Loop von Textual.

### Schichtenmodell

```
main.py          → CLI-Argument-Parsing, startet UaLensApp
app.py           → UaLensApp (Textual App), koordiniert alle Widgets und den UaClient
ua_client.py     → UaClient, kapselt asyncua (Verbindung, Browse, Subscriptions)
screens/         → Modale Screens (ConnectionModal)
widgets/         → Wiederverwendbare Textual-Widgets
messages.py      → Textual-Messages für interne Kommunikation (DataUpdate)
favorites.py     → Persistenz gespeicherter Server-URLs (JSON via platformdirs)
logging_config.py→ Logging in Datei + Queue für TUI-LogPane
```

### Datenfluss bei Subscriptions

1. `UaClient.subscribe()` registriert einen asyncua-Subscription-Handler
2. Handler ruft `callback(node, val, data)` auf → thread-sicherer Aufruf im asyncua-Thread
3. Callback ruft `app.post_message(DataUpdate(node_id, val))` auf
4. `UaLensApp.on_data_update()` empfängt die Message im Textual-Event-Loop
5. `DataTableView` und `GraphView` werden aktualisiert

### Widget-Layout (app.py `compose`)

```
Header
Horizontal
  ├── AddressSpace (Tree mit Lazy Loading)
  └── Vertical
        ├── AttributeInspector (Key-Value-Tabelle für Node-Attribute)
        ├── DataTableView (DataTable der abonnierten Variablen)
        └── GraphView (textual-plotext Zeitreihe)
LogPane
Footer
```

### Lazy Loading im Adressbaum

`AddressSpace` lädt OPC-UA-Kinder nur bei Expand (`on_tree_node_expanded`). Expandierbare Knoten (Object/Folder) erhalten beim ersten Laden einen Platzhalter-`"loading..."`-Knoten; beim Expand wird dieser durch echte Kinder ersetzt.

### Tests

Tests nutzen `pytest-asyncio` mit `asyncio_mode = auto` (keine `@pytest.mark.asyncio`-Dekoratoren nötig). Für Integrationstests, die einen echten OPC-UA-Server brauchen, gibt es das `opcua_server`-Fixture in `conftest.py` (In-Process-Server auf Port 48401). Textual-App-Tests verwenden `app.run_test()` als async Context Manager.

### Logging

`configure_logging()` schreibt in `~/Library/Logs/ualens/app.log` (macOS) bzw. dem plattformspezifischen Verzeichnis via `platformdirs`, plus eine `queue.Queue`. `UaLensApp` draint die Queue alle 0,5 Sekunden in die `LogPane`. asyncua-Logs werden auf WARNING gefiltert um den Log-Pane nicht zu überflutten.

### Wichtige Fallstricke

- **`RowKey.value`**: `DataTable.rows` gibt `RowKey`-Objekte zurück, deren `str()` den Python-Objekt-Repr liefert, nicht den Key-String. Immer `row_key.value` verwenden.
- **`NodeHighlighted` vs `NodeSelected`**: Pfeil-Navigation im Tree feuert `Tree.NodeHighlighted`, nicht `Tree.NodeSelected`. Beide Events werden in `AddressSpace` behandelt, damit `_selected_tree_node` auch bei Tastatur-Navigation aktuell bleibt.
- **Graph node_id Lookup**: `DataTableView._node_ids` mappt `str(node_id) → asyncua NodeId Objekt`. `get_node_id(row_key)` akzeptiert `RowKey` oder String und liest intern `.value`.
