# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file para generar ejecutable limpio de historiador
# 
# Uso: pyinstaller historiador-clean.spec --clean
#
# Este spec genera un ejecutable SIN herramientas de desarrollo,
# reduciendo el tamaño de ~83MB a ~51MB

# Exclusiones para reducir tamaño (herramientas de desarrollo)
dev_tools_excludes = [
    'pytest',
    'pylint', 
    'black',
    'coverage',
    'isort',
    'responses',
    'freezegun',
    'faker',
    'pre_commit',
]

# Exclusiones adicionales para optimizar tamaño
optional_excludes = [
    'matplotlib',
    'scipy', 
    'IPython',
    'jupyter',
    'notebook',
    'tkinter',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'PIL.ImageQt',
    'pandas.plotting._matplotlib',
    'pandas.io.html',
    'pandas.io.sql', 
    'pandas.io.sas',
    'pandas.io.spss',
    'pandas.io.stata',
    'numpy.distutils',
    'numpy.testing',
]

all_excludes = dev_tools_excludes + optional_excludes

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env.example', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=all_excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

import os

# Detectar plataforma y asignar nombre apropiado
import sys
if sys.platform.startswith('win'):
    executable_name = 'historiador.exe'
else:
    executable_name = 'historiador'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=executable_name.replace('.exe', ''),  # PyInstaller añade .exe automáticamente en Windows
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,              # Eliminar símbolos de debug
    upx=False,               # UPX compresión (cambiar a True si está disponible)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
