# The display name comes from os-release VERSION

The SparkyLinux About and System Info tools read OSCODE from /etc/lsb-release in the pinned releases 0.1.49 and 0.1.9.
The edition keeps the internal Tiamat identifiers but displays the name in parentheses of VERSION in /etc/os-release.
Only the two OSCODE assignments change in the carried +stereo3d1 versions.
Never change DISTRIB_CODENAME, VERSION_CODENAME or /etc/sparky/info for a display fix.

Use the [SparkyLinux tool packaging recipe](../../edition-packaging/references/carried-sparkylinux-tool.md).
Run both installed tools against edition and stock release fixtures in separate private logins.
Capture Yad's exact text arguments while still executing the real Yad binary and capture its rendered windows.
Expect Mashtabba on the edition and Tiamat on stock files; hash all release files before and after.
The unmodified tools form the red control on edition files.

## Trap

- **Symptom:** a locally installed stereo tool can lose to the base distribution's package on the next apt operation.
  **Cause:** sparky-apt pins o=SparkyLinux at 1001; a generic pin for another origin is not an explicit preference above it.
  **Fix:** add a specific priority 1002 for sparky-about:any and sparky-system:any from o=Sparky Stereo OS in sparky-stereo-apt's canonical pin file.
  **Found by:** reading the actual installed SparkyLinux preference and measuring apt-cache policy with both archives present.
