# Wizard Desktop Reminder

An animated Windows desktop reminder. A little sprite flies across the
screen on a broomstick, hovers, shows a speech-bubble message, then flies
off — no audio, no intrusive popup windows.


## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activation script, run this once first:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```


## Run a reminder manually

```powershell
python main.py --message "Hey! Drink some water."
python main.py --message "Stand up and stretch." --side right
```

## Schedule recurring reminders

Uses Windows' built-in Task Scheduler under the hood.

**One-off / fixed daily time:**
```powershell
python scheduler_setup.py add --name Water --time 10:00 --message "Hey! Drink some water."
python scheduler_setup.py add --name Stretch --time 15:00 --message "Time to stretch!"
```

**Runs at every login, then repeats every N minutes indefinitely** (this
is what makes it start automatically after a restart, with no manual
step):
```powershell
python scheduler_setup.py add-recurring --name WaterReminder --interval 75 --message "Hey! Drink some water."
```

Other commands:
```powershell
python scheduler_setup.py list
python scheduler_setup.py remove --name WaterReminder
```

> Under the hood, `add-recurring` builds a small XML task definition and
> imports it via `schtasks /Create /XML`. This is intentional —
> `schtasks`'s plain flags (`/SC ONLOGON /RI /DU`) don't support
> repetition on a logon trigger; that combination is only exposed through
> the XML format. The Repetition block also has no `<Duration>` on
> purpose — a missing Duration means "repeat forever," and Task
> Scheduler rejects fixed values like `P4Y` (years aren't a valid unit
> there) if you try to cap it artificially.

## Package as a standalone .exe

```powershell
pyinstaller build.spec --noconfirm
```

The built exe lands in `dist\HarryReminder.exe`. Then, in
`scheduler_setup.py`, change:
```python
EXE_PATH = None
```
to:
```python
EXE_PATH = BASE_DIR / "dist" / "HarryReminder.exe"
```
and re-run `remove` + `add-recurring` so the scheduled task launches the
exe instead of `python main.py` — this makes the reminder work even
without Python or the venv installed.

**Updating sprite frames after the exe is already built:** PyInstaller
bundles whatever PNGs exist in `assets/frames/` at build time, so
swapping the files afterward has no effect until you rebuild:
```powershell
Remove-Item -Recurse -Force build, dist
pyinstaller build.spec --noconfirm
```
The scheduled task points at the exe's file path, not a snapshot of its
contents — overwriting `dist\HarryReminder.exe` in place is picked up
automatically, no need to touch Task Scheduler again unless you're also
changing the message, interval, or task name.

## Troubleshooting: reminder didn't appear after a restart

1. **Enable task history first** — Task Scheduler logs nothing by
   default. Open Task Scheduler → Task Scheduler Library → in the
   right-hand Actions pane click **Enable All Tasks History**.
2. Restart (or sign out/in) again, then check the task's **History**
   tab:
   - A logon-trigger event followed by an error/terminated event means
     the trigger fired but the exe failed — usually a missing-asset or
     working-directory issue.
   - No logon-trigger event at all around your sign-in time means the
     trigger itself never fired — a Task Scheduler configuration issue.
3. **Check the task's configured account** on its General tab, under
   Security options. If you sign into Windows with a Microsoft account
   (common on personal machines), make sure it matches the account you
   actually log in with — a mismatch here means the trigger silently
   never fires for your session.
4. As a sanity check independent of scheduling, right-click the task →
   **Run** to confirm the exe itself launches correctly on demand.

## Customize

Everything tunable lives in `config.py`:
- animation timing (fly-in/hover/fly-out durations, frame speed)
- entry side, hover height
- speech bubble font/size/width
- click-through and always-on-top behavior

## Project layout

```
harry_reminder/
├── main.py                     # CLI entry point
├── overlay.py                  # transparent window + animation + bubble
├── config.py                   # all tunable settings
├── generate_placeholder_sprites.py
├── scheduler_setup.py          # Windows Task Scheduler integration
├── build.spec                  # PyInstaller packaging
├── requirements.txt
├── .gitignore
├── LICENSE
└── assets/frames/               # sprite PNG sequence (replace with your own art)
```

