# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('stocks.csv', '.'), ('ai_brain.json', '.'), ('models', 'models'), ('reports', 'reports'), ('cache', 'cache'), ('stock_ai_analysis', 'stock_ai_analysis'), ('errors_傳統產業.txt', '.'), ('errors_科技股.txt', '.'), ('errors_能源股.txt', '.'), ('errors_虛擬貨幣股.txt', '.'), ('errors_金融股.txt', '.')],
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
    name='app',
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
)
