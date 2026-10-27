"""Create an allowlisted static bundle without third-party dependencies."""

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from emotion_lab.server import PUBLIC

destination = ROOT / 'dist'
if destination.is_symlink():
    raise SystemExit('Refusing to replace a linked build directory.')
if destination.exists():
    shutil.rmtree(destination)
for name in PUBLIC:
    source = ROOT / 'web' / name
    if source.is_symlink() or not source.is_file():
        raise SystemExit(f'Public source is missing or linked: {name}')
    target = destination / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
print(f'Built {len(PUBLIC)} static files ({sum(p.stat().st_size for p in destination.rglob("*") if p.is_file()):,} bytes).')
