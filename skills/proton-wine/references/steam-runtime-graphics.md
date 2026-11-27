# Graphics inside Steam's pressure-vessel container

**For maintainers checking an edition library in Steam Linux Runtime:** identify what the container maps, what the program loads and what reaches the window.
The checks below ran on the edition's r1123a graphics stack on 27 November 2026.
Run them on a disposable system with its own X server and home directory.
Keep both host architectures.

## Check the runtime without an account

1. Download Valve's versioned [soldier depot](https://repo.steampowered.com/steamrt2/images/2.0.20261021.266042/SteamLinuxRuntime_soldier.tar.xz), [sniper depot](https://repo.steampowered.com/steamrt3/images/3.0.20261021.266025/SteamLinuxRuntime_sniper.tar.xz) or [SteamRT3c amd64 client runtime](https://repo.steampowered.com/steamrt3c/images/3c.0.20261103.268067/steam-runtime-steamrt-amd64.tar.xz).
   Verify the archive against `SHA256SUMS` in its version directory, unpack it and record `VERSIONS.txt`.
   Valve describes which runtime each Proton or native game uses. [Steam Runtime README](https://github.com/ValveSoftware/steam-runtime)
2. Run `pressure-vessel/bin/steam-runtime-check-requirements -v` from the unpacked directory, then `PRESSURE_VESSEL_BATCH=1 ./run -- cat /etc/os-release`.
   Expect exit 0 and the build ID of the chosen runtime.
   The checker covers startup prerequisites such as bubblewrap, and a separate graphics probe is necessary.
3. Under a private X server, share the directory containing an i386 `glxinfo` binary and run it with `-B`.
   With both native and i386 Mesa installed on the outer system, expect its full Mesa version in the renderer report.
   Read the target of `/overrides/lib/i386-linux-gnu/libGLX_mesa.so.0` and the software DRI shim under that directory's `dri/`.
   Match both resolved files by SHA-256 to the provider's installed files.
4. Run `./run -- env VK_LOADER_DEBUG=layer vulkaninfo --summary` and repeat with `./run --no-import-vulkan-layers -- env VK_LOADER_DEBUG=layer vulkaninfo --summary`.
   On r1123a the first run discovers `VK_LAYER_MESA_stereo` and inserts it from `/run/host/usr/lib/x86_64-linux-gnu/libVkLayer_MESA_stereo.so`.
   The second still sees the graphics driver and loses the distribution's imported layer.
   Read numbered JSON entries under `/overrides/share/vulkan/{implicit_layer.d,explicit_layer.d}` and check the layer name and library, since the loader sees the numbered names.
   The stereo manifest comes from the amd64 `mesa-vulkan-layer-stereo` package.
5. Run the distribution's `gl-stereo/tests/quad.c` fixture in a shared directory with its `auto` argument and this preload.
   The fixture announces X11 stereo on its private server, checks one full-SBS declaration and double-width geometry, and repeats with the `unsupported` argument to check the absence of a stereo visual when the announcement is missing.

   ```sh
   PRESSURE_VESSEL_BATCH=1 GL_STEREO=1 ./run \
     --filesystem="$PROBES:ro" \
     --ld-preload=/usr/lib/x86_64-linux-gnu/libstereo-declare.so.1 \
     --ld-preload=/usr/lib/gl-stereo/libgl-stereo.so \
     -- "$PROBES/gl-quad" auto
   ```

   Both the explicit options and the same pair in the outer `LD_PRELOAD` passed in soldier, sniper and SteamRT3c.
   Scope this amd64 preload to the test command or a game that requests this layer.
   The edition publishes the GL interposer for amd64 and publishes the Mesa graphics libraries for both architectures.

## Traps

- **`libstereo-declare.so.1: cannot open shared object file` after preloading gl-stereo.** Pressure-vessel passes the interposer from the provider and its loader still needs the declaration library's SONAME.
  `readelf -d /usr/lib/gl-stereo/libgl-stereo.so` shows the dependency.
  The one-module preload fails with exit 127 in the three runtimes.
  Preload the amd64 declaration library before the interposer and rerun both X11 declaration cases.
- **A Vulkan stereo manifest exists on the provider and the loader never inserts it.** The runtime has its own manifest search paths, and a host file listing only proves installation.
  Read `VK_LOADER_DEBUG=layer` for instance and device insertion and compare with `--no-import-vulkan-layers`.
  Default import passed on llvmpipe and on an RTX 3060 exposed to the bench through CDI.
  Those checks prove layer discovery and loading. A two-layer swapchain still needs its own capture.
- **`d3dadapter9.so` is missing even before pressure-vessel starts.** Search both provider architectures and the published Contents indexes before diagnosing the runtime.
  r1123a ships Mesa 26.1.6 and contains no Gallium Nine adapter. Mesa removed the frontend in 25.2.
  A regression test for an older system with Nine needs a provider that actually ships that adapter. [Mesa 25.2 release notes](https://docs.mesa3d.org/relnotes/25.2.0.html)
- **`GLIBC_2.38 not found` when the i386 probe runs without the host graphics provider.** In this comparison the Debian-built probe needs a newer glibc than the copies in these Valve runtimes.
  The default run loaded both the provider's i386 glibc and Mesa. The control with `--graphics-provider=` stopped at the loader, before GLX.
  Use the default provider and check the mapped libraries to prove the render path.

Valve's October 2026 beta and November 11 public client update moved the Linux client to 64-bit in SteamRT3c.
Valve still requires the two graphics and library architectures on x86-64.
The client runtime and the game runtimes have separate version identifiers. [Valve's client requirements](https://github.com/ValveSoftware/steam-for-linux/blob/master/README.beta.md), [November 11 client release notes](https://steamcommunity.com/app/593110/announcements/detail/)

## Test an i386 D3D9 program

Use a disposable Wine prefix under the shared home, an existing PE32 D3D9 fixture that calls `CreateDevice`, `Clear` and `Present`, and private Xvfb with continuous root properties.
Record the HRESULT of each call, the loaded DLLs with `WINEDEBUG=+loaddll`, DXVK's device log, and the X11 declaration.
The r1123a comparison used Wine `10.0~repack-12+stereo3d8+lc1`, DXVK `2.7.1-4+stereo3d5+lc1`, and wiz3D `0.3.1+stereo3d6+lc1`.

1. Create a win32 prefix in the outer environment with `wine32 wineboot -u` and `dxvk-setup install --yes`.
   Run the fixture under `wine32` with `WINEDLLOVERRIDES=d3d9=n`.
   Expect three zero HRESULTs and DXVK's version and device log.
2. Stage a Wine loader and server for the inner path from that same installed Wine build.
   Preserve the loader's install-relative data directory and let the server use Wine's `server/` and sibling `nls/` layout.

   ```sh
   wine_dir=/usr/lib/i386-linux-gnu/wine
   portable="$HOME/portable-wine"
   loader="$portable$wine_dir/wine"
   server="$portable/server/wineserver"
   mkdir -p "${loader%/*}" "${server%/*}" "$portable/usr/share/wine"
   cp "$wine_dir/wine" "$loader"
   cp "$wine_dir/wineserver" "$server"
   cp -a /usr/share/wine/nls "$portable/usr/share/wine/"
   ln -s usr/share/wine/nls "$portable/nls"
   ```

   Run `./run --filesystem="$PROBES:ro" -- env WINESERVER="$server" WINEDLLPATH="/run/host$wine_dir" "$loader" "$PROBES/d3d9.exe"` with the same prefix and native override.
   After the host-only DLL link fails, copy the edition's `/usr/lib/dxvk/wine32/d3d9.dll.so` over the prefix's `drive_c/windows/system32/d3d9.dll` using `cp -L --remove-destination`.
   All three HRESULTs return zero again.
3. Run the inner Wine command through the outer `wiz3d-launch --no-fallback --`.
   A copy of `/usr/lib/wiz3d` under the shared home, selected by `WIZ3D_DIR`, makes its native DLLs visible inside the container.
   Share the launcher's private `XDG_RUNTIME_DIR` with `--filesystem=PATH:rw` so the injector can write the state file that the outer declaration helper reads.
   The supplied DXVK DLL is loaded as `d3d9_real.dll` behind the wiz3D proxy.
   Expect a successful Present, double-width swapchain and one full-SBS X11 declaration when the test server announces stereo support.
   The declaration fixture has no Stereo KWin capture. Real Proton, game scenes and both-eye output need separate rows.

- **`wineserver: failed to load l_intl.nls` when the loader is invoked straight out of `/run/host/usr/lib`.** The server derives its NLS location from its own executable and compiled data paths.
  Wine prefers the server beside its loader before consulting `WINESERVER`.
  This was isolated by comparing the direct launch with the staged paths above.
  Preserve the relative data tree and use a loader directory without a sibling server for this bench. [Wine 10.0 server lookup](https://github.com/wine-mirror/wine/blob/wine-10.0/server/unicode.c), [loader lookup](https://github.com/wine-mirror/wine/blob/wine-10.0/dlls/ntdll/unix/loader.c)
- **Wine cannot open the native D3D9 override or wiz3D says no full-SBS window was declared.** DXVK's setup and wiz3D's installer use absolute links to the outer `/usr/lib`.
  The two `/usr` trees differ. A file at `/run/host/usr/lib` does not satisfy a prefix link pinned to `/usr/lib`.
  Compare unchanged links with the copied DXVK DLL and shared wiz3D tree. Use the native-only DXVK control and require the wiz3D native modules and declaration in the log so a builtin D3D9 path cannot pass.
