"""
Worker thread handler for non-blocking GUI operations.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import traceback

from PySide6.QtCore import QObject, Signal, Slot


class SpawnWorker(QObject):
    finished = Signal(dict)
    error = Signal(Exception)

    def __init__(self, invoke_function, invoke_kwargs=None):
        super().__init__()
        self._invoke_function = invoke_function
        self._invoke_kwargs = invoke_kwargs or {}

    @Slot()
    def run(self):
        try:
            result = self._invoke_function(**self._invoke_kwargs)
            self.finished.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.error.emit(e)
