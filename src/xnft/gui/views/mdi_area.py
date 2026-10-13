"""
Custom QMdiArea with logos.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from importlib.resources import files

from PySide6.QtCore import (
    QPointF,
    QRectF,
    QSize,
    QSizeF,
    Qt,
)
from PySide6.QtGui import (
    QImage,
    QPainter,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QMdiArea

logger = logging.getLogger(__name__)


class QMdiAreaWatermark(QMdiArea):
    """Custom QMdiArea to display watermark."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # self._emrg_logo_path = "src/xnft/resources/logos/emrg_logo_vector.svg"
        # self._lemma_logo_path = "src/xnft/resources/logos/lemma_logo_transparent.png"

        self._emrg_logo_path = str(
            files("xnft.resources.logos").joinpath("emrg_logo_vector.svg"),
        )

        self._lemma_logo_path = str(
            files("xnft.resources.logos").joinpath("lemma_logo_transparent.png"),
        )

        self._emrg_logo = QSvgRenderer(self._emrg_logo_path)
        self._lemma_logo = QPixmap.fromImage(QImage(self._lemma_logo_path))

        self._opacity = 0.5
        self._margin = 12

        self._emrg_target_size = QSizeF(510.2 / 2, 164 / 2)
        self._lemma_target_size = QSizeF(381 / 1.5, 325 / 1.5)

        self._oversample_ratio = 2.0

        dpr = self.devicePixelRatioF() * self._oversample_ratio

        self._emrg_logo_pixmap = self._svg_to_pixmap(
            self._emrg_logo,
            self._emrg_target_size,
            dpr,
        )

        self._lemma_logo_pixmap = self._scale_pixmap(
            self._lemma_logo,
            self._lemma_target_size,
            dpr,
        )

    def _scale_pixels(self, size: QSizeF, dpr: float) -> QSize:
        """Compute QSize in screen pixels"""
        return QSize(round(size.width() * dpr), round(size.height() * dpr))

    def _svg_to_pixmap(
        self,
        renderer: QSvgRenderer,
        size: QSizeF,
        dpr: float,
    ) -> QPixmap:
        pixmap = QPixmap(self._scale_pixels(size, dpr))
        pixmap.fill(Qt.transparent)
        pixmap.setDevicePixelRatio(dpr)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        renderer.render(painter, QRectF(0, 0, size.width(), size.height()))
        painter.end()

        return pixmap

    def _scale_pixmap(self, pixmap: QPixmap, size: QSizeF, dpr: float) -> QPixmap:
        scaled = pixmap.scaled(
            self._scale_pixels(size, dpr),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(dpr)
        return scaled

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setOpacity(self._opacity)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        vp_rect = self.viewport().rect()

        # Add EMRG logo
        emrg_w = self._emrg_target_size.width()
        emrg_h = self._emrg_target_size.height()
        emrg_x = vp_rect.right() - emrg_w - self._margin
        emrg_y = vp_rect.bottom() - emrg_h - self._margin

        painter.drawPixmap(QPointF(emrg_x, emrg_y), self._emrg_logo_pixmap)

        # Add LEmmA logo
        lemma_w = self._lemma_target_size.width()
        # lemma_h = self._lemma_target_size.height()
        lemma_x = vp_rect.right() - lemma_w - self._margin
        lemma_y = vp_rect.top() + self._margin

        painter.drawPixmap(QPointF(lemma_x, lemma_y), self._lemma_logo_pixmap)
