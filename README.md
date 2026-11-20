<p align="center">
  <img src="screenshot_2.png" width="45%" alt="CHIP-8 display"/>
  <img src="screenshot_1.png" width="45%" alt="CHIP-8 display"/>
</p>

# CHIP-8 in Elyra

A CHIP-8 emulator written in [Elyra](https://github.com/vbxq/elyra), using SDL2 through C FFI.

Requires Elyra 0.22.0 and SDL2.

```bash
elyra main.elyra path/to/game.ch8
```

Without an argument, it loads `rom.ch8`. Escape quits. `--mute` disables sound; `--usage` lists the options.

## Keypad

```
CHIP-8       Keyboard
1 2 3 C      1 2 3 4
4 5 6 D      Q W E R
7 8 9 E      A S D F
A 0 B F      Z X C V
```

Classic CHIP-8 only, without SUPER-CHIP or XO-CHIP.

## Tests

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy elyra test.elyra
```
