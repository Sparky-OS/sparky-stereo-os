# stereo-pictures: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Saving a per file stereo correction into the file only on consent and read back: Matroska StereoMode with `mkvpropedit FILE --edit track:v1 --set stereo-mode=V` (values 0 to 14 of RFC 9559 5.1.4.1.28.3; WebM allows only 0, 1, 2, 3, 11), MP4/MOV st3d in place only when moov is last or a free/skip box gives the 13 bytes, PNG sTER right after IHDR only when width divisible by 16 (PNG Extensions 1.4.0 section 3.6, PNG 3rd edition has no sTER). Existing line: stereo-integrations/SKILL.md:141 covers the mkvpropedit command; the st3d byte rule, WebM subset, sTER padding rule and read back check are new. (lane sview-messages-349b)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: `mark 1 -- /tmp/no-such.mkv` prints nothing, exit 0; `sparky-audio-convert flac missing.wav` prints "Converted 0 file(s) to FLAC" exit 0; `align jps -- left.jpg missing.jpg` says "left.jpg is not a stereo picture" exit 1 (a two-file request silently reinterpreted as one-picture). Cause: inputs filtered with isfile before the decision. Fix: check every input first, name each missing one, count it as failed ("Changed 0 file(s), 1 failed", exit 1) (lane no-fallbacks-tools-346f4)
- Symptom: sView on Linux always started in English whatever LANG said. Cause: `setlocale(LC_ALL, ".OCP")` fails on Linux so the locale stays "C". Fix: set the locale from the environment (commit b51de25d). Found by: red captures in English under LANG=pt_BR.UTF-8. (lane sview-messages-349b)
- Symptom: with pl, pt_BR or ja chosen by hand the menus show `[1100]Media [1200]View 3D [1500]Help`. Cause: those language folders hold only the edition's strings and sView marks a missing string with its id. Fix: English text without ids in the Stereo KWin build (commit 5874dbe1); the upstream build keeps ids for translators. (lane sview-messages-349b)
- Symptom: Display Configuration... menu does nothing and logs nothing when kcmshell6 is missing. Cause: vfork plus execvp failed in the child after the parent had reported success. Fix: report failure to start and nonzero exit in the ten languages. Note: kcmshell6 lives in libkf6kcmutils-bin (KF6), not kde-cli-tools, and without kcm_kscreen it opens its own "Could not find plugin kcm_kscreen" window and stays open. Found by: red run with no message and no log line. (lane sview-messages-349b)
- Symptom: link check in the build fails with "The read operation timed out" (60 s per read). Cause: slow mirror, nothing cached across runs. Fix: rerun the build. (lane sview-messages-349b)
- Symptom: MP4 and Matroska files marked 3D get flat thumbnails and previews (0 of 10 marked clips stereo, all 10 stereo when ffmpegthumbnailer is removed). Cause: GNOME's ffmpegthumbnailer (shipped on SparkyLinux's KDE ISO via deb-multimedia) installs freedesktop standard thumbnailers; KIO enables them by default and looks up group wildcards after every exact type (KDE BUG 453480), so ffmpegthumbnailer's `video/mp4` beat ffmpegthumbs' `video/*`. Fix: look up plugins first (name, parents, group), then standard thumbnailers, in kf6-kio +stereo3d5 `FilePreviewJob::pluginForMimeType()` with autotest testPluginBeforeStandardThumbnailer; bump ThumbnailerVersion so cached flat thumbnails are remade (2 to 3). Found by: rebuilding the KIO PreviewJob path with the user's plugin list and a fresh cache. (lane players-shared-layer)
- Symptom: half view SEI videos stay squeezed in thumbnails (8:9, top and bottom 32:9). Cause: thumbnailer did not give each eye its player shape. Fix: ffmpegthumbs uses `Stereo::Video::views()` and `matroskaPlane()` (RFC 9559 18.10 first). Proof: all marked clips side by side with red left and blue right, every view 1.78:1, 2D and 2.39:1 clips stay flat. (lane players-shared-layer)
- Symptom: the same unmarked side by side photo is stereo in the grid (256) and flat in the tooltip (512, 1024), "double preview". Cause: stereo-layer 1.5.0 `Picture::loadPair()` compared halves of the picture as decoded for the requested bound, so near thresholds the answer changed with size (5 of 41 pairs). Fix: stereo-layer 1.5.1 compares the file decoded at the comparison's own width (384), apart from the shown decode; test `pairAtEverySize` with seven sizes; kio-extras raises the thumbnailer versions (JPEG 4 to 5, image 2 to 3) so caches are remade. Found by: 41 pair crops and 82 mono phone crops (EXIF removed) at seven sizes, then through Dolphin's PreviewJob. (lane players-shared-layer)
- Symptom: a PNS fixture is not decoded by digiKam or Showfoto. Cause: the inherited PNS fixture was broken at byte 29 inside the IHDR CRC, not a decoder gap; fixed fixture inserts sTER at byte 33 before IDAT. Fix: validate chunk CRCs and decode with Pillow before diagnosing decoder support. Witnesses: MPO carries disparity MPEntry types, JPS carries `_JPSJPS_` APP3 descriptor 0x40201, PNS carries sTER mode 1. (lane digikam-mimetype-250)
- Auditing which application a MIME type offers: distinguish KService offered applications from explicit MimeType lists (Showfoto already appears through inheritance), set `XDG_CURRENT_DESKTOP=KDE` and record configured defaults separately from unconfigured fresh cache fallback preferences; a standalone digiKam DImg preview needs the loading cache, plugin initialisation and menu attachment that collection startup normally provides. Opening checks use the installed DesktopAppInfo/GIO expansion in an isolated HOME. (lane digikam-mimetype-250)
- Review rule: list the package's files and its 3D menu and refuse any output module (sView shipped six own output modules beside KWin's: Anaglyph, Interlace, PageFlip, Dual, iZ3D, Distorted). Result: only libStOutStereoKWin.so (check-one-output red on stereo3d1, green on stereo3d2), menu Enable 3D, Render resolution per eye, Display Configuration; five upstream patches prepared (reset Swap after saving a swapped layout into JPS, rows left field first flag, do not save layouts JPS cannot describe, keep right first frame sequence order, restart frame sequence pairs at the decoded key frame). Skill text states the one output contract in general; the check script and list are new. (lane sview-one-output-312)
- Symptom: an unmarked side by side PNG (3840x1080, a sunk bark texture) shows as two squares in Gwenview and as a flat pair in Dolphin, while the same pixels with an sTER chunk show in 3D. Cause: the photo policy compared the two halves block by block (`stereo_policy_picture_pair_by_content`, stereo-layer 1.4.1) and only then called the shape a pair; a pair with little depth gives few matched blocks (4 of 48 at the thumbnailer's size) and a smooth panel gives none, so the safety net let real pairs go. Fix: shape alone decides (2:1 to 3.6:1, the Photo Sphere veto first), the comparison stays as `Picture::pairByContent()` and is not asked (stereo-layer 1.17.3); raise the image thumbnailer's `ThumbnailerVersion` so flat thumbnails cached before are made again. Found by: running the policy on the installed library with ctypes in the rig image (`stereo_policy_picture_pair_by_shape` 1, `..._by_content` 0) and a line-for-line numpy port that counts flat, copied and matched blocks. The price: a phone photo or a two-monitor screenshot at 2:1 to 3.6:1 is shown as a pair until the person says Flat. (lane viewers-unmarked-and-background-504)
- Symptom: a stereo picture in Gwenview shows the colour behind the window in strips above and below it. Cause: the viewer made its whole viewport transparent while the layer was active, but the declared surface covers only the fitted picture, and the layer's window filter also cut the whole area out of the window's background. Fix: `Stereo::WidgetLayer::shownRect()` (and the area's property `stereoLayerShown`) say where the picture shows; the window's hole and the viewer's own transparent paint are that rectangle, the rest is the viewer's opaque base colour. Found by: a fullscreen magenta window under the viewer in the proof rig and the share of magenta pixels in the viewport of the left eye (12.6 percent before, 0 after). (lane viewers-unmarked-and-background-504)
- Recipe: see a see-through area in the rig: start the rig, set the virtual output to its 3D twin (`kscreen-doctor output.Virtual-0.mode.2`), run `qml6` on a window with `color: "#ff00ff"` and `visibility: Window.FullScreen`, start the viewer over it, capture both eyes with the rig's capture program and count (255,0,255) pixels inside the viewer's picture area. A flat picture must give 0; a stereo picture must differ between the eyes by the parallax. Dolphin needs `kio-extras` installed in the image, or no thumbnail is made at all. (lane viewers-unmarked-and-background-504)
- Recipe: PNG sTER padding (PNG Extensions 1.4.0, 3.6: padding := 15 - ((W - 1) mod 16), an error above 7, subimage_width := (W - padding) / 2; the encoder pads so the right subimage starts on a column divisible by eight): read from stereo-layer's `unpackPng()` and tested at 0, 1, 6 and 7 columns (`PictureTest::sterPadding`); Qt's reader (qt6-base png patch) applies the same formula and only reports the mark. (lane viewers-unmarked-and-background-504)

## Measured facts

- sView save facts: JPS cannot describe columns, checkerboard, quincunx, green magenta, yellow blue; lossless JPEG (SOF3) has no DQT for the JPS section to follow; red cyan anaglyph keeps its swap because it has no reversed layout; the snapshot save (Ctrl+S, .pns) writes sTER through FFmpeg's pngenc for any width without padding, breaking the divisible by 8 rule; Matroska TrackCombinePlanes, ASF StereoscopicLayout and MPO eye order (CIPA DC-007 IndividualNum) are marks sView reads but cannot write. (lane sview-messages-349b)


## Shared depth choices and JPS writing (ORDER 526)

- Symptom: changing depth assembly options has no effect on a packed picture-with-depth input, whether declared or selected by hand.
  Cause: the shared load helper passes options for separate depth images but calls the packed-image helper with defaults.
  Fix: stereo-layer 1.17.4 passes the chosen options through one private unpacker for all four packed depth layouts; the existing public helper retains its default behavior and ABI.
  Found by: compare each loaded eye with direct `Picture::fromDepth` using non-default options, then compare that oracle with the defaults to prove sensitivity; cover both orders, thumbnails, in-memory pictures and swap corrections.
- Symptom: a saved JPS reopens as stereo but a segment parser finds no `_JPSJPS_` APP3 block.
  Cause: the format plugin swaps the halves and writes a right-first comment, while readers assume right-first for an unmarked JPS.
  Fix: KImageFormats stereo3d6 writes the complete VRex descriptor, reports its fields, and refuses unsupported layouts before writing; the fixed comment is removed because it could contradict explicit layouts.
  Found by: parse JPEG segments independently and reopen every write; cover the four stereo layouts, both orders, mono display choices, half-size flags, separation, comments and unchanged device bytes on refusal.
  Exporting a new JPEG and changing only an existing JPEG's metadata are distinct operations: do not claim that an encoding writer preserves compressed bytes.

## Per-file choices in the shared store (ORDER 512)

- Symptom: after a file's choice goes back to Automatic, its context menu shows the 3D entry greyed out.
  Cause: the action's state was computed on the selection change, when the new pair thumbnail had not arrived; the selection did not change afterwards.
  Fix: the view emits a signal when an item's preview pixmaps change, and the actions are updated once after a burst of them.
  Found by: a capture of the context menu after the second step of a three-step sequence (Not 3D, Automatic, Not 3D); a one-step test passes.
- Symptom: "Save the correction into the file" on a PNG says "The JPEG segments or scan data are truncated or invalid".
  Cause: the shared save parses every file as a JPEG.
  Fix: the entry point for a stored choice checks the JPEG signature first and says which formats it can write.
  Found by: reading the message bar in a capture; a test that only asserts "an error text exists" passes on the wrong text.
- Symptom: a video's swap is kept, and its thumbnail does not change.
  Cause: the video thumbnailer read the swap from the file's attribute, and the swap had moved to the store.
  Fix: every reader of a per-file choice calls `Stereo::Picture::fileChoice()`; list the readers of the old place before moving a store (`grep -rn userSwapEyes` over the published patches of every package on the layer).
  Found by: rereading the diff as a reviewer and searching the published sources for the old call.
- Symptom: `cmake` configures a program without stereo and prints no error after the layer's required version was raised.
  Cause: `find_package(StereoLayer N CONFIG)` is optional in these programs, so an older layer is "not found".
  Fix: raise `libstereo-layer-dev (>= N)` in `Build-Depends` with the CMake version, and read the configure log's feature summary.
- Symptom: `stereo_policy_file_choice stored;` does not compile in C++ ("expected ';' before 'stored'").
  Cause: the struct and the function share a name, which C allows and C++ resolves to the function.
  Fix: write `struct stereo_policy_file_choice stored;` in C++ callers.
- Symptom: `cmake` fails with "Could not open file for write in copy operation .../.git/hooks/pre-commit.tmp".
  Cause: ECM installs a git hook into a source tree that has a `.git`, and the tree was mounted read-only.
  Fix: build from a copy without `.git` (`rsync -a --delete --exclude .git`, which keeps times so the build stays incremental).
- Symptom: a measuring script reports one place with both eyes seeing both colours.
  Cause: two thumbnails 23 px apart were merged by a 24 px gap rule.
  Fix: a gap smaller than the grid's spacing; print each place's position and size and read them before the verdict.
- Recipe: drive a context menu in the rig with KWin's fake input by clicking coordinates read from a capture, one capture per menu level; entries keep their offsets from the click, so later steps reuse them.
- Measured: a two-monitor screenshot 3840x1080 set to Not 3D shows flat in the thumbnail and the information panel within 2 s; the same after a restart and after a new session with the thumbnail cache removed.

## The per-file choice as packages, and a viewer on the shared menu (ORDER 551)

- Symptom: a picture set to "Not 3D", or given a packing, in the file manager opens in the viewer as if nothing was chosen, while the file manager's thumbnail follows the choice.
  Cause: the viewer decodes a document it already holds in memory through `Picture::fromReader()`, which knows no path; the store was applied only by `load()` and `loadPair()`.
  Fix: `Picture::fromReader(path, ...)` and `Picture::fromImages(path, ...)` (stereo-layer 1.18.0), which apply the stored choice as `load()` does, a stored packing over the file's mark included.
  Found by: listing every caller of the layer's decode functions in the viewer's adapter and comparing with the functions the store's change touched.
- Symptom: in the viewer, choosing an input packing for a file that declares its layout does nothing, and only "Swap eyes" corrects it.
  Cause: a caller's packing comes after the file's mark in `decide()`; only a packing kept for the file in the store comes before it.
  Fix: the viewer's per-file entries write the store instead of a session variable.
  Found by: a JPS whose descriptor says left eye first over pixels that are right eye first, opened in the published viewer with "Side by side, right eye first" chosen: the left eye still saw the right view.
- Symptom: a new field would be handy in `Picture::Options` (say, "this packing overrides the mark").
  Cause, and why not: programs built against the older header construct `Options` themselves and pass it by reference; a longer structure makes the library read past theirs.
  Fix: a new function or overload, never a new field, while programs built against the older library are still installed (the thumbnail worker of an earlier round was).
- Symptom: a shortcut of an entry that left the menu stops working.
  Cause: a shortcut works on an action that a shown widget holds; an action that is only in the action collection and in no menu is held by none.
  Fix: `window->addAction(action)` for each action that keeps its shortcut.
- Symptom: a program's swap action, connected to `toggled`, writes the store again each time the program sets its mark from the store.
  Fix: connect to `triggered`, which only the person causes; set marks under a `QSignalBlocker`.
- Symptom: `cmake` stops with "static assertion failed: No Q_OBJECT in the class with the signal".
  Cause: a signal was added to a `QObject` subclass that had no `Q_OBJECT` macro.
  Fix: add the macro (the build's automoc picks the header up).
- Symptom: two programs that both listen for renames would, with a plain "move the entry" call, lose it: the second finds nothing at the old path and clears the new one.
  Fix: the store's move changes nothing the second time; it tells a record that was just carried (it names the device and inode of the file now at the path) from the record of a file that the move overwrote (another inode).
  Found by: writing the test for "a second program saw the same rename" before the code.
- Symptom: the test of the D-Bus follower fails at once with "Could not get password database information for UID of current process" and "dbus-run-session: EOF reading address from bus daemon".
  Cause: the test container runs as a numeric user that has no line in `/etc/passwd`.
  Fix: mount a passwd and a group file that name the user.
- Symptom: `ctest -R 'policy|picturetest'` passed through an environment variable prints "No tests were found!!!".
  Cause: the quotes arrive as part of the pattern.
  Fix: pass the pattern without quotes.
- Recipe, the red controls of the store kept in the suite or beside it: the collision and concurrent-writer test builds the store's source with a hash mask of 0 (every path in one entry file); the same test built without the lock is registered with `WILL_FAIL` (45 of 320 choices survived in one run); a prune and a move that do nothing fail 40 and 14 checks of `policytest`.
- Measured: one writer's lock (`flock` on a file in the store's folder) with eight processes writing 80 choices each into one entry file: 5.4 s for the whole test on a busy station, every record kept.
- Measured, not yet decided (ORDER 551, milestone 2): a file moved to the wastebin keeps its per-file choice only until the store's next write, since the write's prune finds nothing at the file's path; restored at once, or by the file manager's undo, it has its choice, restored after a write it has none. The file manager then still draws the thumbnail it cached with the choice, while a viewer shows the file without it. Three ways to carry it were listed, none built: the prune keeps a record while a wastebin's info file names its path (`Trash/info/*.trashinfo`, `Path=`); the move listener follows the two `FileMoved` signals of a trashing and an undo (a restore announces none, so this alone is not enough); the record's device and inode re-identify the file after a restore on the same file system. Whichever is built, the cached thumbnail needs its own answer.
- Measured (same order): the file manager offers "3D Input Format" for a file with a pair preview or a stored choice only; an unmarked top and bottom picture or half side by side film is flat with no such entry. A viewer on the shared menu offers the list for any local picture, and a choice made there gives the file the entry in the file manager. No program gave an unmarked film a choice in that round.

