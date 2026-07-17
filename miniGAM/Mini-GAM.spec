# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

datas_list = [('core', 'core')]
hidden_imports_list = [
    'pandas',
    'openpyxl',
    'pyautogui',
    'pynput',
    'pynput.mouse._win32',
    'pynput.keyboard._win32',
    'pyperclip',
    'PIL',
    'PIL.ImageGrab',
    'cv2',
    'pytesseract',
    'rapidocr_onnxruntime',
    'pyclipper',
    'shapely',
    'onnxruntime',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog'
]

try:
    datas_list += collect_data_files('rapidocr_onnxruntime')
    hidden_imports_list += collect_submodules('rapidocr_onnxruntime')
except Exception:
    pass

a = Analysis(
    ['Mini-GAM.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=hidden_imports_list,
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
    name='Mini-GAM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Mini-GAM_Pendrive',
)
