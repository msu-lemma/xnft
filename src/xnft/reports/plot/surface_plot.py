"""
Handle xnft 2d plotting actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.

TODO: Add colormap selection (based on type of scale user selected, e.g., cyclic for phase)
"""

import logging
from collections import namedtuple
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np
import pyqtgraph as pg
import unyt
import xarray as xr

# import scipy.spatial.qhull as qhull
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from quantiphy import Quantity
from scipy.interpolate import griddata  # , CloughTocher2DInterpolator

from ...common.enums import CoordinateSystemType
from ...project.nodes.fields import FieldNode
from .functions.field_components import FieldComponent
from .functions.field_quantities import FieldQuantities, FieldQuantity
from .functions.functions import PlotFunction, PlotFunctions
from .functions.normalizations import PlotNorm, PlotNorms
from .functions.scales import PlotScale
from .helpers.coordinate_transforms import phitheta_to_unit

logger = logging.getLogger(__name__)


AxisData = namedtuple("AxisData", ("values", "label", "units"))

GradientState = dict[str, Any]


@dataclass
class SurfacePlot2DParameters:
    source: FieldNode
    field_quantity: FieldQuantity
    field_component: FieldComponent
    plot_domain: CoordinateSystemType

    applicate_function: PlotFunction
    applicate_scale: PlotScale
    applicate_norm: PlotNorm

    selected_frequency: float

    gradient_cmap: str | None = "CET-L3"
    cyclic_gradient_cmap: str | None = "CET-C2"

    gradient_state: GradientState | None = None
    cyclic_gradient_state: GradientState | None = None

    def serialize(self):
        return {
            "field_quantity": self.field_quantity.name,
            "field_component": self.field_component.name,
            "plot_domain": self.plot_domain.name,
            "applicate_function": self.applicate_function.name,
            "applicate_scale": self.applicate_scale.name,
            "frequency": Quantity(self.selected_frequency, "Hz"),
        }


