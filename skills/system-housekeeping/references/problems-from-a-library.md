# A library that tells the person (Mesa's GLX, ORDER 561)

A program can show its failure in its own window; a library inside any program cannot, and a line on standard error reaches nobody.
Mesa's GLX hands its two failures to `sparky-stereo-problems`, the way a C program does ([edition-packaging, the OpenXR runtime's recipe](../../edition-packaging/references/openxr-runtime-package.md#a-programs-failure-through-the-problems-engine-a-c-or-c-program-order-58b)), with what a library in a `Multi-Arch: same` package adds.

## The two problems

| Package | Key | Message | Severity | Kept when | Ended when |
|---|---|---|---|---|---|
| `libglx-mesa0` | `stereo-pair:PROGRAM` (the process name; letters, digits and `_ @ + - .`, anything else `_`) | `LOCAL2`: the program, then Mesa's own words | failed | the X server copied the two eyes of a stereo window twice in a row, so the declaration was taken back and the window shows the left view | a pair of that program is flipped again |
| `libglx-mesa0` | `zink-without-dri3` | `LOCAL4`: Mesa's own words | degraded | zink was set for the session and the X server has no DRI3, so programs draw on the software renderer | a program finds zink with DRI3 |

`LOCAL1` and `LOCAL3` are their titles (`--subject LOCAL1 --subject LOCAL3=LOCAL4` at catalog time).
Both are the person's own (`--person`): the library runs as the person.

## Recipe

1. **One key for each thing that fails, and one for each program where programs fail apart.** Two programs with one key would hide and end each other's problem.
2. **Open the engine's library at run time, never link it** (`dlopen` of the path given at build time, `ssp_keep`, `ssp_clear`, `ssp_error_en`): a link would put a private library into every program that loads the GL library.
3. **A process that cannot load it runs the command.** The engine is an amd64 package; a 32-bit program's `dlopen` fails, and `posix_spawn` of `/usr/bin/sparky-stereo-problems keep --person --quiet --details JSON PACKAGE KEY MESSAGE ARG...` keeps the same record. A program that reaps every child itself can take the status first (`waitpid` answers `ECHILD`): count that as done.
4. **When neither is there, say that the person cannot be told,** as an error line; when only an old problem was to be ended, as an information line.
5. **Behind a build option that is empty upstream** (`-Dsparky-stereo-problems-library=PATH`): other builds only log.
6. **Packaging in a `Multi-Arch: same` package:** `Build-Depends` and `Depends` on `sparky-stereo-problems (>= 0.1.2) [amd64]`; the catalogs made in the amd64 build only (`sparky-stereo-problems catalog PACKAGE debian/lang debian/PACKAGE/usr/lib/systemd/catalog ...`), since a file that one architecture alone ships is no conflict between the two; the same build option on every architecture; a postrm that runs `sparky-stereo-problems clear --all PACKAGE` on remove and purge when the command exists.
7. **Proof:** the failure made on purpose in the rig, `sparky-stereo-problems list` in English and with `LC_ALL=pt_BR.UTF-8`, the same case ended (`list --json` is `[]`), and the package's own test with the engine absent, which reads the message on standard error.

## Traps

- **Symptom:** the record appears and goes at every start of a stereo program.
  **Cause:** the first copied present was taken for certain; the window manager drops that frame.
  **Fix:** two in a row ([native-linux, when the pair cannot be flipped](../../native-linux/references/x11-stereo-window-without-glamor.md#when-the-pair-cannot-be-flipped)).
- **Symptom:** `sparky-stereo-problems list` shows the title "a problem needs attention" and the English text in every language.
  **Cause:** the package's catalog is not installed (a development build of the library), so the record's `text_en` is shown.
  **Fix:** install the package that carries the catalogs before judging a translation.
