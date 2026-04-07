"""
Handle xnft 2d plotting actions.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.

TODO: Add colormap selection (based on type of scale user selected)
TODO: Add plot normalization
    - Source units (unnormalized)
    - Relative to local maxima (simply the peak value)
    - Relative to global maxima (across all frequencies)
"""

import logging
import numpy as np
import pyqtgraph as pg
import xarray as xr
import unyt
from scipy.interpolate import griddata, CloughTocher2DInterpolator
import scipy.spatial.qhull as qhull

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QSplitter,
    QSizePolicy,
    QComboBox,
    QFormLayout,
    QLabel,
)
from ..enums import CoordinateSystemType, Units, FieldType

from .functions import PlotFunctions
from .scales import PlotScales
from ..coordinate_transforms import phitheta_to_unit

from quantiphy import Quantity

logger = logging.getLogger(__name__)

# TODO: this should be moved elsewhere
pg.setConfigOption("useNumba", True)


class Plot2D(QWidget):
    # Mapping of valid source coordinates to plotting domain
    __coordinate_domains__ = {
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

        if coordinates_type not in self.__coordinate_domains__.keys():
            raise ValueError(
                f"Plot coordinates must be one of {[x.name for x in self.__coordinate_domains__.keys()]},"
                f" got {coordinates_type.name}"
            )

        self.field = report_node.fields[0]
        self.last_domain = coordinates_type

        # == Add control widgets ==

        layout_controls = QVBoxLayout()
        layout_controls.setContentsMargins(0, 0, 0, 0)
        layout_controls.setSpacing(4)

        # -- Add Frequency Selection --
        self.lw_frequency_range = QListWidget()
        self.lw_frequency_range.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout_controls.addWidget(QLabel("Frequency"))
        layout_controls.addWidget(self.lw_frequency_range)

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

        # == Update Plotting Options ==

        self._update_frequency_options()
        self.lw_frequency_range.setCurrentRow(0)

        self._update_report_field_components()
        self._update_plotting_domain_options()

        self._update_plotting_function_options()
        self._update_plotting_scale_options()

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
        self.cmap = pg.colormap.get("viridis")

        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.image_item)
        self.hist.gradient.loadPreset("viridis")
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
        self.lw_frequency_range.itemSelectionChanged.connect(self._update_plot)
        self.cb_field_component.currentTextChanged.connect(self._update_plot)
        self.cb_plot_domain.currentTextChanged.connect(self._update_plot)
        self.cb_plot_function.currentTextChanged.connect(self._update_plot)

        self.cb_plot_function.currentTextChanged.connect(self._update_plotting_scale_options)
        self.cb_plot_scale.currentTextChanged.connect(self._update_plot)

        # Draw initial plot
        self._update_plot()

        QTimer.singleShot(0, lambda: layout.setSizes([100, 1000]))

    def _update_plotting_function_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_plot_function.count()):
            self.cb_plot_function.removeItem(0)

        for plot_function in PlotFunctions:
            print(self.field.data.attrs)
            print(plot_function)
            if self.field.data.attrs['field_type'] in plot_function.value.field_types:
                self.cb_plot_function.addItem(plot_function.value.name, plot_function)

    def _update_report_field_components(self):
        # Remove all items before updating items
        for _ in range(self.cb_field_component.count()):
            self.cb_field_component.removeItem(0)

        # logger.debug(self.field.data)

        field_components = ["All"]
        field_components += self.field.data.coords["component"].data.tolist()

        self.cb_field_component.addItems(field_components)

    def _update_plotting_scale_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_plot_scale.count()):
            self.cb_plot_scale.removeItem(0)

        plot_function = self.cb_plot_function.currentData()

        for scale in plot_function.value.scales:
            self.cb_plot_scale.addItem(scale.value.name, scale)

    def _update_plotting_domain_options(self):
        # Remove all items before updating items
        for _ in range(self.cb_plot_domain.count()):
            self.cb_plot_domain.removeItem(0)

        # Get selected field source coordinates
        source_coordiante_system = self.field.data.attrs["coordinate_system"]

        valid_plot_domains = self.__coordinate_domains__[source_coordiante_system]

        for coordinates_domain in valid_plot_domains:

            self.cb_plot_domain.addItem(coordinates_domain.value.name, (coordinates_domain,))

    def _update_frequency_options(self):
        # Remove all items before updating items
        self.lw_frequency_range.clear()

        frequencies = self.field.data.coords["frequency"].values.tolist()

        # Get only unique items
        frequencies = list(set(frequencies))

        frequencies_items = sorted([(str(Quantity(x, units="Hz")), x) for x in frequencies])
        for label, data in frequencies_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, data)
            self.lw_frequency_range.addItem(item)

    def _update_plot(self):
        # Only one item can be selected at a time
        selected_frequency = self.lw_frequency_range.selectedItems()[0].data(Qt.UserRole)

        cb_component = self.cb_field_component.currentText()
        if cb_component in self.field.data.coords["component"]:
            component = cb_component
        else:
            component = self.field.data.coords["component"]

        logger.debug(f"{component=}")

        field_data = self.field.data.sel(frequency=selected_frequency, component=component)

        # -- Apply selected plotting function --
        plot_function = self.cb_plot_function.currentData().value.function
        logger.debug(plot_function)

        field_fun = plot_function(field_data["E"])
        logger.debug(f"{field_fun.shape=}")

        if isinstance(field_fun, xr.DataArray):
            field_fun = field_fun.values

        # -- Apply selected scale --

        scale_function = self.cb_plot_scale.currentData().value.function
        logger.debug(plot_function)

        field_fun_scaled = scale_function(field_fun)

        # -- Apply selected coordinate transform --
        # TODO: Add coordinate transform
        selected_domain = self.cb_plot_domain.currentData()[0]
        logger.debug(f"{selected_domain=}")

        # NOTE: Native domain is spherical
        # Direction cosines require nonlinear transformation so we need to use pcolormesh for
        if selected_domain == CoordinateSystemType.DIRECTION_COSINE:

            # Get phi and theta as numpy arrays
            phi = self.field.data.phi.values
            theta = self.field.data.theta.values

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
                method="cubic",
            )

            self.image_item.setImage(field_fun_scaled)
            self.image_item.setRect((-1, 1, 2, -2))
            self.plot.setLabel("left", text="U<sub>y</sub>", units=None)
            self.plot.setLabel("bottom", text="U<sub>x</sub>", units=None)
            self.vb.setLimits(xMin=-25, yMax=+25, xMax=+25, yMin=-25)
            self.vb.setAspectLocked(True, 1.0)

        else:
            self.vb.setAspectLocked(False)

            # Set Labels
            components = self.field.data.coords["component"]

            ordinate = components[1].values.item()
            abscissa = components[0].values.item()

            abscissa_values = self.field.data.coords[abscissa].values
            ordinate_values = self.field.data.coords[ordinate].values

            # Initialize labels
            ordinate_label = ordinate
            abscissa_label = abscissa

            # Map names to symbols
            if ordinate.lower() == 'theta':
                ordinate_label = "θ"
            if ordinate.lower() == 'phi':
                ordinate_label = "φ"
            if abscissa.lower() == 'theta':
                abscissa_label = "θ"
            if abscissa.lower() == 'phi':
                abscissa_label = "φ"

            yaxis_label = str.title(ordinate_label)
            yaxis_units = list(self.field.data.attrs["coordinate_units"].values())[1]

            xaxis_label = str.title(abscissa_label)
            xaxis_units = list(self.field.data.attrs["coordinate_units"].values())[0]

            axis_scale = 1.0

            # Convert radians to degrees
            print(f"{xaxis_units=}", f"{type(xaxis_units)=}")
            if xaxis_units == unyt.radian:
                xaxis_units = unyt.degree
                yaxis_units = unyt.degree
                axis_scale = 180 / np.pi

            self.plot.setLabel("left", text=yaxis_label, units=yaxis_units)
            self.plot.setLabel("bottom", text=xaxis_label, units=xaxis_units)

            # Shift to make abscissa and ordinate centered about zero
            abscissa_midpoint_idx = round(abscissa_values.size / 2)
            logger.debug(f'{abscissa_midpoint_idx=}')
            abscissa_min_idx = np.argmin(np.abs(abscissa_values))
            logger.debug(f'{abscissa_min_idx=}')
            abscissa_roll_idx = abscissa_min_idx - abscissa_midpoint_idx
            logger.debug(f'{abscissa_roll_idx=}')

            ordinate_midpoint_idx = round(ordinate_values.size / 2)
            logger.debug(f'{ordinate_midpoint_idx=}')
            ordinate_min_idx = np.argmin(np.abs(ordinate_values))
            logger.debug(f'{ordinate_min_idx=}')
            ordinate_roll_idx = ordinate_min_idx - ordinate_midpoint_idx
            logger.debug(f'{ordinate_roll_idx=}')

            # Roll phi values in spherical coordinates
            logger.debug(f'{self.field.field_type=}')
            if self.field.field_type == FieldType.FAR:
                roll_val = abscissa_values[abscissa_roll_idx]
                logger.debug(f'{roll_val=}')
                abscissa_values = abscissa_values - roll_val
                # ordinate_values = ordinate_values - ordinate_values[ordinate_roll_idx]
            
            # Set image
            self.image_item.setImage(np.roll(field_fun_scaled, (abscissa_roll_idx, ordinate_roll_idx), axis=(0,1)))

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

        # AutoRange after domain changed
        if self.last_domain != selected_domain:
            self.vb.autoRange()

        self.last_domain = selected_domain