class Plot2D(QWidget):
    # Mapping of valid source coordinates to plotting domain
    __coordinate_domains__: ClassVar[
        dict[CoordinateSystemType, Collection[CoordinateSystemType]]
    ] = {
        CoordinateSystemType.SPHERICAL: (
            CoordinateSystemType.SPHERICAL,
            CoordinateSystemType.DIRECTION_COSINE,
            # CoordinateSystemType.SPHERICAL_AZEL,
        ),
        CoordinateSystemType.CARTESIAN: (CoordinateSystemType.CARTESIAN,),
    }

    def __init__(
        self,
        report_node,
        coordinates_type=CoordinateSystemType.SPHERICAL,
        parent=None,
    ):
        """
        Parameters
        ----------
        field : xr.Dataset
            Far field dataset containing E and H fields and respective
            components.
        coordinates_type : str
            Coordinate system type to plot in.
        """
        super().__init__(parent)

        if coordinates_type not in self.__coordinate_domains__:
            raise ValueError(
                f"Plot coordinates must be one of {[x.name for x in self.__coordinate_domains__]},"
                f" got {coordinates_type.name}"
            )

        self.report_node = report_node
        self.field_node = report_node.fields[0]
        self.last_plot_domain = coordinates_type

        # == Add control widgets ==

        layout_controls = QVBoxLayout()
        layout_controls.setContentsMargins(0, 0, 0, 0)
        layout_controls.setSpacing(4)

        # -- Add Frequency Selection --
        self.lw_frequency_range = QListWidget()
        self.lw_frequency_range.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )

        layout_controls.addWidget(QLabel("Frequency"))
        layout_controls.addWidget(self.lw_frequency_range)

        # -- Add Field Quantity Selection --

        self.cb_field_quantity = QComboBox()
        self.cb_field_quantity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_controls.addWidget(QLabel("Field Quantity"))
        layout_controls.addWidget(self.cb_field_quantity)

        # -- Add Field Component Selection --

        self.cb_field_component = QComboBox()
        self.cb_field_component.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_controls.addWidget(QLabel("Field Component"))
        layout_controls.addWidget(self.cb_field_component)

        # -- Add Coordinates Selection --

        self.cb_plot_domain = QComboBox()
        self.cb_plot_domain.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_controls.addWidget(QLabel("Domain"))
        layout_controls.addWidget(self.cb_plot_domain)

        # -- Add Function Selection --

        self.cb_plot_function = QComboBox()
        self.cb_plot_function.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_controls.addWidget(QLabel("Function"))
        layout_controls.addWidget(self.cb_plot_function)

        # -- Add Scale Selection --

        self.cb_plot_scale = QComboBox()
        self.cb_plot_scale.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_controls.addWidget(QLabel("Scale"))
        layout_controls.addWidget(self.cb_plot_scale)

        # -- Add Normalization Selection --

        self.cb_plot_norm = QComboBox()
        self.cb_plot_norm.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_controls.addWidget(QLabel("Normalization"))
        layout_controls.addWidget(self.cb_plot_norm)

        # == Update Plotting Options ==

        self._update_frequency_options()
        self.lw_frequency_range.setCurrentRow(0)

        self._update_report_field_quantities()
        self._update_report_field_components()
        self._update_plotting_domain_options()

        self._update_plotting_function_options()
        self._update_plotting_scale_options()
        self._update_plotting_norm_options()

        # --- Load/Create Plot Parameters ---
        if isinstance(self.report_node.data, SurfacePlot2DParameters):
            self.plot_parameters = self.report_node.data

            # Update selections from loaded paramters
            # (combobox, value, update_options_function)
            cb_field_map = [
                (
                    self.cb_field_quantity,
                    self.plot_parameters.field_quantity,
                    self._update_report_field_quantities,
                ),
                (
                    self.cb_field_component,
                    self.plot_parameters.field_component,
                    self._update_report_field_components,
                ),
                (
                    self.cb_plot_domain,
                    self.plot_parameters.plot_domain,
                    self._update_plotting_domain_options,
                ),
                (
                    self.cb_plot_function,
                    self.plot_parameters.applicate_function,
                    self._update_plotting_function_options,
                ),
                (
                    self.cb_plot_scale,
                    self.plot_parameters.applicate_scale,
                    self._update_plotting_scale_options,
                ),
                (
                    self.cb_plot_norm,
                    self.plot_parameters.applicate_norm,
                    self._update_plotting_norm_options,
                ),
            ]

            for cb, val, update_cb_options in cb_field_map:
                update_cb_options()
                idx = cb.findData(val)
                if idx != -1:
                    cb.setCurrentIndex(idx)

            # Set frequency selection in list widget
            # Iterate over each item in list by index
            for i in range(self.lw_frequency_range.count()):
                item = self.lw_frequency_range.item(i)
                # Check if data matches selected frequency
                if item.data(Qt.UserRole) == self.plot_parameters.selected_frequency:
                    self.lw_frequency_range.setCurrentItem(item)
                    break

        else:
            plot_parameters = SurfacePlot2DParameters(
                source=self.field_node,
                field_quantity=self.selected_field_quantity,
                field_component=self.selected_field_component,
                plot_domain=self.selected_plot_domain,
                applicate_function=self.selected_field_function,
                applicate_scale=self.selected_field_scale,
                applicate_norm=self.selected_field_norm,
                selected_frequency=self.selected_plot_frequency,
            )
            self.plot_parameters = plot_parameters
            self.report_node.data = self.plot_parameters

        # === Add 2D Field View ===
        self.glw = pg.GraphicsLayoutWidget()
        self.plot = self.glw.addPlot()
        self.vb = self.plot.getViewBox()

        # Store temp plot items for uniformly sampled image and mesh item
        # (pcolormesh is much slower tha imageitem)
        # TODO: replace pcolormesh with interpolated regularly sampled image
        self.image_item = pg.ImageItem()
        # self.mesh_item = pg.PColorMeshItem()

        # Layout
        plot_layout = QVBoxLayout(self)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.glw)

        # Add colorbar
        # TODO: Set colormap dynamically based on units selected
        #       i.e., for cyclic data use cyclic colormap as default
        # self.cmap = self.plot_parameters.cmap

        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.image_item)
        self.glw.addItem(self.hist)
        self.vb.addItem(self.image_item)

        # Add split layout for frequency and plot
        layout = QSplitter(Qt.Orientation.Horizontal)

        layout_controls_widget = QWidget()
        layout_controls_widget.setLayout(layout_controls)
        layout_controls_widget.setMinimumWidth(150)
        layout.addWidget(layout_controls_widget)

        layout_plot_widget = QWidget()
        layout_plot_widget.setLayout(plot_layout)
        layout_plot_widget.setMinimumWidth(150)
        layout.addWidget(layout_plot_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(layout)

        # ---- Connections ----
        self.cb_field_quantity.currentTextChanged.connect(self._update_plot)
        self.lw_frequency_range.itemSelectionChanged.connect(self._update_plot)
        self.cb_field_component.currentTextChanged.connect(self._update_plot)
        self.cb_plot_domain.currentTextChanged.connect(self._update_plot)
        self.cb_plot_function.currentTextChanged.connect(self._update_plot)
        self.cb_plot_norm.currentTextChanged.connect(self._update_plot)
        self.cb_plot_function.currentTextChanged.connect(
            self._update_plotting_scale_options
        )
        self.cb_plot_function.currentTextChanged.connect(
            self._update_plotting_norm_options
        )
        self.cb_plot_scale.currentTextChanged.connect(self._update_plot)

        self.hist.gradient.sigGradientChanged.connect(self._save_state)

        # Draw initial plot
        self._update_plot()

        QTimer.singleShot(0, lambda: layout.setSizes([100, 1000]))

    # --- Properties ---

    @property
    def selected_plot_frequency(self):
        return self.lw_frequency_range.selectedItems()[0].data(Qt.UserRole)

    @property
    def selected_plot_domain(self):
        return self.cb_plot_domain.currentData()

    @property
    def selected_field_quantity(self):
        return self.cb_field_quantity.currentData()

    @property
    def selected_field_component(self):
        return self.cb_field_component.currentData()

    @property
    def selected_field_function(self):
        return self.cb_plot_function.currentData()

    @property
    def selected_field_scale(self):
        return self.cb_plot_scale.currentData()

    @property
    def selected_field_norm(self):
        return self.cb_plot_norm.currentData()

    # --- Private Methods ---

    def _set_lut_gradient(self) -> None:
        if self.selected_field_function == PlotFunctions.MAGNITUDE.value:
            cmap = self.plot_parameters.gradient_cmap
            state = self.plot_parameters.gradient_state
        elif self.selected_field_function == PlotFunctions.PHASE.value:
            cmap = self.plot_parameters.cyclic_gradient_cmap
            state = self.plot_parameters.cyclic_gradient_state
        else:
            return

        if state is not None:
            self.hist.gradient.restoreState(state)
            self.hist.gradient.showTicks(False)

        elif cmap is not None:
            self.hist.gradient.setColorMap(pg.colormap.get(cmap))
            self.hist.gradient.showTicks(False)

    def _update_plotting_function_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_plot_function.count()):
            self.cb_plot_function.removeItem(0)

        for plot_function in PlotFunctions:
            if (
                self.field_node.data.attrs["field_type"]
                in plot_function.value.field_types
            ):
                self.cb_plot_function.addItem(
                    plot_function.value.name, plot_function.value
                )

    def _update_report_field_quantities(self):
        # Remove all items before updating items
        for _ in range(self.cb_field_quantity.count()):
            self.cb_field_quantity.removeItem(0)

        logger.debug(f"field_node.data = {self.field_node.data}")

        field_quantities = FieldQuantities

        newitem_index = 0
        for fc in field_quantities:
            if self.field_node.data.attrs["field_type"] in fc.value.field_types:
                self.cb_field_quantity.addItem(fc.value.name, fc.value)
                self.cb_field_quantity.model().item(newitem_index).setEnabled(
                    fc.value.enabled(self.field_node.data)
                )
                newitem_index += 1

    def _update_report_field_components(self):
        # Remove all items before updating items
        for _ in range(self.cb_field_component.count()):
            self.cb_field_component.removeItem(0)

        if self.selected_field_quantity is not None:
            field_components = self.selected_field_quantity.field_components

            newitem_index = 0
            for fc in field_components:
                # Only add if field type is valid for that function
                if self.field_node.field_type in fc.value.field_types:
                    self.cb_field_component.addItem(fc.value.name, fc.value)
                    self.cb_field_component.model().item(newitem_index).setEnabled(
                        fc.value.enabled
                    )
                    newitem_index += 1

    def _update_plotting_scale_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_plot_scale.count()):
            self.cb_plot_scale.removeItem(0)

        plot_function = self.cb_plot_function.currentData()

        for scale in plot_function.scales:
            self.cb_plot_scale.addItem(scale.value.name, scale.value)

    def _update_plotting_norm_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_plot_norm.count()):
            self.cb_plot_norm.removeItem(0)

        if self.selected_field_quantity is not None:
            field_norms = [x for x in PlotNorms]

            plot_function = self.cb_plot_function.currentData()
            print(plot_function)

            newitem_index = 0
            for fc in field_norms:
                if plot_function in [x.value for x in fc.value.functions]:
                    self.cb_plot_norm.addItem(fc.value.name, fc.value)
                    self.cb_plot_norm.model().item(newitem_index).setEnabled(
                        fc.value.enabled
                    )
                    newitem_index += 1

    def _update_plotting_domain_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_plot_domain.count()):
            self.cb_plot_domain.removeItem(0)

        # Get selected field source coordinates
        source_coordiante_system = self.field_node.data.attrs["coordinate_system"]

        valid_plot_domains = self.__coordinate_domains__[source_coordiante_system]

        for coordinates_domain in valid_plot_domains:
            self.cb_plot_domain.addItem(
                coordinates_domain.value.name, coordinates_domain.value
            )

    def _update_frequency_options(self):
        # Remove all items before updating items
        self.lw_frequency_range.clear()

        frequencies = self.field_node.data.coords["frequency"].values.tolist()

        # Get only unique items
        frequencies = list(set(frequencies))

        frequencies_items = sorted(
            [(str(Quantity(x, units="Hz")), x) for x in frequencies]
        )
        for label, data in frequencies_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lw_frequency_range.addItem(item)

    def _save_state(self):
        self.plot_parameters.field_quantity = self.selected_field_quantity
        self.plot_parameters.field_component = self.selected_field_component
        self.plot_parameters.plot_domain = self.selected_plot_domain
        self.plot_parameters.applicate_function = self.selected_field_function
        self.plot_parameters.applicate_scale = self.selected_field_scale
        self.plot_parameters.applicate_norm = self.selected_field_norm
        self.plot_parameters.selected_frequency = self.selected_plot_frequency
        if self.selected_field_function == PlotFunctions.MAGNITUDE.value:
            self.plot_parameters.gradient_state = self.hist.gradient.saveState()
        if self.selected_field_function == PlotFunctions.PHASE.value:
            self.plot_parameters.cyclic_gradient_state = self.hist.gradient.saveState()

    def _update_plot(self):
        # Set the histogram gradient
        self._set_lut_gradient()

        # _update_plot is called whenever state changes, so call save_state here too
        self._save_state()

        # Compute applicate surface from updated plot parameters
        field_fun_scaled, axis_dict = get_transformed_data(self.plot_parameters)

        if isinstance(field_fun_scaled, xr.DataArray):
            field_fun_scaled = field_fun_scaled.values

        # -- Apply selected coordinate transform --

        # NOTE: Native domain is spherical
        # Direction cosines require nonlinear transformation so we need to use pcolormesh for
        if self.selected_plot_domain == CoordinateSystemType.DIRECTION_COSINE.value:
            # Get phi and theta as numpy arrays
            phi = self.field_node.data.phi.values
            theta = self.field_node.data.theta.values

            phi_grid, theta_grid = np.meshgrid(phi, theta, indexing="ij")
            ux_vals, uy_vals, _ = phitheta_to_unit(phi=phi_grid, theta=theta_grid)

            num_x_samples, num_y_samples = 2048, 2048
            x_idx = np.linspace(ux_vals.min(), ux_vals.max(), num_x_samples)
            y_idx = np.linspace(uy_vals.min(), uy_vals.max(), num_y_samples)
            x_idx_mesh, y_idx_mesh = np.meshgrid(x_idx, y_idx, indexing="ij")

            # TODO/FIXME: implement faster interpolator using pre-computed Delaunay triangulation
            field_fun_scaled = griddata(
                points=np.column_stack([ux_vals.ravel(), uy_vals.ravel()]),
                values=field_fun_scaled.ravel(),
                xi=(x_idx_mesh, y_idx_mesh),
                method="linear",
            )

            self.image_item.setImage(field_fun_scaled)
            self.image_item.setRect((-1, 1, 2, -2))
            self.plot.setLabel("left", text="U<sub>y</sub>", units=None)
            self.plot.setLabel("bottom", text="U<sub>x</sub>", units=None)
            self.vb.setLimits(xMin=-25, yMax=+25, xMax=+25, yMin=-25)
            self.vb.setAspectLocked(True, 1.0)

        else:
            self.vb.setAspectLocked(False)

            abscissa_values = axis_dict["x"].values
            ordinate_values = axis_dict["y"].values

            # Initialize labels
            ordinate_label = axis_dict["y"].label
            abscissa_label = axis_dict["x"].label

            # Map names to symbols
            if ordinate_label.lower() == "theta":
                ordinate_label = "θ"
            if ordinate_label.lower() == "phi":
                ordinate_label = "φ"
            if abscissa_label.lower() == "theta":
                abscissa_label = "θ"
            if abscissa_label.lower() == "phi":
                abscissa_label = "φ"

            yaxis_label = str.title(ordinate_label)
            yaxis_units = axis_dict["y"].units

            xaxis_label = str.title(abscissa_label)
            xaxis_units = axis_dict["x"].units

            axis_scale = 1.0

            # Convert radians to degrees
            if xaxis_units == unyt.radian:
                xaxis_units = unyt.degree
                yaxis_units = unyt.degree
                axis_scale = 180 / np.pi

            self.plot.setLabel("left", text=yaxis_label, units=yaxis_units)
            self.plot.setLabel("bottom", text=xaxis_label, units=xaxis_units)

            # Set image
            self.image_item.setImage(field_fun_scaled)

            # Set extents
            x_range = abscissa_values.max() - abscissa_values.min()
            y_range = ordinate_values.max() - ordinate_values.min()

            upper_left_x = axis_scale * abscissa_values.min()
            upper_left_y = axis_scale * ordinate_values.max()

            width = axis_scale * x_range
            height = -axis_scale * y_range

            # logger.debug((upper_left_x, upper_left_y, width, height))

            self.image_item.setRect((upper_left_x, upper_left_y, width, height))
            self.vb.setLimits(
                xMin=upper_left_x,
                yMax=upper_left_y,
                xMax=upper_left_x + width,
                yMin=upper_left_y + height,
            )

        if self.selected_field_function == PlotFunctions.MAGNITUDE.value:
            # TODO: this should be passed in by the function itself, not special code here
            # Scale the range to clip low long-tail values
            self._autoscale_lut_range()

        # AutoRange after domain changed
        if self.last_plot_domain != self.selected_plot_domain:
            self.vb.autoRange()

        self.last_plot_domain = self.selected_plot_domain

        # Set applicate label on LUT histogram
        field_quantity = self.plot_parameters.field_quantity
        function = self.plot_parameters.applicate_function
        scale = self.plot_parameters.applicate_scale

        applicate_label = f"{function.name_short}({field_quantity.name})"
        applicate_units = scale.unit_modifier(field_quantity.units)

        self.hist.axis.setLabel(applicate_label, units=applicate_units)

    def _autoscale_lut_range(self, min_percentile=20, max_percentile=100):
        low, high = np.nanpercentile(
            self.image_item.image,
            [min_percentile, max_percentile],
        )
        logger.debug(f"autoscale_lut: {low=}, {high=}")
        self.hist.setLevels(low, high)


