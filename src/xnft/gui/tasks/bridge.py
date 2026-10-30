"""
Module providing communication between worker and main thread.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class TaskBridge(QObject):
    """
    Bridge object residing on the Main Thread.
    Receives signals from background workers and marshals calls safely to the UI thread.
    """

    def __init__(self, thread, worker, on_finished, on_error, main_window):
        super().__init__(
            main_window
        )  # Parented to MainWindow -> belongs to Main Thread
        self.thread = thread
        self.worker = worker
        self.on_finished = on_finished
        self.on_error = on_error
        self.main_window = main_window

    @Slot(object)
    def handle_finished(self, result):
        try:
            if self.on_finished:
                self.on_finished(result)
        finally:
            self._cleanup()

    @Slot(Exception, str)
    def handle_error(self, exc, tb_str):
        try:
            logger.error(f"Task error: {exc}\n{tb_str}")
            if self.on_error:
                self.on_error(exc, tb_str)
            else:
                self.main_window.statusBar().showMessage(f"Error: {exc}")
                QMessageBox.critical(
                    self.main_window,
                    "Task Error",
                    f"Operation failed with error:\n\n{exc}\n\nCheck log for details.",
                )
        finally:
            self._cleanup()

    def _cleanup(self):
        self.main_window._on_task_completed(self.thread)
        self.thread.quit()
        self.worker.deleteLater()
        self.thread.deleteLater()
        self.deleteLater()
