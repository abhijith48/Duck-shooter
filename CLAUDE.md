# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CYBER DUCK // NEON HUNT** — a 3D cyberpunk-themed duck shooting game built with Python, Pygame, and OpenGL (fixed-function pipeline). Single-file game (`duck_game.py`).

## Running

```bash
python3 duck_game.py
```

Dependencies: `pygame`, `PyOpenGL`, `PyOpenGL_accelerate` (optional).

```bash
pip install pygame PyOpenGL
```

## Packaging

Uses PyInstaller. Spec file: `duck_game.spec`.

```bash
pyinstaller duck_game.spec
```

## Architecture

Everything lives in `duck_game.py` (~560 lines). No shaders — all rendering uses OpenGL immediate mode (`glBegin/glEnd`) and GLU quadrics (`gluSphere`, `gluCylinder`, `gluDisk`).

**Key classes:**
- `Game` — main loop, input, scene rendering (sky, city, neon grid, rain), HUD, and game state
- `Duck` — neon cyber-duck with 5 color schemes, glow effects, hit detection via 3D→2D projection (`gluProject`)
- `Particle` — holographic explosion particles on duck hit
- `Building` — procedural city skyline with lit windows and neon accents
- `RainDrop` — rain particle system

**Audio:** Procedurally generated synthwave (bass, arpeggio, pad, rain) using `struct.pack` to build raw PCM buffers for `pygame.mixer.Sound`. No external audio files.

**HUD:** 2D text overlay rendered via `glDrawPixels` on top of the 3D scene using orthographic projection switching.

## Constraints

- OpenGL fixed-function pipeline only (no shaders, no VBOs)
- All scenery data (buildings, grid) is generated once in `Game.__init__()` with seeded RNGs for determinism
- Target 60 FPS — keep draw calls lightweight (low-tessellation quadrics, simple geometry)
- Single-file architecture — no module splits
