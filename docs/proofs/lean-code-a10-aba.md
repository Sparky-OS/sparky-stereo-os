# Lean Code on a 2016 laptop: lean, original, lean again

Measured on 3 November 2026 on an AMD A10-9600P laptop from 2016 (11 GiB of memory, two SATA SSDs, Sparky Stereo OS with kernel 7.3.1-stereo3d14, dpkg-stereo 0.1.24).
The question: what does a whole installed system gain or pay for being lean, compared with the same system holding its packages' original files?
Every measured case is in [lean-code-a10-aba/results.csv](lean-code-a10-aba/results.csv).

## How it was measured

Three states of the same installation, in this order:
1. **Lean:** every file dpkg-stereo projects is in its lean form.
2. **Original files:** `dpkg-stereo --restore` put every projected file back to its package's bytes (about 28,500 files).
3. **Lean again:** projected once more.

In each state: three boots to the desktop, then the same bench (program launches, driver builds against the kernel headers, package and settings tools).
Every step started with the processor at or below 55 °C, so heat could not decide a result.
The two lean states agree with each other, so a difference from the original files is the projection's, not the order of the runs.

## Builds against the kernel headers: faster

Driver modules built the way DKMS builds them, and single headers through the preprocessor; "warm" means the files were already in memory, "cold" that the cache was dropped first.

| Build or step | Lean | Original files | Lean again | Change |
|---|---|---|---|---|
| `dkms-evdi-1.15.1+dfsg-j4-warm` | 39.12 s | 42.99 s | 39.13 s | -9.0 % |
| `dkms-evdi-1.15.1+dfsg-j1-warm` | 50.40 s | 54.66 s | 50.30 s | -7.9 % |
| `dkms-evdi-1.15.1+dfsg-j1-cold` | 52.05 s | 55.35 s | 51.74 s | -6.2 % |
| `dkms-v4l2loopback-0.15.4-j4-warm` | 6.34 s | 6.81 s | 6.18 s | -8.0 % |
| `dkms-v4l2loopback-0.15.4-j1-warm` | 6.76 s | 7.13 s | 6.89 s | -4.3 % |
| `dkms-v4l2loopback-0.15.4-j1-cold` | 7.90 s | 8.34 s | 7.77 s | -6.0 % |
| `dkms-acpi-call-1.2.2-j4-warm` | 4.40 s | 4.70 s | 4.23 s | -8.2 % |
| `dkms-acpi-call-1.2.2-j1-warm` | 4.89 s | 5.25 s | 5.00 s | -5.8 % |
| `dkms-acpi-call-1.2.2-j1-cold` | 5.55 s | 5.74 s | 5.84 s | -0.8 % |
| `cpp-kernel-linux_netdevice.h` | 0.47 s | 0.51 s | 0.45 s | -9.5 % |
| `cpp-kernel-linux_fs.h` | 0.28 s | 0.31 s | 0.28 s | -8.4 % |
| `cpp-kernel-linux_mm.h` | 0.31 s | 0.34 s | 0.31 s | -6.9 % |
| `cpp-kernel-linux_sched.h` | 0.13 s | 0.14 s | 0.13 s | -7.7 % |
| `cpp-usr-stdio.h` | 0.02 s | 0.03 s | 0.02 s | -3.9 % |

Every build is faster lean: 6 to 9 % when warm, 1 to 6 % when cold.
Both lean runs built byte-identical modules.
With the original files, acpi-call is identical and evdi and v4l2loopback differ, which is expected: lean headers have fewer lines, and kernel macros carry header line numbers into the module ([line numbers](../lean-code-packages.md)); that this is the only difference was not checked byte by byte here.

## Programs: smaller, except Discover

| Program (memory, PSS, median of all launches) | Lean | Original files | Lean again | Change | Window opens (median) |
|---|---|---|---|---|---|
| plasmashell | 220 MiB | 226 MiB | 218 MiB | -2.9 % | 2.83 / 2.82 / 2.82 s |
| systemsettings | 164 MiB | 172 MiB | 164 MiB | -4.2 % | 4.57 / 4.67 / 4.62 s |
| dolphin | 57 MiB | 58 MiB | 51 MiB | -6.4 % | 2.23 / 2.20 / 2.29 s |
| plasma-discover | 968 MiB | 640 MiB | 968 MiB | +51.4 % | 4.58 / 4.40 / 4.94 s |

