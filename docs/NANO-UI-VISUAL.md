# Native menu appearance

The visual layer uses Half-Life's classic grey/orange controls and Counter-Strike
1.6's Steam green/yellow controls. It retains the native 240×240 fitting, focus
scrolling and saved preferences. Main menus use plain text selection; settings
have compact titles, beveled buttons and inset fields. Lists scroll with focus
without a scrollbar or position indicator. Loading screens retain actual engine
and bot progress.

Half-Life's main menu opens a combined save browser with three entries and three
aspect-correct thumbnails. A loads, X saves or overwrites, Y deletes and B returns.
`New save` remains at the top. Saving requires an active single-player game.
Overwrite and delete prompt first, default to Cancel, and keep the chosen filename
fixed until confirmation. Preview textures are released before a shifted window
loads, and when loading, saving or closing the browser.

The supplied game font is Tahoma. Exact original retail/WON picture-button
lettering remains pending. Counter-Strike artwork comes from its original
800×600 loading tiles. The available Half-Life installation supplies restored
classic artwork through its Anniversary HD layout; it has not been verified as
byte-identical to the 1998 release. The square crop preserves proportions and
uses 60% horizontal placement for Half-Life and the right edge for Counter-Strike.
Logos remain small. Pause menus dim the game world when `ui_renderworld` already
permits it; device clarity and performance determine whether that path is usable.

## Preparing owned artwork

Install Pillow for the asset preparation step, then run:

```sh
python3 tools/prepare_menu_art.py --games /path/to/game-data --output build/menu-art
```

The input folder contains `valve` and `cstrike`. This version expects the supplied
Half-Life `resource/HD_BackgroundLayout.txt` and logo, and the CS 800×600 loading
tiles and `resource/game_menu.tga`. It writes two 240×240 TGA backgrounds, two small
transparent TGA logos, and one opaque indexed GoldSrc sprite for CS bot loading.
`menu-art.json` records source/output hashes and crop positions. Copy the generated
game folders into the private runtime. The Nano loads these bounded resources
even with low-memory mode enabled, instead of loading the full HD tile set.
Without them, menus retain the theme's solid background.

Artwork remains in private build outputs. The public source includes its
preparation code and the `ui-v5-*` patches, without proprietary game assets.
The normal source-fetch tools apply the visual patches and copy shared headers.
The UI update packager accepts only the five named artwork paths when a candidate
manifest explicitly supplies their hashes. Installation checks the current
baseline, backs up replaced files, and supports rollback including new assets.
UI settings stay at profile version 3; appearance does not require migration.

## Valve intro

The framebuffer engine can play the owner's classic Valve-man intro once at
startup, before the existing Half-Life map or Counter-Strike match menu. It
preserves the full original 4:3 frame at 240×180, centred vertically on the
240×240 screen. Any physical button skips it; its held/repeat/release records
are consumed so the same press cannot activate the following menu. Normal map
loading retains its themed artwork and real progress rather than replaying the
intro. `-nointro` or `-noavi` disables playback.

Prepare the locally owned `valve.avi` using FFmpeg on the build host:

```sh
python3 tools/prepare_intro.py --source /path/to/valve/media/valve.avi --output build/menu-art
```

This produces `valve/media/nano_valve.nvi` and `intro.json` with source/output
hashes. The inspected original is 10 seconds at 15 fps, with 22050 Hz mono
unsigned PCM audio. The prepared file stores RGB565 frames and the audio;
playback keeps one packed frame, one RGBA frame and one renderer texture, and
streams audio through the existing mixer. It needs no target FFmpeg libraries.
The file is about 13.2 MB on storage, rather than being loaded whole into RAM.
Header bounds and exact file length are checked before allocating. Textures,
files and frame buffers are released on completion, skip or interruption.

The update packager separately allowlists this one media path when a candidate
manifest includes `intro_media` hashes. Prepared pictures/audio stay private,
alongside the owner's other game data. Missing or invalid media leaves the
normal launcher destination available.

## Validation

Both ARM menu libraries, the engine input change and the CS loading change compile.
Host checks execute the actual menu layout, save actions and input routing with
address/undefined-behavior sanitizers. They cover main traversal, titled settings
and tab bounds, dialog overflow and cancellation, save/delete target stability,
three-thumbnail ownership during scrolling, new-save guards, and settings and
bot-progress behavior. A disposable host runtime checks update installation and
complete rollback, including newly created artwork directories.
The intro test executes the real player and cinematic code with sanitizers,
checking bounded allocations, RGB565 decoding, audio streaming, one texture,
timing, pause, malformed/truncated media, skips and restoration of queued maps
or match setup. Input checks cover every physical skip button and both presets.

Device checks on 7 October 2026 launched both installed `(source)` OPKs through
their normal entry points. Framebuffer captures confirm the classic Valve intro,
CS artwork, match setup, options, audio sliders and Cancel-default Quit dialog,
plus the HL campaign launch, main menu, Configuration and three-entry save browser.
X and Y opened the overwrite/delete prompts, A accepted their selected Cancel,
and scrolling replaced the three thumbnails correctly. No test committed an
overwrite or deletion. All installed component/media hashes match the candidate;
saved settings, bindings, match preferences and save files stayed byte-identical.

Hardware testing caught and fixed cached child positions after a parent viewport
move, and theme initialization before profile cvars had loaded. The layout
regression covers the first issue; representative captures confirm both fixes.
The intro's original audio samples are unchanged and ALSA playback was active
with the amplifier enabled. Audible sound quality still requires listening on
the device. World-backed pause performance, total runtime memory profiling and
every specialized editor remain outside this representative hardware check.
