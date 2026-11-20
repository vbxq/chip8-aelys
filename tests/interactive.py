#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument('--elyra', default='elyra')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
env = dict(os.environ, DISPLAY=':99', SDL_AUDIODRIVER='dummy')
with tempfile.TemporaryDirectory(prefix='chip8-keyboard-') as directory:
    work = Path(directory)
    rom = work / 'key.ch8'
    rom.write_bytes(bytes.fromhex('6000 6100 F20A F229 D015 120A'))
    snapshot = work / 'display.pgm'
    command = [args.elyra, 'run', '-ae.jit=on', str(root / 'main.elyra'), str(rom), '--scale', '2', '--screenshot', str(snapshot)]
    proc = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        window = None
        for _ in range(100):
            found = subprocess.run(['xdotool', 'search', '--pid', str(proc.pid), '--name', '^Elyra CHIP-8$'], env=env, capture_output=True, text=True)
            if found.returncode == 0:
                window = found.stdout.splitlines()[-1]
                break
            if proc.poll() is not None:
                raise AssertionError(proc.stdout.read())
            time.sleep(0.05)
        assert window, 'SDL window was not created'
        subprocess.run(['xdotool', 'windowfocus', '--sync', window], env=env, check=True)
        time.sleep(0.15)
        subprocess.run(['xdotool', 'keydown', 'q'], env=env, check=True)
        time.sleep(0.1)
        subprocess.run(['xdotool', 'keyup', 'q'], env=env, check=True)
        time.sleep(0.15)
        subprocess.run(['xdotool', 'key', 'Escape'], env=env, check=True)
        stdout, _ = proc.communicate(timeout=10)
        assert proc.returncode == 0, stdout
        expected = bytearray(2048)
        for y, row in enumerate([0x90, 0x90, 0xF0, 0x10, 0x10]):
            for x in range(8):
                expected[y * 64 + x] = 255 if row & (0x80 >> x) else 0
        assert snapshot.read_bytes() == b'P5\n64 32\n255\n' + expected, stdout
        print(stdout, end='')
        print('PASS: real X11 Q input -> CHIP-8 key 4 -> exact glyph framebuffer; Escape exits')
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
