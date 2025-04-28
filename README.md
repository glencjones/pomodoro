# Pomodoro CLI Tool Final

## Running

```bash
python src/pomodoro.py start --task "Fix login bug" --phase "Coding" --key "PROJ-1234"
python src/pomodoro.py list
python src/monitor.py
```

## Org-mode Capture

Capture into `pomodoro-capture.org` with entries like:

```org
* Pomodoro Sessions
** TODO Fix login bug
:PROPERTIES:
:Key: PROJ-1234
:Phase: Coding
:Started: [2025-04-27 Sun 14:00]
:Duration: 25 min
:END:
```

Optional Emacs org-capture snippet:

```elisp
(setq org-capture-templates
      '(("p" "Pomodoro" entry
         (file+headline "~/path/to/pomodoro-capture.org" "Pomodoro Sessions")
         "* TODO %^{Task}\n:PROPERTIES:\n:Key: %^{Key}\n:Phase: %^{Phase|Coding|Testing|Admin}\n:Started: %U\n:Duration: %^{Duration|25} min\n:END:\n")))
```

## Building

```bash
make package
```

Binary will appear under `dist/`.

## Cleaning

```bash
make clean
```