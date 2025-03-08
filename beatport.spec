# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['paste.txt'],  # Your main Python file
    pathex=[],
    binaries=[],
    datas=[('preferences.json', '.')],
    hiddenimports=[
        'selenium',
        'webdriver_manager',
        'webdriver_manager.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.support',
        'selenium.webdriver.support.wait',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Beatport Track Finder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)