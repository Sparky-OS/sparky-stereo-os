---
name: test-bench
description: >-
  Tests on real machines and 3D televisions with a person at the bench and a partner working remotely: baselines before
  and after, every change recoverable, clean power (UPS, NUT, the pull-the-plug test), failure domains, the television
  rules, inventory and reservations, the unattended lab model (BayLibre, LAVA, labgrid), KDE's CI run locally
  (kde-ci-local), container test harnesses (setpriv for an unprivileged uid, proot and exit status, dpkg --unpack for a
  real postrm, a read-copy of the repository for a gate). Load it when a test needs a cable, a TV or a laptop, a bench
  machine must be reserved or recovered, tests pass as root but fail for the person, a CI image lacks the edition's
  Xwayland, QSignalSpy::wait loses a signal, a KWin autotest flakes, or a kernel test could brick a board.
---

# Testing on real machines and televisions

## Working recipe

1. Name the machine, what the test changes and how the person at the bench can undo it.
2. Take a baseline, tell the person what will run and when, and keep the machine recoverable.
3. Run the test, measure, take the same baseline again, and hand back the numbers with what changed besides your work.

**Check freshness first.**
Written on 2026-11-04.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.
Prices, models and project pages named here change; check each on its own page before relying on it.

The virtual benches come before any real one.
[`stereo-proof-rig`](../stereo-proof-rig/SKILL.md) proves what the compositor hands an output, and [`vkms-stereo`](../vkms-stereo/SKILL.md) proves the kernel's 3D modes with no display at all.
A real machine and a real television are for what a virtual one cannot show: a cable, a panel, a heat limit, a driver on real silicon.

## The reliability definition, and our model

Patrick Titiano of BayLibre gave the talk "Making Your CI Lab More Reliable" at a Linux Foundation event in 2026.
His definition: a lab is reliable when we can detect, isolate and recover remotely from any failure.
We keep the three verbs and change the last word, because the model differs.

**The edition's model:** a person sits at the bench with physical access and expert knowledge, and the AI partner works over the network.
Recovery that needs hands is the person's part of the job, not a gap in the lab.
A lab is reliable here when the partner can detect a failure, isolate it to one machine and one change, and leave the person able to recover in minutes.

The unattended model of BayLibre, where nobody is nearby, is a different case with different hardware.
It is described near the end, for contributors and companies who run labs that way, after a section for the middle case: a few people sharing a few benches.

## Who does what

| Step | The partner | The person at the bench |
| --- | --- | --- |
| Before | Names the machine, the change, the expected duration and the rollback. Takes the baseline. | Says go, or says wait. Is told before anything loads the machine or reboots it. |
| During | Runs the bounded test, logs to the machine itself and to its own workspace, watches temperature and the clock. | Uses the machine as usual and may stop the test. |
| A failure | Detects it from the logs and from silence (no ping, no ssh, no new log line), stops sending commands, and says exactly what it saw. | Looks at the screen, the power light and the keyboard, and does what needs hands: a power button, a boot menu, a cable. |
| Recovery | Prepares the instructions in advance: the boot entry to pick, the file to restore, the command to run. | Follows them, or uses expert judgement and says what was done. |
| After | Takes the same baseline, writes the before and after table, lists everything else that changed. | Confirms what only eyes can confirm (the picture on the television, the sound). |

Say exactly what you need from the person's hands, in one message, with the order of steps.
A bench that waits on an unclear request costs more than one that is slow.

## Keep every change recoverable by the person

Before a change that can stop a machine from booting or from showing a picture:

- The previous kernel stays installed and its boot entry exists. Check the entries, never assume them.
- Write the boot options in use, the package versions and the display state down first (the baseline below).
- Ship a rollback with the change: a script that restores the previous packages or files, tested once on a throwaway copy, with its path told to the person.
- Do not depend on ssh as the only way back. A kernel or display test that can drop the network needs the person's keyboard, and a note saying so.
- Do not change the one thing you reach the machine by (network configuration, the ssh service, the login manager) in the same step as the test.
- Long jobs run as a systemd unit on the machine, with their state in a file, so a dropped ssh session does not kill them and a rerun resumes.
- Never test a crash on a machine that is also somebody's daily display, unless the person has chosen that window.

