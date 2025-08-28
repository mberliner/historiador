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
    'numpy.distutils',
    'numpy.testing',
]

all_excludes = dev_tools_excludes + optional_excludes

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env.example', '.')],
    hiddenimports=[
        'numpy.core._multiarray_tests',
        'ssl',
        '_ssl',
        'urllib3',
        'requests',
        'certifi',
    ],
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

# Detectar plataforma y configurar opciones apropiadas
import sys

if sys.platform.startswith('win'):
    executable_name = 'historiador.exe'
    # En Windows, strip no está disponible por defecto y causa warnings
    strip_enabled = False
    upx_enabled = False  # UPX raramente disponible en Windows
else:
    executable_name = 'historiador'
    # En Linux/Mac, strip está disponible y ayuda a reducir tamaño
    strip_enabled = True
    upx_enabled = False  # Cambiar a True si UPX está instalado

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
    strip=strip_enabled,     # Condicional: True en Linux/Mac, False en Windows
    upx=upx_enabled,         # Condicional: False por defecto, configurable por plataforma
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
