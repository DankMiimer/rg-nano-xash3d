Half-Life and Counter-Strike for RG Nano and FunKey S - @VERSION@
=================================================================

Half-Life and Counter-Strike 1.6 running natively on the 240x240 screen,
with menus, HUD and controls made for these tiny consoles.

No game files are included. You need your own copy of Half-Life (and
Counter-Strike 1.6 if you want it), for example from Steam.


WHAT YOU NEED
-------------
- An RG Nano or a FunKey S running DrUm78's FunKey OS.
- Half-Life from Steam. Counter-Strike 1.6 is optional.
- About 900 MB free on the SD card.


INSTALL
-------
1. Put the console's SD card in your PC (card reader, or connect the
   console over USB and choose "Mount USB" in its menu).

2. Copy your game files.
   On the PC, open your Half-Life folder. In Steam: right-click Half-Life >
   Manage > Browse local files. It is usually
   Steam\steamapps\common\Half-Life
   Copy the "valve" folder, and the "cstrike" folder if you have
   Counter-Strike, into this folder on the SD card (create it if needed):
   FunKey\Xash3D-source

3. Copy this release.
   Copy everything inside the "SD card" folder of this zip to the root of
   the SD card. When asked, choose to replace the files.

4. Eject the card, start the console and open Native games.
   Start "Half-Life" or "Counter-Strike".

The first start takes a few seconds longer: the game builds its menu
artwork and launcher icon from your game files. The new icon shows after
the next restart.


CONTROLS
--------
D-pad                 Walk and turn
Hold R + D-pad        Look up/down and strafe
Hold L                Faster camera
X                     Shoot
Y                     Reload
A                     Use
B                     Jump
Hold Fn               Crouch
Start                 Half-Life: flashlight     Counter-Strike: buy menu
Fn + Start            Half-Life: next weapon    Counter-Strike: auto-buy
Fn + L / Fn + R       Half-Life: quick save / quick load
Menu                  Game menu (save, load, options, quit)
Fn + A / Fn + Y       Volume up / down
Fn + X / Fn + B       Brightness up / down
Hold Fn + L + R       Force quit if a game is stuck

Counter-Strike menus: Fn + Left / Down / Right pick 1 / 2 / 3,
Fn + Start + L / R pick 4 / 5.

Prefer aiming with the face buttons? Menu > Options > Nano settings >
Control scheme > Face-button aiming, then restart the game.


GOOD TO KNOW
------------
- Closing the FunKey S lid, or pressing the RG Nano power button, saves
  Half-Life and turns the console off. Turn it on again to continue where
  you left off. Counter-Strike closes without saving.
- Half-Life saves are under Menu > Save/Load Game (A load, X save,
  Y delete).
- Counter-Strike starts with an offline match setup (map, bots,
  difficulty). Bots need a navigation file for each map, which a new
  install doesn't have. If you see "No NAV: bots 0 or Advanced", play with
  0 bots, or open Advanced, tick "Allow slow NAV analysis" and start: the
  console then spends a few minutes (once per map) mapping it for bots.
  Bots fight normally but don't use voice chatter.
- Expect some pauses while levels load: the console has only 64 MB of RAM.
- Settings for frame rate, aiming and HUD size: Menu > Configuration >
  Nano settings (Counter-Strike: Menu > Options > Nano settings).


UPDATING
--------
Repeat step 3 with the new release. Your saves and settings are kept.


IF SOMETHING GOES WRONG
-----------------------
- "Files missing" message: check that the "valve" (and "cstrike") folders
  are directly inside FunKey\Xash3D-source on the SD card.
- Logs are in FunKey\Xash3D-source\diagnostics.
- Report problems at https://github.com/DankMiimer/rg-nano-xash3d/issues

This is an unofficial fan project, not affiliated with Valve, Anbernic or
the FunKey project. Licences and source: FunKey\Xash3D-source\licenses.
