# Privileged entry points

## Working recipe

1. Inventory the published packages, staged predecessor, action annotations and every caller before editing.
   Search the source tree and installed payloads, including compiled callers' UTF-16 strings.
   Record the source revision and each old package version separately.
2. Read the distribution's exact polkit source and pkexec manual.
   Confirm canonical-path matching, argument matching, environment filtering and PAM additions from that revision.
3. Give an action with retained authorization a program path of its own.
   Prefer a separate executable that accepts only the intended operation and constructs its trusted context directly.
   Its behavior must remain restricted when invoked directly, with a forged argv0 or through a symlink.
   Do not expose a switch that turns that executable into a general command runner.
4. Keep the normal CLI usable by package tools that inherited a privileged parent's environment.
   An installer launched through pkexec can pass that environment to apt, dpkg and maintainer scripts.
   An inherited variable does not establish which action authorized a descendant.
5. Move every privileged caller to the dedicated path and require the first engine version that installs it.
   Update both generated binary controls and source controls.
   Preserve old commands and notifications across upgrades, recording whether fresh authentication is required.
6. Reproduce the predecessor's failure before building its successor.
   In isolated systemd and polkit containers, check an inherited mark with run, keep, clear, list and dpkg's hook.
   Require the command's own observable effect as well as its status.
   A maintainer script returning zero after `|| :` does not establish that its command ran.
7. Authorize only the repair action in the attack fixture and deny generic exec.
   Check every forbidden verb, person scope, extra command, environment store override, symlink and forged argv0, then a permitted repair of a record root kept.
   Separately test real retained authorization after authentication; a rules file returning YES proves implicit authorization only.
   Keep a notification open while upgrading each predecessor and invoke its original Repair action afterward.
8. Run the owning suites and package gates, then compare each successor payload against its predecessor file by file.
   Include the new helper in the recipe's CPU-baseline check.
   Distinguish runtime results from the source inspection that justified the design.

## Source-backed facts

Inspected in ORDER 661 on 17 November 2026 against Debian testing's **policykit-1 128-1**, whose binary packages include pkexec and polkitd.
The Debian tarball contains no patches.
The source observations below were followed by the container measurements in the next section.

- `src/programs/pkexec.c:708–715` resolves the program with `realpath` while preserving original argv0.
  Lines 334–347 compare the canonical path with `org.freedesktop.policykit.exec.path` and optionally compare argv1.
  Lines 364–367 select generic `org.freedesktop.policykit.exec` if no specific action matches.
- Lines 490–521 save SHELL, LANG, LINGUAS, LANGUAGE, LC_COLLATE, LC_CTYPE, LC_MESSAGES, LC_MONETARY, LC_NUMERIC, LC_TIME, LC_ALL, TERM, COLORTERM, DISPLAY and XAUTHORITY.
  Lines 416–456 validate their values.
  SHELL must be listed in `/etc/shells`.
  Other saved values reject percent signs, `..`, and slashes except in XAUTHORITY.
- Line 779 clears the environment.
  Lines 978–1001 generate PATH, LOGNAME, USER, HOME, PKEXEC_UID, SUDO_UID and SUDO_GID.
  Lines 1009–1012 withhold DISPLAY and XAUTHORITY unless the selected action enables `allow_gui`.
  Lines 200–219 and 1068–1074 allow the configured PAM session to add environment afterward.
  Fixed stores must therefore be an invariant of the helper's own code.
- The pkexec manual's SECURITY NOTES warns that it does not validate the program's arguments.
  Retaining authorization makes the helper's own validation essential.
  A directly executed script matches its script path; the separate WRAPPER USAGE example of a script with a pkexec shebang matches its interpreter and requires the script as argv1.
  Confusing these forms can authorize every script accepted by that interpreter.
- A caller store override stripped by pkexec is no longer visible to the helper.
  Prove it cannot select a decoy store or execute that store's repair.
  Do not claim an explicit helper rejection for a variable that never reached it.
  An override passed as an argument must be rejected by the narrow grammar.
- When the old executable no longer matches the repair action, an old command or running notifier may request generic administrator authentication.
  The repair action's cached authorization is not permission to execute that general program.
  This source distinction does not replace an upgrade test with the old process still running.