## Kinds of machine

**An x86 laptop or desktop with no serial port.**
The console is the screen and the keyboard, and they are the person's.
The partner reads what the machine writes down: the journal (persistent across boots), `dmesg`, the kernel's `pstore` crash records where the firmware keeps them, and a log shipped to a second machine while the test runs.
A watchdog helps only if the machine's hardware has one.
A machine that stops answering is isolated by silence: the partner stops, and the person looks.

**An ARM box with a UART.**
Most boards have a serial console on three pins (ground, transmit, receive) at 3.3 V.
Wire it once, with a USB serial adapter that has a 3.3 V setting, label the cable, and the partner can read the boot from the first line, even with the network down.
Never connect the adapter's power pin unless the board needs it, and never use a 5 V level on a 3.3 V board.
Boards differ: read the board's own page for the pins, and record that you did.
Whether a given box has its UART wired is a fact to measure and write in the bench sheet, not to assume.

**A television, as a display only.**
A television shows what the machine sends; it is not a test machine and not a player.
The rules are below.

**A virtual machine or a container.**
These are the disposable sub-labs: cheap to break, easy to repeat, one per question.
Pin the base image by digest, start each case from a fresh one, and stop everything you start.

## Power, UPS and a clean shutdown

A test that is killed by a power outage proves nothing, and a machine that is cut while writing can lose more than the test.

- **Outages freeze sessions.** A storage device that drops with the power makes every process that touches it hang, and a session whose working directory is on it freezes too. Keep work on disks that live behind the same protected power as the machine, and nothing lasting on storage without protection.
- **A UPS tells the machine to shut down, if you let it.** Network UPS Tools (NUT) reads the UPS over USB or serial and runs a clean shutdown when the battery is low. Debian packages it as `nut`. A UPS with no data cable only keeps the lights on for a few minutes.
- **The NUT server can serve other machines.** One UPS with a data cable can tell several machines to shut down, if they all hang off it and its rating covers their sum. Check the UPS's watts, not only its VA, against the real load.
- **Test the shutdown once,** with the real load, by pulling the UPS from the wall at a time the person chose, and write down how long the battery held and whether the machine stopped cleanly. Batteries age.
- **A laptop has a UPS built in.** Its battery carries it through a short outage, so a UPS adds little for the laptop itself. It also means that cutting the mains does not power-cycle it: with the battery in, a hard power cycle needs the person's hands on the power button, or the battery out. Do not buy a switched outlet for a laptop with a battery in.

**A small bench done right, as an example.**
The main machine sits behind a 2000 VA sine-wave UPS that NUT manages, so a long outage ends in a clean shutdown.
The network firewall has its own 1000 VA UPS, so the partners, the main machine and the network stay up together while the power is out.
The laptop bench uses its battery as its UPS.
The file server holds no work at all, so its power is not part of any test.
Each machine has the protection that its role needs, and nothing more.

## Failure domains

Keep each failure small.

- One question per machine and per session. A kernel test and a display test do not share a boot.
- One change per step, so a failure points at one change.
- A bench machine that the person also uses every day is a small domain only if you announce what you will do on it.
- Keep a second, boring machine (or a virtual one) that you do not touch, as the control.
- Where hardware is shared (one television, one switch), say so in the bench sheet: a failure there takes every machine behind it.

## Baselines before and after

A baseline is what the machine said before your change, kept somewhere you can compare it with.

- Inventory, kernel and package versions, boot options, the display state of each output, the GPU and Vulkan or GL strings, and the compositor's settings.
- For performance: measure cool. A processor that throttles hot makes a change look like a slowdown. Record the temperature beside each run, start each step at or below a set temperature, and compare runs from the same minutes.
- Compare like with like: the same packages, the same session, the same state of the machine. When something else changed in between (a package from the distribution, a cache refresh), write it in the table so your change is told apart.
- Keep the files small: logs, measurements, a screenshot. They are evidence for a stated setup, not for a newer one.

## Television rules

