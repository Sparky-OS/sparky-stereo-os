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
These are source observations; the successor's container proofs are still required.

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
The machine observation belongs to ORDER 661's brief; its source inspection is complete, and container red/green remains a separate required proof.

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