def get_transformed_data(spp: SurfacePlot2DParameters):
    field_ds = spp.source.data

    if not isinstance(field_ds, xr.Dataset):
        raise TypeError(
            f"SurfacePlot2DParameters.source.data must be of type xarray.Dataset, not {type(field_ds)}"
        )

    if spp.field_component.name in field_ds.coords["component"]:
        component = spp.field_component.name
    else:
        component = field_ds.coords["component"]

    logger.debug(f"{spp.selected_frequency=}")
    logger.debug(f"{spp.field_component=}")

    field_data = field_ds.sel(frequency=spp.selected_frequency, component=component)

    # -- Apply selected component / functions --
    field_scaled = spp.applicate_scale.function(
        spp.applicate_function.function(
            spp.applicate_norm.function(
                spp.field_quantity.function(
                    spp.field_component.function(field_data),
                ),
            ),
            dim=2,
        ),
    )

    # -- Get axis values, labels, and units --
    components = field_ds.coords["component"]

    x_key = components[0].values.item()
    y_key = components[1].values.item()

    axis_dict = {
        "x": AxisData(
            values=field_ds.coords[x_key].values,
            label=x_key.title(),
            units=next(iter(field_ds.attrs["coordinate_units"].values())),
        ),
        "y": AxisData(
            values=field_ds.coords[y_key].values,
            label=y_key.title(),
            units=list(field_ds.attrs["coordinate_units"].values())[1],
        ),
    }

    return field_scaled, axis_dict