Plasma's shell, System Settings and Dolphin use 3 to 6 % less memory lean, and their windows open in the same time.

**Discover is the exception, and it is a problem we are fixing.**
Its first launch uses about the same memory in every state; from the second launch on it stays near 968 MiB lean, against about 620 MiB with the original files, in both lean runs.
Lean files should make it smaller, not bigger, so we are tracing which of the files it reads causes this; this page will be updated with the cause and the fix.

## Boot: the same

| Boot | Lean | Original files | Lean again |
|---|---|---|---|
| To the desktop, median (mean) of 3 boots | 47.5 s (48.2 s) | 47.5 s (48.2 s) | 48.5 s (48.7 s) |
| Desktop memory after boot, PSS, mean | 3079 MiB | 3100 MiB | 3056 MiB |


Boot time is within its own noise in all three states; the desktop uses 0.7 to 1.4 % less memory lean.

## What being lean costs

| Step | Lean | Original files | Lean again | Change |
|---|---|---|---|---|
| `dpkg-configure-noop` | 1.80 s | 1.02 s | 1.37 s | +55.0 % |
| `dpkg-stereo-verify` | 23.39 s | 10.95 s | 21.10 s | +103.1 % |
| `hardware-dryrun-warm` | 8.28 s | 7.06 s | 8.15 s | +16.4 % |
| `hardware-dryrun-cold` | 8.52 s | 7.83 s | 8.52 s | +8.8 % |
| `daemon-reload` | 1.82 s | 1.88 s | 1.79 s | -3.9 % |
| `daemon-reload-cold` | 2.31 s | 2.30 s | 2.40 s | +2.5 % |
| `stereo-display-info-warm` | 0.91 s | 0.93 s | 0.93 s | -0.5 % |
| `python3-start-cold` | 0.10 s | 0.10 s | 0.10 s | -0.2 % |
| `bash-interactive-cold` | 0.13 s | 0.13 s | 0.12 s | -6.3 % |

- A dpkg run with nothing to do takes 0.35 to 0.78 s longer: that is dpkg-stereo's check after each run. dpkg-stereo 0.1.29 has since cut that check from about 368 ms to 64 ms on a test system; the laptop will be measured again with it.
- Verifying all 28,500 projected files takes 21 to 23 s, against 11 s with nothing projected; it runs when someone asks for it.
- Hardware Setup's dry run takes about 1 s longer, because it calls dpkg.
- Reading settings and starting small tools differ by a few percent either way, within this bench's noise: the per-read gain may be there, but this bench is too coarse to show it.

## A year of heavy use, projected from these numbers

A projection, not a measurement: these assumptions are ours, and each line scales with its own number.
- A kernel update every two weeks (26 a year), each rebuilding the three modules above.
- Three package operations a day (1,095 dpkg runs a year).
- A full verification once a month, and Hardware Setup's check once a week.

| Who | Over a year |
|---|---|
| Someone who builds drivers or modules, 1 hour a day against kernel headers, 250 working days | **15 to 22 hours saved**: each hour of building saves 3.6 to 5.4 minutes, and the costs below are minutes against that |
| A heavy desktop user who never compiles | **About even**: the rebuilds at kernel updates save about 2 minutes; the checks after each package operation cost 6 to 14 minutes with dpkg-stereo 0.1.24 as measured, or about 1 to 2.5 minutes with 0.1.29's check, plus 2 to 2.5 minutes of monthly verification and about 1 minute of Hardware Setup |

What does not grow with time: memory.
It is a level, set by how many programs are open: each program measured here, except Discover, is 3 to 6 % smaller lean.
What grows with time: every build against the headers, and every package operation's check.

Measured earlier, and permanent: the ISO is 10.09 MiB smaller after paying for dpkg-stereo and its records, and this laptop's installed package files take 140 MB less (55,442 files projected, 24 MB of records), as the [lean-code skill](../../skills/lean-code/SKILL.md) records.
