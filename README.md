# Fortnite Android on Linux through Waydroid

An experimental Waydroid setup and a record of a September 9, 2026 test on Arch Linux.
**This did not produce a verified, playable online Fortnite setup.** Installation,
login, rendering, and controller input worked, but the user reported being kicked
from a match with a generic poor-connection/VPN/proxy message. No full online match
was completed successfully.

The exact kick text was not captured. It does not prove that a VPN was present,
that anti-cheat rejected Waydroid, or that the network was the underlying cause.
This repository contains troubleshooting helpers and findings, not a Fortnite port.

## Results

| Stage | Observed result |
| --- | --- |
| Android boot and networking | Worked after narrow UFW rules allowed DHCP, DNS, and forwarding. |
| Epic Games Store | Worked when explicitly installed with the ARM64 ABI. Default ABI selection crashed the tested APK. |
| Fortnite download and launch | Worked through the official Epic Games Store. |
| Epic login and onboarding | Worked using injected Android touchscreen presses where mouse clicks failed. |
| Keyboard and mouse | Android detected both; Fortnite's mobile interface did not provide usable native gameplay controls. |
| Xbox Series S\|X controller over USB | Worked after publishing its Linux input device inside Android. |
| Graphics | Android compositor used AMD hardware rendering. The game's full rendering path was not independently profiled. |
| Frame rate | User reported a 30 FPS limit and poor performance. No benchmark or successful FPS unlock was recorded. |
| USB debugging warning | ADB and developer settings were disabled and verified. |
| Online gameplay | User entered a match but was kicked. The test ended without a completed match. |

## Tested environment

- Arch Linux, kernel `7.2.4-arch1-2`, built-in Rust Binder, Hyprland/Wayland.
- Ryzen 5 9600X, approximately 30 GiB RAM, AMD Navi 23 / Radeon RX 6600 family GPU.
- Waydroid Android 13, x86-64, VANILLA system and MAINLINE vendor images.
- `libndk_translation.so`, advertised bridge version `0.2.3`, for ARM64 code.
- `ro.hardware.egl=mesa`, `ro.hardware.vulkan=radeon`.
- SurfaceFlinger reported AMD Radeon Graphics, `radeonsi`, `navi23`, OpenGL ES 3.2,
  and Mesa 26.0.5. The selected render node was `/dev/dri/renderD128`.
- A late diagnostic showed a 931×498 Android display at 144 Hz. This was a snapshot
  of the resized window, not a benchmark configuration. The game's reported 30 FPS
  limit was therefore not explained by a 30 Hz Android display mode.

Running ARM code on x86-64 requires translation. Hardware rendering in Android's
compositor does not establish the game's bottleneck or guarantee good performance.

## Helpers

Python 3 is required. Run these from the repository directory. Helpers that need
privileges request sudo authentication in your terminal; they do not collect passwords.

| Command | Purpose |
| --- | --- |
| `./fortnite-linux doctor` | Inspect host, Android boot, GPU configuration, and native bridge readiness. |
| `./fortnite-linux ui` | Open Waydroid's full Android UI. |
| `./fortnite-linux bridge-install` | Install the pinned third-party bridge after preparing its source below. |
| `./fortnite-linux play` | Launch an already installed Fortnite package. |
| `python connect-controller.py` | Expose one connected Xbox controller for the current Android session. |
| `python diagnose-signin.py` | Save local input, window, activity, and logcat diagnostics. |
| `python prepare-game.py` | Disable debugging, collect graphics diagnostics, and relaunch Fortnite. |

Diagnostics remain under ignored `.diagnostics/`. They can contain account or device
information and should be reviewed before sharing. No raw diagnostics, account data,
APKs, game assets, or third-party binary dependencies are included here.

## Setup used in this experiment

