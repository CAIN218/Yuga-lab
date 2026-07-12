# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

datas_comtypes, binaries_comtypes, hiddenimports_comtypes = collect_all('comtypes')
datas_pycaw, binaries_pycaw, hiddenimports_pycaw = collect_all('pycaw')

a = Analysis(
    ['switch_audio.py'],
    pathex=[],
    binaries=binaries_comtypes + binaries_pycaw,
    datas=datas_comtypes + datas_pycaw,
    hiddenimports=[
        'pycaw',
        'pycaw.pycaw',
        'pycaw.constants',
        'pycaw.utils',
    ] + hiddenimports_comtypes + hiddenimports_pycaw,
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
    name='AudioSwitcher',
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
    icon=['app_icon.ico'],
)
