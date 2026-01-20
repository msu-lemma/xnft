"""
Custom QMdiArea with logos.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

from PySide6.QtCore import (
    QRect,
    QSizeF,
)
from PySide6.QtGui import (
    QPainter,
    QImage,
)
from PySide6.QtWidgets import QMdiArea

import logging

logger = logging.getLogger(__name__)


class QMdiAreaWatermark(QMdiArea):
    """Custom QMdiArea to display watermark."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._emrg_logo_path = "src/xnft/resources/logos/emrg_logo.svg"
        self._lemma_logo_path = (
            "src/xnft/resources/logos/lemma_logo_transparent.png"
        )

        self._opacity = 0.5
        self._margin = 12
        self._emrg_target_size = QSizeF(510.2 / 2, 164 / 2)
        self._lemma_target_size = QSizeF(381 / 1.5, 325 / 1.5)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setOpacity(self._opacity)

        # Compute lower right corner location for watermarks

        vp_rect = self.viewport().rect()
        emrg_w, emrg_h = (
            self._emrg_target_size.width(),
            self._emrg_target_size.height(),
        )
        emrg_x = vp_rect.right() - emrg_w - self._margin
        emrg_y = vp_rect.bottom() - emrg_h - self._margin
        emrg_target_rect = QRect(emrg_x, emrg_y, emrg_w, emrg_h)

        painter.drawImage(emrg_target_rect, QImage(self._emrg_logo_path))

        lemma_w, lemma_h = (
            self._lemma_target_size.width(),
            self._lemma_target_size.height(),
        )
        lemma_x = vp_rect.right() - lemma_w - self._margin
        lemma_y = vp_rect.top() + self._margin
        lemma_target_rect = QRect(lemma_x, lemma_y, lemma_w, lemma_h)

        painter.drawImage(lemma_target_rect, QImage(self._lemma_logo_path))
