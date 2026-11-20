#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys
sys.dontwritebytecode = True
from opcode_oracle import corpus

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--elyra', default='elyra')
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='chip8-tests-') as directory:
    work = Path(directory)
    for source in ROOT.glob('*.elyra'):
        shutil.copy2(source, work / source.name)
    (work / 'test_oracle.elyra').write_text(corpus())
    for name in ['cpu', 'sdl', 'oracle']:
        if name != 'oracle':
            shutil.copy2(ROOT / 'tests' / f'{name}.elyra', work / f'test_{name}.elyra')
        for flags in [[], ['-ae.jit-sync=on'], ['-ae.jit=on', '-ae.gc-stress=on', '-ae.gc-verify=on']]:
            command = [args.elyra, 'run', *flags, str(work / f'test_{name}.elyra')]
            print('$', ' '.join(command), flush=True)
            subprocess.run(command, check=True, timeout=60, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))

subprocess.run([sys.executable, str(ROOT / 'tests/application.py'), '--elyra', args.elyra], check=True, timeout=90)