- A script never changes a television's mode or settings, and never caps a program's resolution to fit it. The person chooses the mode; the partner tells them which one to pick.
- A test never leaves traces in a program's own settings. List what the setup changes, and restore only that.
- Tests that need the person's eyes on a television wait for one testing window: collect them all, test them once, take notes first, fix after. A change after a session invalidates it.
- A television can dim, or turn its output off, after an idle time, and a dimmed or switched-off output changes what the compositor reports and stops its frame log. Before a measurement, hold the screen awake and check that frames are still being presented (see [`power-idle`](../power-idle/SKILL.md)).
- A television that keeps a list of the servers it has seen keeps every test server too: give each test media server one fixed identity and reuse it.
- Never crash-test on a television that is somebody's display.
- A recorded test on a television proves the picture only when the person has looked at it. A capture of what the compositor hands the output is proof of the stereo layout, not of the screen.

## Inventory

Label every machine, cable and adapter, and keep a sheet with one line each:

- what it is (model, firmware, kernel in use, how it is updated);
- how to reach it, by name and not by address in anything public;
- how a failure is detected, isolated and recovered, and which step needs the person;
- its power (protected or not, whether a clean shutdown is configured);
- what hangs off it (displays, adapters, the television input).

A text file does for a few machines. Snipe-IT is a free asset manager if the list grows.
The sheet with real addresses and names stays private; a public page names models only.

## A few people sharing a few benches

