"""Graph view widget for time-series variable data."""

import logging
from collections import defaultdict, deque
from time import time

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual_plotext import PlotextPlot

logger = logging.getLogger(__name__)

# Fixed palette so each variable gets a stable color by assignment order.
# Ordered for maximum contrast on dark backgrounds; "black" removed as it is
# invisible against dark terminal themes.
_PLOT_COLORS = (
    "green",
    "cyan",
    "yellow",
    "magenta",
    "red",
    "blue",
    "white",
    "orange",
)


class GraphView(Vertical):
    """Time-series graph for subscribed variables."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_history = defaultdict(lambda: deque(maxlen=100))
        self.node_names: dict = {}
        self.graphed_nodes: set = set()
        # Stable color per node_id so adding/removing other plots doesn't change colors.
        self._node_colors: dict = {}
        self._next_color_index = 0

    def compose(self) -> ComposeResult:
        yield Static(
            "Subscribe to a variable ('s') then press 'g' to graph it",
            id="graph-hint",
        )
        yield PlotextPlot()

    def on_mount(self) -> None:
        self.border_title = "Graph View"
        self.query_one(PlotextPlot).theme = "clear"
        self._update_plot()

    def add_data_point(self, node_id, value, display_name: str) -> None:
        """Add a data point for a node."""
        try:
            numeric_value = float(value)
            self.data_history[node_id].append((time(), numeric_value))
            self.node_names[node_id] = display_name
            if node_id in self.graphed_nodes:
                self._update_plot()
        except (ValueError, TypeError):
            pass

    def toggle_node_graph(self, node_id, display_name: str | None = None) -> bool:
        """Add or remove a node from the graph."""
        if node_id in self.graphed_nodes:
            self.graphed_nodes.remove(node_id)
        else:
            self.graphed_nodes.add(node_id)
            if display_name:
                self.node_names[node_id] = display_name
            # Assign a stable color when first graphed (never reassign).
            if node_id not in self._node_colors:
                self._node_colors[node_id] = _PLOT_COLORS[
                    self._next_color_index % len(_PLOT_COLORS)
                ]
                self._next_color_index += 1
        self._update_plot()
        return node_id in self.graphed_nodes

    def clear_node_data(self, node_id) -> None:
        """Clear data history for a specific node."""
        if node_id in self.data_history:
            del self.data_history[node_id]
        if node_id in self.node_names:
            del self.node_names[node_id]
        if node_id in self.graphed_nodes:
            self.graphed_nodes.remove(node_id)
        self._update_plot()

    def clear_all(self) -> None:
        """Clear all data."""
        self.data_history.clear()
        self.node_names.clear()
        self.graphed_nodes.clear()
        self._node_colors.clear()
        self._next_color_index = 0
        self._update_plot()

    def _update_plot(self) -> None:
        """Update the plot with current data."""
        try:
            hint = self.query_one("#graph-hint")
            plot = self.query_one(PlotextPlot)

            if not self.graphed_nodes:
                hint.display = True
                plot.display = False
                return

            hint.display = False
            plot.display = True
            plt = plot.plt
            plt.clear_figure()
            plt.title("OPC UA Variable Time Series")
            plt.xlabel("Time (seconds, 0 = latest)")
            plt.ylabel("Value")

            # Common "now" so all series align with latest at right edge.
            all_ts = [
                t
                for node_id in self.graphed_nodes
                if node_id in self.data_history
                for t, _ in self.data_history[node_id]
            ]
            t_now = max(all_ts) if all_ts else time()
            t_oldest = min(all_ts) if all_ts else t_now
            x_min = t_oldest - t_now
            x_max = 0.0
            if x_min >= x_max:
                x_min = -1.0

            plots_added = 0
            for node_id in self.graphed_nodes:
                if node_id in self.data_history and self.data_history[node_id]:
                    data = list(self.data_history[node_id])
                    times = [t - t_now for t, _ in data]
                    values = [v for _, v in data]
                    label = self.node_names.get(node_id, str(node_id))
                    color = self._node_colors.get(node_id, _PLOT_COLORS[0])
                    plt.plot(times, values, label=label, marker="braille", color=color)
                    plots_added += 1

            if plots_added > 0:
                plt.xlim(x_min, x_max)
            else:
                plt.text("Waiting for data...", x=0.5, y=0.5)

            plot.refresh()
        except Exception as e:
            logger.error("Error updating plot: %s", e, exc_info=True)
