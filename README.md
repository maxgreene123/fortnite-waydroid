# Fortnite on Linux through Waydroid

Fortnite launched, login worked, and a match could be entered, but gameplay stuttered and ended in a kick. No full match was completed.

## Environment

| Component | Tested setup |
| --- | --- |
| OS | Arch Linux, kernel 7.2.4-arch1-2 |
| Desktop | Hyprland / Wayland |
| CPU | AMD Ryzen 5 9600X |
| RAM | 32 GB DDR5-6400 |
| GPU | AMD Radeon RX 6600 family / Navi 23 |
| Android | Waydroid Android 13, x86-64, VANILLA system, MAINLINE vendor |
| ARM translation | libndk_translation.so, version 0.2.3 |
| Graphics | Mesa 26.0.5, radeonsi, Radeon Vulkan driver configured |
| Controller | Xbox Series S\|X controller connected over USB |

## Findings

- **Installation:** The tested Epic Games Store APK crashed when installed as x86-64.
  Explicitly installing its ARM64 version worked. Fortnite was downloaded through
  the official store.
- **Login:** Sign-in and onboarding worked. Some buttons required injected Android
  touchscreen presses because mouse clicks did not activate them.
- **Controls:** Native keyboard and mouse gameplay did not work in this test. The
  Xbox controller worked after its input device was manually exposed to Android.
- **Graphics:** Android's compositor used AMD hardware rendering. The game's
  rendering path and performance bottleneck were not independently profiled.
- **Performance:** Fortnite was capped at **30 FPS**. There were also constant
  in-game stutters attributed to ping. Poor performance was not just the frame-rate
  cap; no measurements were collected to isolate the cause of the stutters.
- **Debugging:** USB debugging, wireless debugging, and developer options were
  disabled, and the ADB service was verified stopped before the final match attempt.

## Match removal

After entering a match and experiencing constant stutters, the game displayed:

> You were removed from the match due to internet lag, your IP or machine,
> VPN usage, or for cheating. We recommend not utilizing VPN or proxy
> services while attempting to play Fortnite.

Error code: `errors.com.epicgames.common.processing`

The message lists several possible reasons; it does not identify which caused this
kick. VPN use, an anti-cheat rejection, and the underlying network cause were not
confirmed. Launching Fortnite worked, but reliable online play was not demonstrated.

## Experiment scripts

The original helpers are included for reference and reproduction:

- [`fortnite-linux`](fortnite-linux): readiness checks, full UI, ARM translation installation, APK installation, and launching.
- [`connect-controller.py`](connect-controller.py): temporary Xbox controller input repair.
- [`diagnose-signin.py`](diagnose-signin.py): local sign-in and input diagnostics.
- [`prepare-game.py`](prepare-game.py): disable Android debugging and collect graphics diagnostics.

See [script usage and limitations](docs/SCRIPTS.md). These helpers do not resolve
the match-removal error or unlock the frame-rate cap.
