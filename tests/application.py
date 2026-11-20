#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--elyra', default='elyra')
args = parser.parse_args()
ENV = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')


def run(arguments, success=True):
    command = [args.elyra, *arguments]
    result = subprocess.run(command, capture_output=True, text=True, env=ENV, timeout=30)
    assert result.returncode == (0 if success else 1), (command, result.returncode, result.stdout, result.stderr)
    return result.stdout + result.stderr


with tempfile.TemporaryDirectory(prefix='chip8-app-') as directory:
    work = Path(directory)
    for source in ROOT.glob('*.elyra'):
        shutil.copy2(source, work / source.name)
    entry = str(work / 'main.elyra')
    rom = work / 'rom.ch8'
    sprite = bytes([0xF0, 0x90, 0x90, 0x90, 0xF0])
    rom.write_bytes(bytes.fromhex('00E0 6000 6100 A20C D015 120A') + sprite)
    snapshot = work / 'snapshot.pgm'
    expected = bytearray(2048)
    for y, row in enumerate(sprite):
        for x in range(8):
            expected[y * 64 + x] = 255 if row & (0x80 >> x) else 0
    for flags in [[], ['-ae.jit-sync=on'], ['-ae.jit=on', '-ae.gc-stress=on', '-ae.gc-verify=on']]:
        output = run(['run', *flags, entry, '--headless', '--cycles', '10', '--screenshot', str(snapshot)])
        assert 'cycles 10, frames 0, pc 522, lit 14' in output, output
        assert snapshot.read_bytes() == b'P5\n64 32\n255\n' + expected
    assert 'Keypad:' in run([entry, '--usage'])
    for invalid in [['--scale', '0'], ['--hz', 'nan'], ['--cycles'], ['--unknown'], ['--cycles', '-1'], ['--scale', '2.5']]:
        assert 'error:' in run([entry, *invalid], success=False)
    assert 'error:' in run([entry, str(work / 'absent.ch8'), '--headless'], success=False)
    for data, message in [(b'', 'empty'), (bytes(3585), '3584'), (bytes.fromhex('5001'), 'invalid opcode')]:
        path = work / 'invalid.ch8'
        path.write_bytes(data)
        assert message in run([entry, str(path), '--headless', '--cycles', '1'], success=False)
    output = run([entry, '--frames', '3', '--scale', '1'])
    assert 'frames 3' in output, output
    artifact = work / 'main.avbc'
    run(['compile', entry, '-o', str(artifact)])
    output = run(['run', str(artifact), '--headless', '--cycles', '10'])
    assert 'cycles 10, frames 0, pc 522, lit 14' in output, output
    output = run(['run', str(artifact), '--frames', '3', '--scale', '1'])
    assert 'frames 3' in output, output
print('PASS: headless/default ROM, exact PGM, CLI errors, bounded ROM input, graphical run and compiled bytecode')
