"""
Data model parameters for 1D plot traces.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pyqtgraph as pg
from numpy.typing import ArrayLike
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen

if TYPE_CHECKING:
    from ....project.nodes.node import DataNode
    from ..functions.field_components import FieldComponent
    from ..functions.field_quantities import FieldQuantity
    from ..functions.functions import PlotFunction
    from ..functions.normalizations import PlotNorm
    from ..functions.scales import PlotScale


@dataclass
class TraceParameters:
    trace_name: str
    pen_color: str = "#ffffff"
    pen_width: float = 1.0
    pen_style: int = Qt.SolidLine.value
    trace_marker_symbol: str | None = None
    source_field: DataNode | None = None
    abscissa: str = ""
    slice_dict: dict[str, ArrayLike] = field(default_factory=dict)
    field_quantity: FieldQuantity | None = None
    field_component: FieldComponent | None = None
    ordinate_function: PlotFunction | None = None
    ordinate_scale: PlotScale | None = None
    field_norm: PlotNorm | None = None

    @property
    def trace_pen(self) -> QPen:
        """Construct live QPen on demand for GUI rendering."""
        return pg.mkPen(
            color=QColor(self.pen_color),
            width=self.pen_width,
            style=Qt.PenStyle(self.pen_style),
        )
