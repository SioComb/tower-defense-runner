# Tower Defense Runner

A pygame prototype of an ad-style lane shooting defense game.

This is not a classic maze or route based tower defense game. Enemies, gates,
weapon crates, and bosses move straight down from the top of the screen. The
player moves the soldier squad left and right along the base area and lines up
straight upward shots.

## Screenshot

No screenshot is included yet.

```text
[ screenshot placeholder ]
```

## Setup

Python 3.11 or newer, Windows 11, uv, and a virtual environment are assumed.

```powershell
uv venv
.venv\Scripts\activate
uv sync
```

## Run

```powershell
uv run python -m tower_defense_runner.main
```

Or:

```powershell
uv run tower-defense-runner
```

## Controls

- `A` or `Left Arrow`: Move the soldier squad left
- `D` or `Right Arrow`: Move the soldier squad right
- `SPACE`: Pause / resume
- `R`: Restart after game over
- `ESC`: Quit

## Game Overview

- The base is at the bottom of the battle lane.
- Enemies move straight down and damage the base when they reach the base line.
- Soldiers fire straight upward only. There is no auto aim and no homing.
- Move the squad left and right to line up shots.
- Gates such as `+5`, `+10`, and `x2` gain charge when hit by bullets.
- A charged gate activates and increases the soldier count, then disappears.
- Weapon crates lose HP when hit. Destroying one raises the weapon level.
- Weapon levels improve bullet damage, bullet speed, and fire rate.
- Every fifth wave spawns a large boss with high HP.

## Directory Structure

```text
tower_defense_runner/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ .gitignore
├─ src/
│  └─ tower_defense_runner/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ settings.py
│     ├─ game.py
│     ├─ entities.py
│     ├─ weapons.py
│     ├─ waves.py
│     └─ ui.py
└─ tests/
   └─ test_basic.py
```

## Future Ideas

- Additional enemy types
- Additional weapon types
- Additional gate effects
- More stages
- Save data
- Sound
- Particle effects
- Menu screen
- Mobile-style UI

## Credits

Developer: SioComb

Developed with: Codex / ChatGPT 5.5

License: CC0-1.0
