# Experiment scripts

These are the helpers used during the experiment described in the [findings](../README.md).
They wrap Waydroid; they do not create an emulator or provide Fortnite game files.
Restoring these source files does not reinstall Android or restore deleted app data.

## Requirements

Run commands from the repository directory, as your normal desktop user. The scripts
use Python 3's standard library. Waydroid must be installed, and Android must be
initialized and running for app, controller, and Android diagnostic commands.
Opening the UI requires a Wayland desktop. Commands that need root request sudo
in your terminal; do not run the entire launcher as root.

The tested combination was x86-64 Android 13 with an ARM64 native bridge. Other
versions and hardware were not verified. See the README for the tested environment.

## `fortnite-linux`

```bash
./fortnite-linux --help
./fortnite-linux doctor
./fortnite-linux ui
./fortnite-linux play
```

- `doctor` reports host readiness, Waydroid status, Android boot completion, GPU
  properties, supported ABIs, and the native bridge. These checks do not prove that
  Fortnite can complete a match or that its own renderer is hardware accelerated.
- `ui` opens Android's full interface. It may remain attached to the terminal.
- `play` checks that Fortnite is installed and requests its launch.
- `install-apk PATH` installs a local APK through Waydroid. It does not force ARM64.
  The tested Epic Games Store APK crashed when default installation selected x86-64;
  use the explicit ARM64 installation described below for that case.
- `bridge-install` installs the pinned third-party libndk bridge, stops the Android
  session, and restarts the container. It requires `lzip`, supports Android 11/13,
  and refuses to replace an already configured bridge.

### Prepare the bridge installer

Git and Python venv/pip support are needed for this step. Run it before
`./fortnite-linux bridge-install`:

```bash
mkdir -p .external
git clone https://github.com/casualsnek/waydroid_script.git .external/waydroid_script
git -C .external/waydroid_script checkout d5289cfd8929e86e7f0dc89ecadcef8b66930eec
python -m venv .external/waydroid_script/.venv
.external/waydroid_script/.venv/bin/python -m pip install -r .external/waydroid_script/requirements.txt
./fortnite-linux bridge-install
./fortnite-linux ui
```

The [upstream installer](https://github.com/casualsnek/waydroid_script) source is
pinned; its Python dependencies and downloaded translation payloads are not fully
locked by this repository. The installer modifies Android's system or overlay.

### Install the tested Epic Games Store APK as ARM64

Download Epic Games Store from [Epic's Android page](https://www.fortnite.com/mobile/android).
The tested APK was version 1.6.2 (50102). These commands assume Waydroid's default
per-user data location and an APK named `EpicGamesStore.apk` in Downloads:

```bash
mkdir -p "$HOME/.local/share/waydroid/data/waydroid_tmp"
cp "$HOME/Downloads/EpicGamesStore.apk" "$HOME/.local/share/waydroid/data/waydroid_tmp/EpicGamesStore-arm64.apk"
chmod 644 "$HOME/.local/share/waydroid/data/waydroid_tmp/EpicGamesStore-arm64.apk"
sudo waydroid shell -- pm install --abi arm64-v8a /data/waydroid_tmp/EpicGamesStore-arm64.apk
```

The successful test used a clean store installation. Removing an existing store
with `sudo waydroid shell -- pm uninstall com.epicgames.portal` deletes its app data.
Once the store opens, install Fortnite through it. The helper does not download games.

## `connect-controller.py`

```bash
python connect-controller.py
```

Connect one Xbox controller that Linux already detects. With Android running, the
script finds its Linux input node, checks Android's input devices, and publishes a
matching character device inside Android if detection needs repair. It uses a hard
link to generate the `IN_CREATE` event Android's input watcher expects.

It then checks for the controller and saves before/after diagnostics. A success
message confirms Android detection; test the D-pad and buttons in Fortnite as well.

The repair lasts only for the current Android session. It is not a general hotplug
service or keyboard mapper. If reconnecting changes device numbering, restart
Waydroid and rerun the script. More than one detected Xbox controller causes it to stop.

## `diagnose-signin.py`

```bash
python diagnose-signin.py
```

Collects Waydroid status, input devices, windows, activities, and recent logcat output.
It does not change Android settings. Each diagnostic command has a 30-second timeout;
errors and timeouts are recorded alongside the output.

Reports are written to a new `.diagnostics/signin-*` directory. Use them to inspect
input or login failures rather than guessing button coordinates from cropped images.

## `prepare-game.py`

```bash
python prepare-game.py
```

This script changes Android settings. It:

1. Saves the previous debugging settings and persistent USB functions.
2. Disables USB debugging, wireless debugging, and developer options.
3. Removes ADB from the persistent USB functions and stops the ADB service.
4. Collects compositor, display, resolution, thermal, graphics-property, and logcat reports.
5. Verifies debugging is disabled, then force-stops and relaunches Fortnite.

Run it while out of a match. Results are saved under `.diagnostics/graphics-*`.
The settings persist; the saved JSON is a record of the previous values, not an
automatic rollback. Waydroid's local LXC shell still works without ADB.

It does not spoof device identity, change graphics quality, unlock FPS, or fix the
match-removal error. In the test, debugging was successfully disabled but online
play still ended in a kick.

## Diagnostic files

Controller, sign-in, and graphics reports stay in ignored `.diagnostics/` directories.
They can contain account and device information; review them before sharing. APKs,
installer dependencies under `.external/`, and diagnostic logs are not committed.
