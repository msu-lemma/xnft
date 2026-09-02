"""
Main entrypoint for the packaged application.

Isolates entrypoint from relative imports used in the rest of the package which can't be adequately handled using PyInstaller.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import multiprocessing
import os
import sys

# Handle noconsole mode on Windows
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


def is_worker():
    """
    Comprehensive check to determine if the current process is a
    multiprocessing helper or worker.
    """
    # Check for joblib spawned tasks
    if os.environ.get("LOKY_WORKER") == "1" or os.environ.get("JOBLIB_SPAWNED_PROCESS") == "1":
        return True

    # Check for multiprocessing spawned tasks
    if "--multiprocessing-fork" in sys.argv:
        return True

    # Check for multiprocessing resource tracker tasks
    if "-c" in sys.argv:
        return True

    # Check for multiprocessing named task
    if multiprocessing.current_process().name != "MainProcess":
        return True

    return False


def main():
    # Must be first
    multiprocessing.freeze_support()

    if is_worker():
        sys.exit(0)
    else:
        try:
            multiprocessing.set_start_method("spawn", force=True)
        except RuntimeError:
            pass

        from xnft.gui.app import run_gui

        run_gui()


if __name__ == "__main__":
    main()
