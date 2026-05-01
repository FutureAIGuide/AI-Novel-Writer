# PyInstaller spec for a macOS-friendly local studio bundle.
# Build from repo root:
#   pip install -e ".[studio,packaging]"
#   pyinstaller packaging/pyinstaller.spec
#
# The resulting app runs the FastAPI studio (default port 8765).

from pathlib import Path

block_cipher = None
# SPECPATH is the directory containing this .spec (injected by PyInstaller).
root = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(root / "packaging" / "studio_entry.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "novel_writer" / "studio" / "static"), "novel_writer/studio/static"),
    ],
    hiddenimports=["uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto", "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto", "uvicorn.lifespan", "uvicorn.lifespan.on"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ai-novel-writer-studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ai-novel-writer-studio",
)
