"""
Worker thread handler for non-blocking GUI operations.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
import traceback
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class SpawnWorker(QObject):
    finished = Signal(object)
    error = Signal(Exception, str)  # Emits (Exception, traceback_str)

    def __init__(
        self,
        invoke_function: Callable,
        invoke_args: tuple[Any, ...] = (),
        invoke_kwargs: dict[str, Any] | None = None,
    ):
        super().__init__()
        self._invoke_function = invoke_function
        self._invoke_args = invoke_args or ()
        self._invoke_kwargs = invoke_kwargs or {}

    @Slot()
    def run(self):
        try:
            result = self._invoke_function(*self._invoke_args, **self._invoke_kwargs)
            self.finished.emit(result)
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.exception("Worker operation failed in background thread.")
            self.error.emit(e, tb_str)
