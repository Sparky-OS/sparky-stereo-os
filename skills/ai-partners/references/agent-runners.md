# Unattended agent runners

**For whoever runs an AI partner unattended and reviews what it hands back:** Codex in `exec` mode, Claude Code, or a local model behind either.
Each lesson below was measured on the edition's work in October and November 2026, with the date it was found.
The product named is where it happened; the rule applies to any runner.

## A runner that stops after turns with no tool call

A runner that ends a session after a set number of turns without a tool call (ours stops after two) is saying that the model did not act.
Read the model's last output in the runner's log before relaunching anything.
The causes seen so far:

- **The service refused the requests.** An expired sign-in answers HTTP 401 ("Missing bearer or basic authentication", after a sign-in changed on 2026-10-22), and an exhausted quota answers with its own text ("Your workspace is out of credits", 2026-10-14 and 2026-10-16).
  The model never ran: sign in again (for Codex, `codex login --device-auth`) or wait for the quota, then relaunch.
  The hand-back's status line still says the work is under way, so a watch must also match the runner's stop line and the service's error text.
- **The model writes its tool calls as plain text.** Through Codex's `--oss` provider, DeepSeek v4 Pro wrote `<invoke name="exec_command">` into its answer, so nothing ran (2026-10-04).
  Use a model whose tool calls the runner parses (GLM 5.3 made real tool calls from its first seconds), and keep the other for plain answers.
- **The session holds input the model cannot take.** A model without image input that opened a PNG once failed every later resume of that session ("this model does not support image input", 2026-10-04).
  Start a fresh session, and keep the archived log outside the workspace: a partner that found the old log in its folder printed the old session id, and the runner resumed the broken session from it.
  Tell such a partner to check images by script, from pixel values, never by opening them.
- **The session is too long.** A session resumed across days carried about 570,000 tokens of history (2026-10-04); start a fresh one from the saved handoff.

## A runner that cannot write

- **Codex's `workspace-write` sandbox** makes every path outside the workspace read-only unless it is a writable root (`-c 'sandbox_workspace_write.writable_roots=["/path"]'`). List the build and scratch folders before launch.
- **It also mounts a read-only, empty `.git`** at the top of the workspace and of every writable root, so no repository can be created or used there (2026-10-14). Put each repository in a subfolder, made before launch, and name its path in the brief.

## A runner that will not stop

- **Killing the wrapper and the running command is not enough.** The agent process, reparented to init, keeps its turn and starts new commands; one wrote two more 15 GB repository copies within the hour (2026-10-30).
  Find it by its working directory (`/proc/PID/cwd`), since a resumed session's command line carries no workspace path, stop it and its sandbox children by PID, then check by working directory that nothing is left.
- **Never stop processes by pattern** (`pkill -f`, `pgrep -f`): the pattern also matches the caller's own command line.

## A runner that hands back to nobody

- **An unattended runner notifies no one.** Its status lives in its hand-back file, so start one watch for every running partner when it is launched, matching the status line, the runner's stop line and the service's errors together (two partners sat unseen for 40 minutes on 2026-11-01).
- **A runner that reads the hand-back's status line before it starts** (ours exits at once on `STATUS: review` or `STATUS: blocked`) needs that line set back to a working status before a relaunch.
- **Under heavy load Codex's app-server daemon** can take about three minutes to open its socket ("app server did not become ready"): nothing is broken; run again, or use `--no-daemon`.

## The shared machine (any partner, any model)

- **Nothing a partner runs may open a window or a prompt on a person's desktop.** A shell started from a desktop inherits `DISPLAY`, `WAYLAND_DISPLAY` and the session bus: an ssh password fallback opened an askpass dialog (2026-10-06), a script ran ImageMagick's `import` on the desktop and waited 14 hours for a click (2026-10-12), and a unit test showed a real dialog (2026-10-24).
  Run host commands with `env -u DISPLAY -u WAYLAND_DISPLAY -u DBUS_SESSION_BUS_ADDRESS SSH_ASKPASS_REQUIRE=never`, ssh with `-o BatchMode=yes -o PasswordAuthentication=no -o ConnectTimeout=10`, and virtual machines headless.
  A `docker pull` can call a credential helper that asks for a passphrase on the desktop: build or import base images locally instead.
- **Never follow symlinks in an unbounded scan.** One `find -L` across trees linked into each other used 80 GB of memory (2026-10-21).
  Use `find` without `-L`, `grep -r` rather than `-R`, `-maxdepth`, a `timeout` around the whole pipeline, and `git ls-files` for tracked files.
- **In a partial clone (`--filter=blob:none`), commands that read file contents download every blob they touch.** A loop of `git cherry` over 60 branches ran for 14.5 hours and grew a 50 GB temporary pack that `du` did not show (2026-10-30).
  Ask such a clone only commit-graph questions (`branch --contains`, `merge-base`, `log` without `-p`), or bound each command with `timeout`.
- **Large builds fill shared disks.** A workspace-wide `cargo test` wrote 26 GB at about 143 MB/s and filled the root file system (2026-10-22).
  Put build targets on a named scratch path, build one program at a time, delete the target after it, and stop the build below a free-space floor checked during the build, not only before it.
- **Quote every heredoc that writes text** (`<<'EOF'`): an unquoted one ran backticked words as commands, twice on 2026-10-10.
- **Every `apt-get`** in a script, container or virtual machine runs with `DEBIAN_FRONTEND=noninteractive` and `-y`.
- **Never print a credential file, even through a filter that hides the secret.** A pattern that misses one line prints it; extract only what the task needs, such as host names.
