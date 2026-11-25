# FreeCAD's CI on a fork, and the same checks in a container (ORDER 903, 2026-11-25)

**For** anyone who must see FreeCAD's checks green before a pull request: which workflows a pull request runs, which of them run on a personal fork and what makes them see the change, how long they take, and the commands that run the same checks locally with the versions FreeCAD pins, with the runs that proved them and the traps met.

Read at `main` 8861f26a7c (`.github/workflows`, `.pre-commit-config.yaml`, `tools/lint`); the workflows change often, so read them again before relying on a line.

## What a pull request runs

| Workflow | When | Jobs | Needs secrets | Runs on a fork |
| --- | --- | --- | --- | --- |
| `CI_primary.yml` ("FreeCAD CI primary") | `pull_request` (opened, synchronize, reopened), `push` to `main` and `releases/**`, `merge_group`, `workflow_dispatch` | Prepare, Ubuntu, Lint, WrapUp | `GITHUB_TOKEN` only | yes, on GitHub's `ubuntu-latest` and `ubuntu-26.04` |
| `CI_approved.yml` | `pull_request` including `labeled` | the macOS and Windows builds, gated by labels | `GITHUB_TOKEN` | the jobs exist; they start only with the labels |
| pre-commit.ci (a GitHub App, not a workflow) | each pull request to FreeCAD/FreeCAD | the hooks of `.pre-commit-config.yaml` | the App's own | only where the fork's owner installs the App |
| `labeler.yml`, `score_prs.yml`, `backport.yml`, CodeQL, Crowdin, stale | labels, triage, backports, security scans | | various | gated by `github.repository_owner == 'FreeCAD'` or secrets |

The head of pull request 34447 (merged 2026-11-16) carries the status `pre-commit.ci - pr` and the check runs Prepare, Lint, Ubuntu / Build, Pixi builds on `ubuntu-latest`, `macos-latest` and `windows-2022`, Windows / Build, CodeQL and dependency-review (`gh api repos/FreeCAD/FreeCAD/commits/SHA/check-runs` and `/status`).
CI primary on pull requests took a median of 31 minutes (19 to 142) over FreeCAD's 40 latest successful runs (2026-11-23 to 2026-11-25, Actions API).

### Prepare decides what Lint sees

`sub_prepare.yml` lists the changed files and lines only for a `pull_request` event (step "Get files modified in changeset", `if: env.isPR == 'true'`), through `tools/lint/changed_lines.py` and the pull request's number.
On a `push` or a `workflow_dispatch` the lists stay empty, and `sub_lint.yml` skips its whole job (`if: inputs.changedFiles != ''`).
A push that creates a branch is told so: "files changed will be ignored".
**So on a fork, the checks see a change only through a pull request inside the fork:** base the fork's copy of `main` (synced to FreeCAD's, since Prepare warns when the base is more than 48 hours old), head the change's branch.
Such a pull request runs Prepare, Ubuntu and Lint unchanged; it is the fork's own, and nothing reaches FreeCAD.

### What each job checks

- **Lint** (`sub_lint.yml`, on `ubuntu-26.04`): version sync (`src/Tools/sync_version.py --check`), file-name case, pylint on changed Python files, the binding-stub smoke check (pixi and uv), the Qt string-connection check, codespell, clang-tidy on the changed lines after `package/ubuntu/install-apt-packages.sh` and a CMake configure.
  Pylint, the Qt check, codespell and clang-tidy are `continue-on-error`: they write the report and never fail the run ("warnings or notes will never fail the CI, only errors" for clang-tidy).
  clang-format is not in this job.
- **Ubuntu** (`sub_buildUbuntu.yml`, on `ubuntu-26.04`): `package/ubuntu/install-apt-packages.sh`, ifcopenshell 0.8.5 from pip, CMake 4.2.3, GCC, `cmake --preset release -G Ninja -DFREECAD_USE_EXTERNAL_COIN_PIVY=ON -DFREECAD_USE_EXTERNAL_PYCXX=ON -DFREECAD_USE_EXTERNAL_JSON=ON`, the build, the Coin node snapshot visual tests (`FreeCAD -t TestCoinNodeSnapshots` under xvfb), the C++ test executables (`tests/*_tests_run`, one minute in all), install, then the command-line and GUI Python tests on the install.
- **pre-commit** (`.pre-commit-config.yaml`): pre-commit-hooks v6.0.0 (trailing whitespace, end of file, YAML, large files, mixed line endings), Black 26.5.1 with `--line-length 100`, clang-format v23.1.0, the version sync hooks; on `src/Base`, `src/Gui`, `src/Main`, `src/Tools`, most `src/Mod` folders and `tests/src`; excluding `src/Gui/Quarter`, `src/Gui/QSint`, `src/Gui/3Dconnexion/navlib`, `.ts` files and others.

## The same checks here

Two scripts in this skill run them in containers, with the checkout mounted read-only and nothing changed in it.

### Formatting and lint: `scripts/freecad-checks.sh`

```sh
bash scripts/freecad-checks.sh --image IMAGE CHECKOUT BASE [HEAD]       # the files BASE..HEAD changes
bash scripts/freecad-checks.sh --all-files --image IMAGE CHECKOUT REV REV  # the baseline of a revision
```