Primary sources: [Debian source archive](https://deb.debian.org/debian/pool/main/p/policykit-1/), [upstream pkexec source](https://github.com/polkit-org/polkit/blob/128/src/programs/pkexec.c), [pkexec manual](https://manpages.debian.org/testing/pkexec/pkexec.1.en.html), and [polkit manual](https://manpages.debian.org/testing/polkitd/polkit.8.en.html).
Use the exact source package's manual when the rolling testing link changes.

## Traps

### An inherited mark suppresses an install step

Symptom: a maintainer script prints `through pkexec only repair --machine or repair --boot runs`, returns success after `|| :`, and its command never runs.
Cause: the installer was launched through pkexec and its descendants inherited PKEXEC_UID; the engine mistook that mark for its own restricted entry point.
Fix: make the action name a dedicated restricted program, and remove inherited-variable detection from the general engine and its library.
How found: the installer's launch chain and the engine's context constructor and verb guard were compared with failing postinst calls.
The machine observation belongs to ORDER 661's brief.
In the container reproduction, version 0.2.3 passed dpkg while the command marker was absent and keep, clear and list failed; 0.2.4 passed all five checks.

### A hook workaround leaves the shared cause in place

Symptom: dpkg's hook succeeds after dropping PKEXEC_UID, but other maintainer calls and the installer's keep operation remain refused.
Cause: one caller clears the variable while the shared engine still trusts its presence.
Fix: correct the shared boundary and remove the hook's special workaround, retaining visible nonfatal hook errors.
How found: the staged 0.2.3 hook and its own postinst were read side by side.

### A second pathname is not a second program

Symptom: the proposed entry point is a symlink to the general CLI, or its restriction depends on argv0.
Cause: pkexec matches the canonical executable path but preserves the caller's argv0 for multicall programs.
Fix: compile a separate entry point whose repair-only behavior does not depend on either name supplied by the caller.
How found: `realpath`, the argv0 preservation comment and `find_action_for_path` in polkit 128's source.

### A binary caller disappears from a text search

Symptom: an archive search finds the notifier but misses the Memory page's repair invocation.
Cause: Qt literals are UTF-16, and a byte search for UTF-8 `pkexec` misses them.
Fix: inspect both encodings and connect the installed binary to its source caller.
How found: the initial archive search missed a caller present in source; including UTF-16 found the installed Memory plugin with both paths.

## Measured in ORDER 661

On 18 November 2026, in isolated amd64 containers with systemd 262 and polkit 128, the engine 0.2.4, Plasma 0.2.1 and Memory page 0.1.9 used the dedicated compiled helper.
The shipped action kept its ID and authorization defaults and named only the helper path.
Its argv1 annotation was removed so forbidden verbs reached the helper's own refusal after authorization.

- The predecessor had four inherited-mark failures; the successor had zero, including the actual maintainer command's marker and dpkg's hook.
- The real authorization fixture used a login session, synthetic `pam_permit` authentication and an unprivileged `pkttyagent`.
  After one successful administrator challenge, the agent was stopped.
  Keep, run, clear, person repair, additional command/repair arguments, a decoy environment store and a symlink invocation all failed as expected.
  A subsequent machine repair still ran without an agent, while generic exec was denied.
  This establishes retained authorization in that fixture; it is not a password-entry or desktop-agent measurement.
- A separate probe action authorized a real script path and its symlink while generic exec was denied.
  Both ran, confirming canonical script matching.
  Caller HOME and store overrides disappeared; selected language and terminal variables survived.
  A configured `pam_env` session then added all three engine overrides and XDG_STATE_HOME, and the helper still could not find or execute the decoy's repair.
- A real notification from Plasma 0.2.0 stayed open while engine 0.2.1 or 0.2.3 and Plasma were upgraded.
  The old notifier's PID and executable hash remained unchanged.
  Its original Repair action requested generic administrator authentication for the general engine and then repaired the root-kept record.
  This preserves the offered repair with a fresh prompt; it does not extend the repair action's cached permission to arbitrary commands.
- The engine's CLI suite passed 145 checks, its systemd suite 47 and its sleep suite 55.
  The notifier session suite passed 52 checks; the Memory callback passed both permission outcomes against a test authority enumerating the installed policy.
  Both C++ packages also compiled with Clang.
- Five successor archives, including the two required HR companions, passed archive-qualified linking.
  All seven ELF files met the amd64 baseline, all 16 C-library exports remained, and no predecessor payload path, mode or symlink target was removed or changed.
  Rebuilding the native sources produced source descriptors identical to the recipe outputs and complete build records.

The private lane evidence holds the logs and hashes; no physical machine was used for these measurements.

## Further traps from the proof

### A root-marked internal text agent cannot complete authentication

Symptom: polkit 128's socket-activated helper reports `No session for cookie` when pkexec's built-in text agent tries to authenticate.
Cause: in this setup the helper socket sees UID 0 from the internal agent, whereas the authority matches the cookie against the unprivileged agent creator UID.
The helper reads SO_PEERCRED and the authority checks `agent->creator_uid` before looking up the cookie.
Fix: register a separate unprivileged `pkttyagent` for the process, wait for its notify fd, authenticate once, then stop it before testing retained authorization.
How found: the helper unit's PID/UID descriptions and journal error, followed by `polkitagenthelper-pam.c` and `get_authentication_session_for_uid_and_cookie` in the exact source.
The isolated fixture used synthetic PAM success, not a real password.

### A synthetic handler disappears under a real manager

Symptom: three general CLI-suite checks fail because a fabricated failed service is no longer listed.
Cause: the suite expects no manager; real systemd reports that the fabricated unit is not failed, so the engine correctly collects its record.
Fix: run the CLI and journal-fixture suites in the intended container without a manager, and run systemd-tests under the real manager.
How found: the suite header, its synthetic MONITOR variables and the same suite passing without the live bus.
Clear records left by failed authentication fixtures before the systemd suite's initial empty-state assertion.

### The archive solve lacks Sparky's app center

Symptom: the Memory page's link gate fails with `sparky-aptus-stereo-appcenter Depends sparky-aptus-appcenter` and no installable choice.
Cause: the gate had Debian, deb-multimedia and the edition but omitted Sparky's own signed archive.
Fix: use the image's complete public source set, including Sparky core and tiamat with its published key.
How found: the first policy-attempt solver log, compared with the image's authored apt setup.
Adding the sources qualified all five archives without changing the candidate packages or weakening dependency checks.

### An exported recipe looks like a broken checkout

Symptom: copy-recipe refuses a native source export as `not a git repository` even though it is an exported folder.
Cause: a sandbox-provided `.git` marker exists above the export, and the guard correctly refuses to assume it is absent.
Fix: set GIT_CEILING_DIRECTORIES to the known export workspace boundary for that build process.
The guard still detects a broken `.git` inside the exported source itself.
How found: the copier's ancestor check and the protected marker folders in the sandbox workspace.