Between one person's bench and an unattended lab sits the common middle: a small team, a handful of machines, people nearby most of the time.
What changes is that the machines are shared, so the rules between partner and person also hold between people.
- **One bench, one holder at a time.** Before using a machine, say so where the team looks (a shared note, a channel, or labgrid's places, which make it explicit). Release it when done. A partner never starts on a machine someone else holds.
- **Each machine has a named responsible person** who answers when it needs hands, and a second who knows how to recover it.
- **Announce before load or reboot, to whoever is at that machine.** A test that reboots a machine in the middle of someone's session looks like a crash to them.
- **One inventory for the team,** with who holds what and since when, and the recovery steps written so that the second person can follow them.
- **Shared displays get a calendar.** A television or a 3D monitor serves one test window at a time; collect the tests that need it and run them together.
- **Partners reach shared benches through one coordinator,** never each on their own. One place decides which partner may load which machine, and the people know whom to ask.

## The unattended lab: BayLibre's model

When nobody is near the machines, the lab has to recover itself, and then the hardware matters.
These are the ideas and tools from Patrick Titiano's talk and the projects it names.
Use them when you run a board farm, a business lab or a remote CI, not as a baseline for a bench with a person at it.

- **Treat the lab as infrastructure.** Every board remotely observable, controllable and recoverable, never depending on ssh or on someone walking over.
- **Reliable power from the start.** Several protected circuits, not one outlet with power strips. A power distribution unit (PDU) that switches outputs one after the other keeps the inrush current down and lets you power-cycle a whole sub-lab. A UPS filters the grid and gives a clean shutdown.
- **Small independent sub-labs.** Modular, standalone, movable; maintaining one leaves the rest running.
- **Standard packages only.** Depend on the distribution's own software, so a rebuilt lab behaves like the old one.
- **Label and inventory everything.** The talk uses Snipe-IT.

Tools, each credited to its own project:

| Tool | What it gives | Where |
| --- | --- | --- |
| Copilot (BayLibre) | One USB cable to a board: power switching, a serial console and extra GPIO lines, with udev rules and no extra software. Open hardware, MIT licence. | [github.com/BayLibre/Copilot](https://github.com/BayLibre/Copilot), [docs](https://baylibre.github.io/Copilot/) |
| LabRack (BayLibre) | A 1U rack front panel and PCB: isolated 5 V and 12 V rails, three Ethernet passthroughs, fan connectors, a circuit that presses a power button. | [github.com/BayLibre/Labrack](https://github.com/BayLibre/Labrack) |
| NanoKVM (Sipeed) | An IP-KVM: the target's screen over HDMI, an emulated keyboard, mouse and USB storage, for what a serial console cannot reach (BIOS and boot menus). GPL-3.0. | [github.com/sipeed/NanoKVM](https://github.com/sipeed/NanoKVM) |
| Snipe-IT | Asset and inventory management. AGPL-3.0. | [github.com/grokability/snipe-it](https://github.com/grokability/snipe-it) |
| LAVA (Linaro) | A continuous integration system that deploys operating systems to physical and virtual hardware and runs tests. GPL-2.0 or later. | [docs.lavasoftware.org](https://docs.lavasoftware.org/lava/), [gitlab.com/lava/lava](https://gitlab.com/lava/lava) |
| labgrid | A Python library and a remote layer for controlling boards (power, serial, bootstrap), used with pytest. LGPL-2.1. | [github.com/labgrid-project/labgrid](https://github.com/labgrid-project/labgrid) |

Reach: VLANs on the lab's switch keep boards apart from the home or company network, and WireGuard or Tailscale gives remote people a way in.

**An IP-KVM and a television.**
An IP-KVM takes the target's HDMI output as a monitor, so on a machine whose only HDMI goes to a television, it would take the television's input.
Either use a model with an HDMI loop-out that keeps the television in the chain, or a splitter, and then test that the television still reports the 3D modes: a device in the HDMI path changes the EDID the machine sees, and EDID is what decides the 3D modes ([`vkms-stereo`](../vkms-stereo/SKILL.md)).

### Connecting a bench to LAVA or labgrid

Do this when a contributor wants the bench to run tests for others without the person at the keyboard.
The names below are the projects' own; read their current documentation for the exact syntax before you write a configuration.

1. **Make each machine controllable by a command.** Power on and off (a switched outlet, a PDU, Copilot) and a console (a UART adapter, or an IP-KVM's serial channel). A machine with only a screen is a manual machine; say so.
2. **Pick the layer.** With labgrid: a coordinator (a gRPC service that tracks places and who holds them), an exporter on the host that has the cables (it publishes resources such as a USB serial port or a network power port), and clients that must acquire a place before using it. With LAVA: a server and a worker on the host with the cables, and a device entry that tells LAVA how to power the board and how to reach its console.
3. **Describe the machine,** the way the project asks: labgrid resources and drivers for a target, a LAVA device type and device description.
4. **Run one test by hand first,** a boot to a login prompt with the power cycled through the lab's own command. Then automate.
5. **Reserve, never share by accident.** Mark a board unavailable or acquire its place before a person works on it by hand.
6. **Keep the secrets and addresses private,** in the lab's own configuration, never in the edition's public repository.
7. **Add the baseline** (above) as the first test of every run.

### A board farm for upstream work: obey the project's CI from the start

This is the edition's own practice, added to the talk's model.
The best use of a board farm for a contributor is to run the upstream project's own CI on your own bench from the first commit.
- Run the project's jobs as they are: the same images, the same steps, every job including the lint ones.
- For hardware jobs (kernel, DRM, display), the bench plays the part of the project's lab: KernelCI, for example, runs kernels on real boards through LAVA.
- Iterate on your bench, never on the project's runners. Their CI is shared infrastructure the project pays for, and each failure mails its maintainers.
- Push only what is already green on your bench. The pipeline that runs after the push is the confirmation, not the test loop.
- When a project requires a passing pipeline before merging, the branch behind a merge request must run its pipeline. Skip CI only for documentation and fork-only branches.
- When your work needs something the project's CI images lack, change the CI on your fork only, in a commit marked as fork-only, and never put that commit in the upstream request.
- A failure that also happens on the unpatched tag is not your container's fault until you have checked: see whether the project's own runners fail the same way, and look for the project's later fix to its CI before you push.
- For KDE, [`kde-ci-local`](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/tools/kde-ci-local) reproduces KDE's CI jobs locally.

## Credits

Patrick Titiano and BayLibre for the talk "Making Your CI Lab More Reliable", and for Copilot and LabRack.
Sipeed for NanoKVM, Linaro and the LAVA contributors for LAVA, the labgrid project, and the Snipe-IT authors.
Network UPS Tools and its contributors.
Each is quoted from its own pages and licences, checked on 2026-11-04.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (13 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