It clones the checkout inside the container (`git clone --shared`), runs pre-commit with the revision's own `.pre-commit-config.yaml` (`--from-ref BASE --to-ref HEAD`), then FreeCAD's own `tools/lint` scripts with the Lint job's arguments: version sync, file case, Qt connections, codespell, pylint.
`--tools-ref REF` takes the lint scripts from another revision (a pull request's CI runs its tree merged into the target branch).
Each check prints PASS, FINDINGS or SKIPPED with the CI's own behaviour for it; the exit status is 1 when any check found something.
clang-tidy and the binding-stub check need a configured build or pixi; the build tier runs clang-tidy.

The image: Ubuntu 26.04 (the runner's release, pulled by digest) with python3, git, and in a virtual environment pre-commit 4.7.0, codespell 2.4.3 (the Lint job installs codespell unpinned with pip, `tools/lint/codespell.py` line 78) and pylint 4.1.4; about 355 MB.

```sh
docker run --name fc-lint-build --ulimit core=1 ubuntu@sha256:0d5255be560e2d2ddcfbfda88549e9e815ef29e7cd7fc62183d5709e6e2963c6 sh -c \
  'apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv git ca-certificates &&
   python3 -m venv /opt/fc-lint && /opt/fc-lint/bin/pip install pre-commit==4.7.0 codespell==2.4.3 pylint==4.1.4'
docker commit -c 'ENV PATH=/opt/fc-lint/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' fc-lint-build freecad-lint:26.04
```

### Build and C++ tests: `scripts/freecad-ci-build.sh`

```sh
bash scripts/freecad-ci-build.sh --image UBUNTU_26_04 --build DIR [--target Gui_tests_run]... [--tidy-base BASE] CHECKOUT
```

The Ubuntu job's steps in one container: the same apt script, CMake 4.2.3 checked against Kitware's published SHA-256 (`5bb505d5...ef650c23` for `cmake-4.2.3-linux-x86_64.tar.gz`), the release preset with the job's three options into `DIR/release`, the named test targets built with `-j4` and run under xvfb, and clang-tidy on the lines changed since `--tidy-base` through `tools/lint/clang_tidy.py`.
The checkout needs the revision checked out and three submodules (`git submodule update --init --depth 1 src/3rdParty/GSL src/3rdParty/OndselSolver src/Mod/AddonManager`); Coin and Pivy come from the system, as in the job.
`APT_PREPARE` names a host file to run before apt (a site's apt policy).

## Proofs, 2026-11-25

| Run | Exit | Result |
| --- | --- | --- |
| `freecad-checks.sh --all-files` on unchanged `main` 8861f26a7c | 0 | every hook Passed (whitespace, end of file, YAML, large files, mixed line endings, Black, clang-format, version push); version sync and file case PASS; 68 s with an empty hook cache |
| `freecad-checks.sh` on four commits over the 1.1.3 tag (1.1.3's hooks: clang-format v21.1.5), lint tools from `main` | 1 | pre-commit FINDINGS: clang-format rewrites 31 hunks in 8 files; Qt connections, codespell and file case PASS; version sync SKIPPED (1.1.3 has none) |
| `freecad-ci-build.sh` on unchanged `main`, target `Gui_tests_run` | see below | |

## Traps (symptom, cause, fix, how found)

- **Symptom: the check command exits 0 in a third of a second and prints no verdicts.**
  Cause: `docker run` without `-i` gives the container no standard input, so `bash -s` reads an empty script and exits 0.
  Fix: `docker run -i`; the script now also refuses a run that printed no closing line, so an empty run can never read as a pass.
  How found: the run's time (0.34 s) and the missing verdict lines.
- **Symptom: `qt_connections.py: error: unrecognized arguments: src/Gui/...` on an older revision.**
  Cause: `tools/lint/utils.py` gives `--files` `nargs="+"` on `main`; the 1.1.3 copy takes one value.
  Fix: run the lint scripts of the target branch (`--tools-ref`), as the pull request's CI does on the merged tree.
  How found: the argparse message, then `git show 1.1.3:tools/lint/utils.py`.
- **Symptom: `codespell.py` prints its findings and then a traceback in `emit_problem_matchers`.**
  Cause: the lint scripts print GitHub's problem-matcher lines with `os.getenv("RUNNER_WORKSPACE")`, which is unset outside GitHub (`os.path.join(None, ...)`).
  Fix: set `RUNNER_WORKSPACE` in the container (the script does).
  How found: the traceback's last frames (`tools/lint/utils.py`, line 56).
- **Symptom: pip ends with `uninstall-no-record-file` for `packaging` while installing pre-commit on Ubuntu 26.04.**
  Cause: `pip install --break-system-packages` tries to replace a Debian-installed package that has no RECORD file.
  Fix: a virtual environment (`python3 -m venv`), put first on `PATH`.
- **Symptom: a fork's CI run shows Lint skipped and Prepare's report says "files changed will be ignored".**
  Cause: the run came from a push or a manual dispatch; only a pull request event fills the changed-file lists.
  Fix: a pull request inside the fork. How found: `sub_prepare.yml`'s conditions and `sub_lint.yml`'s `if:`.
- **Symptom: the Developers Handbook says pre-commit covers three folders, but clang-format rewrites `src/Gui` files.**
  Cause: the handbook page (2026-04-14) is older than the configuration, which covers `src/Gui` and most modules.
  Fix: read `.pre-commit-config.yaml`'s `files` and `exclude` at the revision.
- **Symptom: clang-tidy through `tools/lint/clang_tidy.py` finds no compile database, or cannot write `clang-tidy.yaml`.**
  Cause: the script runs `clang-tidy -p build` in its working folder and writes its fixes there.
  Fix: run it from a writable folder holding a `build` link to the build directory, with absolute file paths (the build tier does).
  How found: `tools/lint/clang_tidy.py`, lines 85 to 93.
