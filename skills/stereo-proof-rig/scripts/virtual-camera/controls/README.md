# Camera controls rig (ORDER 678 and 682)

The rows of `sparky-stereo-camera` 0.1.3 against user-space cameras: what is a setting, the apply order, the clean-up of an older store, the best mode, and what Qt and PipeWire programs negotiate. The recipe and the traps are in the skill [kde-desktop-defaults, camera controls](../../../../kde-desktop-defaults/references/camera-controls.md).

One throwaway container per run, from an image that has the package's runtime and build dependencies, PipeWire, WirePlumber and GStreamer's `pipewiresrc`:

    docker run --rm --ulimit core=1 --cpus 4 --network none \
      -v THIS_FOLDER:/rig:ro -v RUN:RUN -v OLD_DEBS:/deb012:ro -v NEW_DEBS:/deb013:ro \
      -v SPARKY_STEREO_HARDWARE_RECIPE:/hw:ro -e RUN=RUN IMAGE bash /rig/inner.sh red|green|upgrade [ROW...]

- `/rig` holds this folder with the parent folder's `vcam-shim.c` beside `inner.sh` (copy it in), `/hw` the hardware package's recipe (its `bin/sparky-stereo-known-machines` and `share/known-machines.json`).
- `inner.sh` runs as root: it writes a passwd entry for uid 1000 (the session bus needs one), builds the shim and the probes, installs the package under test with apt, makes `/dev/video30` to `/dev/video35` broken symbolic links (what Qt lists), then runs `rows.sh` as uid 1000.
- `rows.sh` starts a session bus, PipeWire with the shim preloaded and WirePlumber with its device monitors off, creates one `api.v4l2.source` node per fixture, and prints `PASS`, `FAIL` or `GAP` per row into `RUN/rows.txt`. Rows: `imac refusal flags cluster a10 a10manual modes page sentence vaio watch notfound restart gone retry who`; `upgrade` runs `before-upgrade` on the old package and `after-upgrade` on the new one in the same session. `inner.sh prev` installs a package mounted at `/debprev` (an earlier build to compare with).
- Fixtures: `vcam/video30.cfg` the iMac's two controls, `video31.cfg` the A10's camera, `video32.cfg` a control of each flag and a governed control with a lower id than its governing one, `video33.cfg` sizes and rates in two formats, `video34.cfg` with `machines/` a known machine's camera caveat, `video35.cfg` a camera another program holds.
