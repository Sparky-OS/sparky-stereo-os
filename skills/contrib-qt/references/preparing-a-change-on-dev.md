# Preparing a change on Qt's dev from a fix made on our release (ORDER 603, 2026-11-15)

Written on 2026-11-15 from qtbase `dev` d8133df56f6, qtmultimedia `dev` d47e5cc40 (13 Nov), qtshadertools `dev` e2f91f8, PipeWire 1.6.9, GCC 16.2.
Check freshness first: `dev` moves daily, and the project's own contribution rules win over this page.
Goal: a fix found on our 6.11 build becomes a Gerrit change that builds on `dev`, with its test red without the fix and green with it.

## Recipe

1. **Search first** (nothing written before this).
   `git log -S'the_call' -- path` on a full clone of the module (`git fetch --unshallow`; a depth-300 clone hid the commit that introduced a call).
   Jira answers anonymously: `curl -G https://qt-project.atlassian.net/rest/api/2/search/jql --data-urlencode 'jql=project = QTBUG AND text ~ "word"' --data-urlencode 'fields=key,summary,status,created'`.
   Gerrit answers 403 to the REST API without an account and asks for a login on git over HTTP: say in the report that open changes were not searched.
2. **Build qtbase `dev` once** (about 45 minutes at `-j4`, 1537 steps) in a Debian testing container with only the headers it needs, then install it to a prefix:
   `cmake -G Ninja -S qtbase -B build -DCMAKE_INSTALL_PREFIX=PREFIX -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF -DINPUT_opengl=no -DFEATURE_xcb=OFF -DFEATURE_widgets=OFF -DFEATURE_dbus=OFF -DFEATURE_sql=OFF -DFEATURE_printsupport=OFF -DFEATURE_xml=OFF -DINPUT_openssl=no -DFEATURE_vulkan=OFF -DFEATURE_icu=OFF -DFEATURE_fontconfig=OFF -DFEATURE_xkbcommon=OFF -DFEATURE_glib=OFF` then `cmake --build build --parallel 4` and `cmake --install build`.
   Core, Gui, Network, Concurrent and Test are enough for qtmultimedia's unit tests.
3. **Build qtshadertools `dev` against it** the same way (qtmultimedia needs `Qt6ShaderTools`; a few minutes).
4. **Build qtmultimedia `dev`** with plain cmake, not `qt-configure-module`: `cmake -G Ninja -S qtmultimedia -B b -DCMAKE_PREFIX_PATH=PREFIX -DQT_BUILD_TESTS=ON -DFEATURE_ffmpeg=OFF -DFEATURE_gstreamer=OFF -DFEATURE_pipewire=ON -DFEATURE_linux_v4l=ON` (with libpipewire-0.3-dev and libspa-0.2-dev installed), then `ninja -C b tst_NAME`.
   The V4L2 and PipeWire code is in Qt Multimedia's core library on `dev`, so no media backend is needed for their unit tests; "No media backend found" is only a warning.
5. **Red and green from one commit.**
   Commit the fix with its test on a branch, add a second detached worktree of that commit in which only the fix line is reverted (`sed -i`), build both, and run the same test binary in each: `./tst_NAME -v1 TESTFUNCTION`.
   A crash is a valid red: exit status 139 and the last PASS row before it name the row that broke.
6. **Control.** Build the unmodified `dev` (a third worktree) and run `ctest -j4 --timeout 120` in it and in the branch build: the failing set must be the same.
   Without a media backend this was 11 tests (`module_includes` and ten `media-backend` integration tests) in both.
7. **Commit message in Qt's form**: subject at most 72 characters without a final full stop, body lines at most 72, `[ChangeLog][Class]` where the API behaviour changes, the plain line `AI was leveraged.`, `Pick-to:` only for a fix (not for a new behaviour), `Change-Id` from the hook (`curl -o .git/hooks/commit-msg https://codereview.qt-project.org/tools/hooks/commit-msg`, answers to anonymous callers), no `Assisted-by`, no `Signed-off-by`.
   One stacked branch per change, so a reviewer who takes the first can take the next; bundle each (`git bundle create X.bundle BRANCH ^DEV_COMMIT`) and keep `git format-patch` copies.
8. **Reviewers** from `git log --since=… --format=%B -- paths | grep ^Reviewed-by | sort | uniq -c`: the ones that reviewed those paths this quarter; Gerrit usernames come from an authenticated `/a/accounts/?q=name:` lookup, which a lane does not have.

## Traps (symptom, cause, fix, how found)

- **`qt-configure-module: cannot create //config.redo.in: Permission denied`.** It writes next to the prefix when the container user cannot; use plain `cmake -S SRC -B BUILD -DCMAKE_PREFIX_PATH=PREFIX`.
- **`Could NOT find Qt6ShaderTools … qt_internal_add_shaders unknown`.** A qtbase-only prefix has no ShaderTools; build qtshadertools (step 3).
- **`ninja: unknown target` / `cmake --build B tst_x`.** `cmake --build` takes `--target`; use `ninja -C B tst_x`.
- **A QCameraDevice list that "never changes" in a probe.** `QCameraDevice::operator==` compares ids only; `isDefault` moving is invisible to `!=`. Compare a string made of id and `isDefault` (the private `QCameraDevicePrivate::operator==` does compare it, so the signal is still emitted).
- **A private header cannot be included from a probe: `QtGui/private/qtguiglobal_p.h: No such file`.** Add `-I PREFIX/include/QtGui/6.13.0 -I PREFIX/include/QtGui/6.13.0/QtGui` and the same for QtCore, QtNetwork, plus the module build's `include/QtMultimedia/6.13.0` and `…/QtMultimedia`.
- **D-Bus in a rig container: `Could not get password database information for UID … 1000: not found`.** Append the uid to `/etc/passwd` and `/etc/group` as root before `setpriv`.
- **`spa_json_next(&it, nullptr)` crashes (SIGSEGV, `mov %rax,(%rsi)` with `rsi` 0).** It stores the start of the token in `*value` before it reads anything; always pass a `const char *` variable. Found by the test's row with a member before `name`, and by gdb's disassembly in Qt Test's own crash report.
- **A function in an anonymous namespace cannot be tested.** Declare it in the private header with `Q_MULTIMEDIA_EXPORT` (the tests link `Qt::MultimediaPrivate`).
- **`dev` moved the V4L2 code.** `src/plugins/multimedia/ffmpeg/qv4l2cameradevices.cpp` of 6.11 is `src/multimedia/v4l2/` on `dev` and its log category is `qt.multimedia.v4l2.cameradevices`; a branch made on 6.11 needs both changes. 6.12 already has the new place.

## Perks

- Qt has stereo of its own already: `QSurfaceFormat::StereoBuffers`, QOpenGLWidget stereo since 6.5 (second texture in `QBackingStoreDefaultCompositor`) and the stereo swapchain of QRhi. Faults in those are plain faults for Qt.
- The anonymous Jira REST API is the only tracker search a lane has; github.com/qt/* shows merged work on `dev` only.
