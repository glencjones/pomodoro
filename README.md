# Pomodoro CLI Tool (Grouped Version)

Advanced Pomodoro CLI timer supporting:
- Multiple tasks
- Grouped reporting (by key or phase)
- Special "Main" group for single tasks
- Day/Week/Month reporting
- Monitor live session from another terminal

## Features

- Start, Pause, Resume, Finish tasks
- Track phases and keys (e.g., JIRA tickets)
- Group reports by `key` or `phase`
- Special "Main" group if only one task in a category
- See Day number of the year
- Simple CLI, single Python script

## Usage

```bash
# Start a new task
python3 src/pomodoro.py start --task "Write Daily Report" --phase "Daily" --key "DAILY-1"

# Resume a paused task with monitor
python3 src/pomodoro.py resume --key "DAILY-1" --monitor

# List current active tasks
python3 src/pomodoro.py list

# Group report by phase
python3 src/pomodoro.py report --period day --group phase

# Monitor running task from another terminal
python3 src/monitor.py
```

## Requirements
- Python 3.8+
- Install `tabulate` with `pip install tabulate`

## Emacs Projectile setup
- `.projectile` file included
- Place under `src/` directory

---
MIT License © 2025
