# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['c:\\Users\\81203\\Desktop\\浏览脚本\\网站访问工具.py'],
    pathex=[],
    binaries=[],
    datas=[('c:\\Users\\81203\\Desktop\\浏览脚本\\venv\\Lib\\site-packages\\ttkbootstrap', 'ttkbootstrap'), ('c:\\Users\\81203\\Desktop\\浏览脚本\\venv\\Lib\\site-packages\\seleniumwire\\ca.crt', 'seleniumwire')],
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
    name='网站访问工具',
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
