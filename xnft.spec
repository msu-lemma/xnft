# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
)
from importlib.metadata import version

app_version = version("xnft")

is_mac = sys.platform == "darwin"
is_win = sys.platform == "win32"
is_linux = sys.platform.startswith("linux")

datas = collect_data_files("xnft.resources", includes=["**/*"])

binaries = collect_dynamic_libs("finufft")

a = Analysis(
    ["src/xnft/gui/entrypoint.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="xnft",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    argv_emulation=is_mac,  # macOS specific
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=app_version,
    icon="src/xnft/resources/icons/xnft.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="xnft",
)

if is_mac:
    app = BUNDLE(
        coll,
        name="xnft.app",
        icon="src/xnft/resources/icons/xnft.png",
        bundle_identifier="edu.msu.ece.lemma.xnft",
        version=app_version,
    )