Follow [Waydroid's installation documentation](https://docs.waydro.id/usage/install-on-desktops)
for your distribution. On this Arch system, the setup used:

```bash
sudo pacman -S --needed waydroid lzip
sudo waydroid init -s VANILLA
sudo systemctl start waydroid-container.service
./fortnite-linux ui
```

This is a historical reproduction path, not a promise that current images will work.
The bridge wrapper only accepts Android 11 or 13. Follow Arch's normal full-update
procedure when needed; do not refresh package databases alone with `pacman -Sy`.

Prepare the translation installer before using `bridge-install`:

```bash
mkdir -p .external
git clone https://github.com/casualsnek/waydroid_script.git .external/waydroid_script
git -C .external/waydroid_script checkout d5289cfd8929e86e7f0dc89ecadcef8b66930eec
python -m venv .external/waydroid_script/.venv
.external/waydroid_script/.venv/bin/python -m pip install -r .external/waydroid_script/requirements.txt
./fortnite-linux bridge-install
./fortnite-linux ui
```

Installer source is pinned; its Python dependencies and downloaded translation
payloads are not fully locked by this repository. Do not install competing native
bridges together. The wrapper refuses to replace a configured bridge.

### Network

The test used UFW with incoming and forwarded traffic blocked. Waydroid initially
had no working DHCP lease. These rules resolved the observed networking failure:

```bash
sudo ufw allow in on waydroid0 proto udp to any port 67
sudo ufw allow in on waydroid0 proto udp to 192.168.240.1 port 53
sudo ufw allow in on waydroid0 proto tcp to 192.168.240.1 port 53
sudo ufw route allow in on waydroid0 from 192.168.240.0/24 to any
```

Use the actual bridge/subnet on your host. These rules are specific to this UFW
setup, not a universal networking fix. The later match kick was not diagnosed as
being caused by UFW. See [Waydroid networking](https://docs.waydro.id/debugging/networking-issues).

### Epic Games Store installation

Download the APK from [Epic's official Android page](https://www.fortnite.com/mobile/android).
A similarly named APK obtained earlier was APKPure, not Epic Games Store.

The tested official store APK was version 1.6.2 (50102). It contained x86-64 libraries
but lacked `libnative-lib.so` for that ABI. Default installation selected x86-64 and
crashed with `UnsatisfiedLinkError`. Its ARM64 libraries included the missing file.
The successful installation explicitly selected ARM64:

```bash
mkdir -p "$HOME/.local/share/waydroid/data/waydroid_tmp"
cp "$HOME/Downloads/EpicGamesStore.apk" "$HOME/.local/share/waydroid/data/waydroid_tmp/EpicGamesStore-arm64.apk"
chmod 644 "$HOME/.local/share/waydroid/data/waydroid_tmp/EpicGamesStore-arm64.apk"
sudo waydroid shell -- pm install --abi arm64-v8a /data/waydroid_tmp/EpicGamesStore-arm64.apk
```

These paths assume Waydroid's default per-user data location. The tested repair used
a clean store installation after removing the broken one with
`sudo waydroid shell -- pm uninstall com.epicgames.portal`.
Uninstalling an app deletes its app data. The generic `install-apk` helper does not
force ARM64 and should not be used for this particular store APK failure.

Open Epic Games Store inside Android to download Fortnite. Game content is not
provided by this repository. On Android 13, `pm install` rejected a trailing `-`
used as a stdin filename; staging a readable file avoided that failure and shell
redirection permission problems.

### Input

Epic documents that mobile Fortnite does not support keyboard/mouse gameplay in its
[external-device guidance](https://www.epicgames.com/help/en-US/c-Category_Fortnite/c-Trending_0/what-devices-can-i-use-to-play-fortnite-on-mobile-console-or-pc-a000084884).
Android's input diagnostics showed a keyboard/DPAD, mouse, and virtual touchscreen.
A/B prompts alone were not evidence that Android had detected a physical controller.

`persist.waydroid.fake_touch` was tested and did not fix the observed Fortnite menu
interaction; its previous value was restored. Explicit touchscreen presses through
`waydroid shell -- input touchscreen` did advance login and onboarding. Coordinates
must be calculated from the current Android viewport, not a cropped desktop image.

Enabling `persist.waydroid.udev` and `persist.waydroid.uevent` and restarting was not
sufficient to expose the Xbox controller on this host. Linux detected it through
`xpad`, while Android initially had only Wayland input pipes under `/dev/input`.

`connect-controller.py` creates a character device using the connected Xbox event
node's current major/minor numbers. It prepares ownership and permissions, then
publishes a hard link into Android's input directory. This generates `IN_CREATE`.
An earlier attempt used a move, producing `IN_MOVED_TO`, which Android 13's
[EventHub watcher](https://android.googlesource.com/platform/frameworks/native/+/refs/heads/android13-release/services/inputflinger/reader/EventHub.cpp)
does not subscribe to. The corrected helper resulted in Android detection and
user-confirmed working Fortnite controller input.

This is a temporary, single-controller repair, not a hotplug daemon. Restarting
Waydroid removes the added nodes. Device numbering can change after reconnecting;
restart Waydroid and rerun the helper if needed. It does not pass through all host
input devices or install a keyboard mapper.

### Debugging and matchmaking

`prepare-game.py` saves prior debugging settings locally, disables USB/wireless
ADB and developer options, removes ADB from the persistent USB functions, and stops
`adbd`. Local `waydroid shell` uses LXC and remains available without ADB.

The final diagnostics confirmed:

```text
adb_enabled: 0
adb_wifi_enabled: 0
development_settings_enabled: 0
init.svc.adbd: stopped
persist.sys.usb.config: none
ro.debuggable: 0
```

This follows [Epic's instruction to disable developer options](https://www.epicgames.com/help/c-34254770/c-38015632/a25494421).
It does not spoof hardware identity or alter integrity results. The subsequent
user-reported match kick remained unresolved. Disabling debugging did not establish
that Waydroid was eligible for online play.

## Stopping and removing the experiment

```bash
waydroid session stop
sudo systemctl stop waydroid-container.service
```

This stops Android without deleting app data. Temporary controller nodes disappear
with the container. Remove project caches, staged APKs, and local diagnostics when
no longer needed. Removing the entire Waydroid environment also deletes Android
apps, downloaded content, and sign-in state; that is separate from stopping it.

The final outcome is a documented compatibility experiment: reaching the lobby and
handling input were possible, but reliable online play was not demonstrated.
