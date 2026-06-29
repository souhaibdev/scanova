# -*- mode: python ; coding: utf-8 -*-

import glob
import os

translation_datas = [(path, 'translations') for path in glob.glob(os.path.join('translations', '*'))]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui/scanova-removebg-preview.png', 'ui'), ('logo.ico', '.')] + translation_datas,
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
    a.binaries,
    a.datas,
    [],
    name='Scanova',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
)
