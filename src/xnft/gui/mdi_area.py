"""
Custom QMdiArea with logos.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

from PySide6.QtCore import (
    Qt,
    QRect,
    QRectF,
    QSizeF,
)
from PySide6.QtGui import (
    QPainter,
    QImage,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QMdiArea

import logging

logger = logging.getLogger(__name__)


class QMdiAreaWatermark(QMdiArea):
    """Custom QMdiArea to display watermark."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._emrg_logo_path = "src/xnft/resources/logos/emrg_logo_vector.svg"
        self._lemma_logo_path = (
            "src/xnft/resources/logos/lemma_logo_transparent.png"
        )

        self._emrg_logo = QPixmap.fromImage(QImage(self._emrg_logo_path))
        self._lemma_logo = QPixmap.fromImage(QImage(self._lemma_logo_path))

        self._opacity = 0.5
        self._margin = 12

        self._emrg_target_size = QSizeF(510.2 / 2, 164 / 2)
        self._lemma_target_size = QSizeF(381 / 1.5, 325 / 1.5)

        self._emrg_logo = self._emrg_logo.scaled(
            self._emrg_target_size.toSize(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self._lemma_logo = self._lemma_logo.scaled(
            self._lemma_target_size.toSize(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setOpacity(self._opacity)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Compute lower right corner location for watermarks

        vp_rect = self.viewport().rect()
        emrg_w, emrg_h = (
            self._emrg_target_size.width(),
            self._emrg_target_size.height(),
        )
        emrg_x = vp_rect.right() - emrg_w - self._margin
        emrg_y = vp_rect.bottom() - emrg_h - self._margin
        emrg_target_rect = QRect(emrg_x, emrg_y, emrg_w, emrg_h)

        painter.drawPixmap(emrg_target_rect, self._emrg_logo)

        lemma_w, lemma_h = (
            self._lemma_target_size.width(),
            self._lemma_target_size.height(),
        )
        lemma_x = vp_rect.right() - lemma_w - self._margin
        lemma_y = vp_rect.top() + self._margin
        lemma_target_rect = QRect(lemma_x, lemma_y, lemma_w, lemma_h)

        painter.drawPixmap(lemma_target_rect, self._lemma_logo)

