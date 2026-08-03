# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('app', 'app')],
    hiddenimports=['websocket', 'websocket.client', 'PIL', 'barcode', 'qrcode', 'sqlalchemy', 'loguru', 'pystray', 'pkg_resources'],
    hookspath=[],
    hooks=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='gsn-print-service',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='gsn-print-service',
)
