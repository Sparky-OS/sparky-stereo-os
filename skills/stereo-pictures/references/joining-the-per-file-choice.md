# A program joins the shared per-file choice

**For whoever moves one more viewer, album or player onto the shared per-file 3D choice.**
Written on 2026-11-14 from the work that moved Koko (QML), KPhotoAlbum and digiKam with Showfoto (QWidget) onto it, after Dolphin and Gwenview; stereo-layer 1.19.0.
Extended on 2026-11-15 (stereo-layer 1.19.2): the program's own "Enable 3D" against the file's "Not 3D", a message from a worker thread, and driving digiKam with a collection in the proof rig.
Read [the per-file choice: one store, one menu](../SKILL.md#the-per-file-choice-one-store-one-menu) first: it says what the store is, why it is not the program's own configuration and not an attribute of the file, and how the choice follows a rename.
This page is the recipe for the program's side, for both toolkits, with the proofs and the traps.

The rules it serves, from [`sparky-stereo`](../../sparky-stereo/SKILL.md#part-one-the-contract): never touch the person's file on your own; the definitive eye swap is the output's, a program offers only the per-file correction; no correction for 3D is offered on 2D content; the packing list is the whole list, never a part of it.

## What "joined" means

A program has joined when all of this holds:

1. It decodes every local file through the layer **with the file's path**, so the stored choice applies.
2. Its per-file entries (input packing, Not 3D, the swap, saving into the file) are the layer's one menu, not a list of its own.
3. It keeps nothing per file itself, and nothing that corrects every file at once (a swap for the whole program is the output's, in Display Configuration).
4. What it kept per file before was carried into the store once, or it kept nothing (say which, with the evidence).
5. A choice follows a file the program itself renames or moves, and one the desktop's file jobs rename or move.
6. A picture it shows flat is offered no swap and no save.
7. It writes the person's file only through the layer's "Save the correction into the file".

## First: what the program does today

Do this from the **published** package, not from a folder in a build tree: unpack its `debian.tar.xz`, read `debian/patches/series`, and in the stereo patch find

- the menu: its entries, their shortcuts, which of them correct a file and which only choose a view;
- where each choice lives: a member of a menu or page object (the session's), a configuration file (the program's, lasting), a per-file state file, an attribute on the person's file;
- every call that decodes: `Picture::load`, `loadPair`, `fromReader`, `fromImages`, `WidgetLayer::setSource`, the QML `StereoPicture`.

What was found in the three programs, as a guide to what to look for:

| Program | The choices were | Kept where | To carry |
| --- | --- | --- | --- |
| Koko | five packings, an anaglyph pair, a swap, a view, one set for **every** picture of the page | a `QtObject` of the page, for the session | nothing |
| KPhotoAlbum | five packings, an anaglyph pair, a swap, a view | members of its menu, for the session | nothing |
| digiKam, Showfoto | the same per picture area; the view also in `digikamrc`, `[Stereo 3D]` `View` | the adapter (session); the view lasting, for the whole program | nothing: the lasting view is the program's own and stays |

A choice object shared by every delegate of a view, as Koko's was, is a correction of every file at once: its swap was a swap for the whole program.
That is the thing to look for in a QML program.

## Recipe for a QWidget program

1. **Raise the layer** in the program's `find_package(StereoLayer N ...)` to the version that has what you use, and in `Build-Depends`; keep `-DCMAKE_REQUIRE_FIND_PACKAGE_StereoLayer=ON` in `debian/rules`, or an older layer is "not found", CMake prints no error and the program is built without stereo.
2. **Put the layer's menu where the per-file entries were.**

   ```cpp
   m_fileChoice = new Stereo::FileChoiceMenu(this);
   addMenu(m_fileChoice);                       // "3D Input Format"
   connect(m_fileChoice, &Stereo::FileChoiceMenu::changed, this, &Menu::fileChanged);
   connect(m_fileChoice, &Stereo::FileChoiceMenu::failed, this, &Menu::failed);
   ```

   Give it the file whenever the picture shown changes, and say whether it is shown as a pair:

   ```cpp
   m_fileChoice->setShownAsPair(shownAsPair);
   m_fileChoice->setFiles(path.isEmpty() ? QStringList() : QStringList{path});
   ```
3. **On `changed()`** decode the file again, and tell the other programs: `org::kde::KDirNotify::emitFilesChanged(urls)` where the program links KIO, or the same signal sent with Qt D-Bus where KIO is optional (`QDBusMessage::createSignal("/", "org.kde.KDirNotify", "FilesChanged")` with the list of URLs as text).
4. **On `failed()`** show the message where the program shows its errors. The layer's message names the file and the reason; do not replace it.
5. **Keep the shortcuts** of the entries that left the menu: an action with the old shortcut, added to the window (`window()->addAction(action)`; a shortcut works only on an action a shown widget holds), which triggers the layer's own action (`m_fileChoice->swapEyesAction()`) or writes the store (`Picture::fileChoice()`, change one field, `Picture::setFileChoice()`).
6. **Keep what the program owns**: which eye is shown is a view, not a correction, and stays the program's; so does the switch that shows everything flat, which is the program's "Enable 3D": the layer's `Stereo::Enable3DAction`, never an entry of the program's own (see [the program's Enable 3D](#the-programs-enable-3d-and-the-files-not-3d)).
7. **Decode with the path.** `Picture::load(path, options, mode)` and `WidgetLayer::setSource(path, options)` apply the store. A document held in memory (an editor) uses `Picture::fromImages(path, image, ...)` or `fromReader(path, ...)`; the forms without a path ignore the store.
   Pass only the program's own view in `options`: a packing or a swap passed by the caller is a session choice over the file's.
8. **Follow renames.** Make one `Stereo::FileChoiceMoves` and decode again on `carried()`. If the program renames or moves files with its own code (a photo manager does), call `Stereo::Picture::moveFileChoice(from, to)` after each successful rename, for a folder too: the desktop's file jobs never announce those.
9. **Carry old per-file state once** with `Picture::adoptSwapEyes(path, swap)`, record that it was done, and never read the old entries again ([the store's recipe](../SKILL.md#recipe-put-a-viewer-on-the-shared-menu-and-store), step 6). When the program kept none, write that in the changelog.

## Recipe for a QML program

Since stereo-layer 1.19.0 the module `org.sparky.stereo` has the menu's QML form: `FileChoice` (the state and the acts) and `FileChoiceMenu` (a Qt Quick Controls menu built from it).
Both are faces of the same list as the widgets' menu, so the entries and their words are the same and nothing is repeated in QML.

1. **One `FileChoice` for the picture shown**, and the menu:

   ```qml
   import org.sparky.stereo as Stereo

   Stereo.FileChoice {
       id: fileChoice
       sources: [page.currentPictureUrl]          // a URL that is not a local file is offered nothing
       shownAsPair: page.currentPictureIsAPair     // false: no swap, no save
       onChanged: page.stereoRevision += 1         // the pictures shown decode again
       onFailed: message => applicationWindow().showPassiveNotification(message, "long")
   }
   Stereo.FileChoiceMenu { choice: fileChoice }    // a popup, or a sub-menu of the program's own 3D menu
   ```
2. **Show the file again on `changed()`**: `StereoPicture.refresh()` decodes its source again; anything of the program's own that decides "is this a pair" must decide again too.
3. **Remove the per-file properties** the program passed to `StereoPicture` (`inputLayout`, `inputOrder`, `anaglyph`, `swapEyes`): the item decodes with the file's path and the store applies. Keep `view`.
4. **Shortcuts** act through the object: `fileChoice.swapEyes = !fileChoice.swapEyes` (when `fileChoice.swapEnabled`), `fileChoice.choose("mono")`. Entry names do not change with the language, and they are the Stereo3DLayout words a file's mark uses for the same thing, so the idea has one name everywhere: `sideBySideLeftFirst`, `sideBySideRightFirst`, `topBottomLeftFirst`, `rowInterleavedRightFirst`, `depthSideBySidePictureFirst`, `anaglyphCyanRed`, `mono` for Not 3D, and `automatic` for no choice; `fileChoice.chosen` is the name of the file's entry.
5. **A Kirigami action list cannot hold a Controls menu.** Give the hidden-actions list one action that opens the program's 3D menu as a popup, and put the layer's menu inside that popup.
6. **Keep the stereo QML in files of their own**, loaded with `Loader.setSource(Qt.resolvedUrl(...))`, when the program must also build without the layer: a file that imports `org.sparky.stereo` does not load there.
7. **Renames need no code**: a program with a `FileChoice` keeps every file's choice with it when the desktop's file jobs move it, and `changed()` says so for the file the object names.
8. **Packaging**: the program needs the module at run time through `libstereo-layer1`, which depends on `qml6-module-qtquick-controls` and `qml6-module-qtqml-models`; a program with `dh_qmldeps` names the module in `debian/qmldeps.overrides` (`org.sparky.stereo libstereo-layer1`).

## The program's Enable 3D and the file's Not 3D

Two ideas, two names.
"Not 3D" in the layer's per-file menu is an **input correction of one file**: this file is not a pair, kept in the shared store, for every program.
A program's switch that shows **everything it shows** flat is the first of a program's 3D options in the edition's contract ("enable 3D, render resolution per eye, and a shortcut to Display Settings"), switched off.
Before stereo-layer 1.19.2 the album programs called that switch a second "Not 3D", beside the file's; now it has one entry and one wording in the layer, the words Haruna and sView already ship for the same option ("Enable 3D", in the ten languages).

- **Widgets:** `new Stereo::Enable3DAction(parent)` (in `filechoicemenu.h`): checkable, checked when made, its objectName `stereo_enable_3d`, its words and tooltip from the layer's catalogues. Put it at the top of the program's 3D menu, give it the program's shortcut (Alt+Shift+N in the album programs, where their "Not 3D" was), add it to the window (`window()->addAction()`), connect `triggered(bool)`.
- **QML:** `Stereo.Enable3DAction { }` from `org.sparky.stereo`, a Qt Quick Controls `Action` with the same words (and a `toolTip` property); use it as a `MenuItem`'s `action`.
- **Map it onto what the program already keeps.** The album programs kept one view value (Stereo, left eye, right eye, or 3 for every picture flat); keep that value and its lifetime (the session, or the program's settings), and make Enable 3D off write the flat value, Enable 3D on write back the eye view chosen last. Nothing downstream of the value changes, and a setting saved by the published version still reads the same.
- **Choosing an eye view enables 3D again**, as choosing "Stereo" used to leave "Not 3D": the eye entries stay a group of their own below the switch.
- **It writes nothing to the store**: the test toggles it and compares the store's listing before and after.
- **The file's Not 3D still wins over a one-eye view**: with 3D enabled and the file's stored view Mono, pass `View::Stereo` (a caller's one-eye view would cut the file in half).

Proof in the rig, per program: a marked pair in 3D; Alt+Shift+N: 0 pixels differ between the eyes and the store's records as before; the 3D menu captured with "Enable 3D" unchecked at its top and the file's "Not 3D" inside "3D Input Format" (with 3D off the swap and the save are greyed, as for any picture shown flat); Alt+Shift+N again: the pair; off, then a restart: off again only where the program keeps it in its settings (digiKam and Showfoto, `[Stereo 3D] View=3`).

## A message from a worker thread

A photo manager renames and moves files in jobs on worker threads, and a stored choice that cannot follow such a file (the store cannot be written) must reach the person, not only the log.

- Build nothing of the window in the worker. Post to the main thread: `QMetaObject::invokeMethod(qApp, [error] { tell(error); }, Qt::QueuedConnection)` (Qt, "Synchronizing Threads": a queued call runs in the receiver's thread).
- In the main thread, gather the messages and show them once the event loop runs again (`QTimer::singleShot(0, ...)`): a job that moves a hundred files gives one window, not a hundred.
- **Give the message a window that stays: the program's main window** (the first visible `QMainWindow` among `QApplication::topLevelWidgets()`), never `activeWindow()`. When the queued call runs, the active window is the job's own progress dialog (digiKam's renaming), which closes at once and takes a child message box with it: nothing shows. Found in the rig by preloading two builds of the one exported function (`LD_PRELOAD` of a small library defining `Digikam::stereoFileMoved`, which calls from inside the program's library reach through the PLT): parented to the active window no window appeared; parented to the main window, digiKam's window titled "3D" did, the choice in both cases still at the old path. A stand-in like that tests a fix in minutes where the program's package takes an hour.
- Wrap the layer's own message (`Picture::moveFileChoice()` returns it translated: which path, why) in one sentence of the program's that says what to do: "%1 Until its 3D choice is made again in the 3D menu, the file is shown as its own marks say."
- **Do not report it through the job's error signal.** digiKam's `IOJob::signalError` feeds `DIO::slotResult()`, which skips the job's own bookkeeping (album dates, collection rescans) whenever a job has errors: a carry that failed would change what digiKam does with a move that succeeded.
- A folder digiKam moves to another device is copied and removed (`QDir::rename` fails across devices): carry it after the removal succeeded; a file is moved with `QFile::rename`, which copies across devices itself and returns true, so the existing call after it carries.

## Driving digiKam with a collection in the rig

`digikam FILE` opens a preview window of its own; the album view, the light table, the slide show and digiKam's own file operations need a collection.

1. **No first-run assistant:** `main.cpp` runs it when `digikamrc` has no `[Album Settings]` group or a `[General Settings] Version` starting with 0.5: write both into `$XDG_CONFIG_HOME/digikamrc` (the rig's session sets `XDG_CONFIG_HOME` to a folder of its own).
2. **The database once:** `digikam --database-directory DB` makes `DB/digikam4.db`, then stops at its Collections page; end it by its PID.
3. **The collection:** add it as digiKam itself does when Solid names no volume (`CollectionManager::addLocation`'s fall back, `CoreDB::addAlbumRoot`): `INSERT INTO AlbumRoots (type, label, status, identifier, specificPath, caseSensitivity) VALUES (1, LABEL, 0, 'volumeid:?path=FOLDER', '/', 0)`. A second collection on a tmpfs (`--mount type=tmpfs,dst=FOLDER,tmpfs-mode=1777`) is another device for a move across devices; without the mode the tmpfs is root's and digiKam's move fails with only a notification.
4. **Start for the case** with `--database-directory DB`; Escape closes the model-files dialog; maximise the window with a KWin script so positions repeat.
5. **Acts, by keys and the pointer:** F2 renames the selected picture (type the name, Enter); Shift+F2 renames the selected album; a drag (fake input `p:272`, a few `m:` steps, `r:272`) onto an album in the tree opens a drop menu whose "Move Here" is clicked (60 px right, 9 px up from the drop point); the toolbar's Light Table opens it with the selected picture; Slideshow starts at the album's first picture (Page Down steps on); Alt+Shift+3 opens the slide show's 3D menu; View, then Up (the last entry), then Right opens the preview's 3D menu.
6. Read the store after every act (paths followed or not) and the files' bytes and times at the end.

## Rules that are easy to get wrong

- **A stored "Not 3D" loses to a caller's one-eye view.** The layer lets a field the caller sets win over the stored one, and "left eye only" is such a field. A program with its own eye view passes `View::Stereo` for a file whose stored view is `View::Mono` (`Picture::fileChoice(path).view`), or a file the person set to Not 3D is cut in half.
- **One eye of a pair is still a pair.** With a one-eye view the layer returns a picture that is not `isStereo()`. For `setShownAsPair()` also count `picture.source != Picture::Source::None`, or the swap is greyed exactly when the person looks at one eye to judge it.
- **The list is offered for any local picture, the swap only for a pair.** An unmarked picture gets its packing by hand from the list, so a viewer keeps the list for a picture it shows flat; `setShownAsPair(false)` then takes the swap and the save away. (A file manager offers the menu only for a file with a pair preview or a stored choice.)
- **No new sentence.** The per-file entries are the layer's and come from its catalogues in the ten languages. The program's catalogue keeps only what stays in the program (the menu's title, the view entries); check that those exist in all ten languages, since the per-file sentences that hid a gap are gone.

## The proofs

From the installed packages, in the [proof rig](../../stereo-proof-rig/SKILL.md), on the NVIDIA card or the AMD one, one fresh program start per file.
Fixtures with one flat colour per view (a marked pair, a pair whose mark is wrong, an unmarked pair by shape, an ordinary picture), each capture read by counting colours per eye inside the picture area.

| Step | What must be measured |
| --- | --- |
| A marked pair | its left colour in the left eye only |
| The menu | a capture with the layer's sub-menu open: the whole list, the swap, the save greyed while nothing is kept |
| The swap | the colours change eyes; the store's entry says `swap-eyes=1`; taken back, the entry is gone |
| A wrong mark | as marked: the wrong colour in the left eye; after "Side by side, right eye first": the right one; the store says `layout=1 order=1` |
| Not 3D | 0 pixels differ between the eyes, both halves in each; the store says `view=3` |
| The 2D control | an ordinary picture: 0 pixels differ; the swap's shortcut changes nothing and keeps nothing |
| A restart | the corrected file is still corrected |
| A rename and a copy | `kioclient move` while the program runs: the entry's path follows; `kioclient copy`: no entry for the copy, and it shows as its mark says |
| The files | SHA-256, size, modification time, change time and attributes of every file before and after: identical (a rename moves the change time of the renamed file only) |
| The control | the published packages in the same rig: the old menu, and no store |
| The upgrade | `apt-get install --only-upgrade` of the round's names over the published set: the `Inst` lines, no `Remv` |

Read the store as text (`$XDG_STATE_HOME/stereo-policy/files/*`): one line per file with `path=`, `layout=`, `order=`, `view=`, `swap-eyes=`.
A proof that reads only the picture can pass on the wrong entry; a proof that reads only the store can pass on a program that never decoded again.

## Traps

- **Symptom:** the QML menu is "unavailable": `FileChoiceEntries is not a type`.
  **Cause:** a model class registered with `QML_ANONYMOUS` has no name a QML file can write in a property declaration.
  **Fix:** `QML_ELEMENT` with `QML_UNCREATABLE("...")`.
  **Found by:** the component's error text in the test that loads the menu.
- **Symptom:** a QML file with inline components does not load, or a binding inside one is undefined.
  **Cause:** an inline component (`component Name: ...`) cannot see the ids of the file around it.
  **Fix:** give the component a required property and pass the object in.
- **Symptom:** a test that lists the menu's rows gets an empty list.
  **Cause:** the menu is not open in a test, and an item's `visible` reads the effective visibility, false for everything inside a closed popup.
  **Fix:** tell offered rows by the model's own role (`offered`), and prove the real menu in the rig.
- **Symptom:** a JavaScript array returned to C++ gives an empty `QStringList`.
  **Cause:** the `QVariant` holds a `QJSValue`.
  **Fix:** return one joined text and split it, or convert the `QJSValue`.
- **Symptom:** in the rig, three presses of Down from "Automatic" choose "left eye first" in a Qt Quick menu and "right eye first" in a QMenu.
  **Cause:** in the Qt Quick Controls menu the separator takes a key step; in a QMenu it does not.
  **Fix:** a row count per toolkit, and always read the store after a choice: `order=0` showed it.
- **Symptom:** Right does not open a sub-menu after the popup opens.
  **Cause:** no row is highlighted yet.
  **Fix:** Down first, then Right.
- **Symptom:** the gate stops the layer's build with `previous edition dependency qualification failed` and `conflicting supplied package: libstereo-av1; provide one authoritative edition snapshot`.
  **Cause:** the "previous build" given to the gate was the build an earlier round staged, while the previous edition's snapshot is the published tree, which holds an older build of the same package.
  **Fix:** the previous build is the published one; compare the imports with the staged build by hand (`nm -D`) and say so.
  **Found by:** the line above the conflict names the previous package that failed.
- **Symptom:** a long build ends at its last step with `stereo imports lost: _ZN6Stereo7Picture10fromImages... (the previous build called them)`.
  **Cause:** moving a program onto the store retires calls by design (the pathless `fromImages()` or `fromReader()` of an editor, `userSwapEyes()` of a file manager), and the link gate blocks a lost stereo import unless the source declares it.
  **Fix:** before the build, list the stereo imports of the **published** binaries and compare them with what the new code calls: `nm -D --undefined-only FILE | grep -E 'N6Stereo|stereo_'` on every library, plugin and program of the published packages; each one that will be gone goes into `debian/sparky-lean-retired-stereo-imports` with its reason ([a stereo call retired on purpose](../../edition-packaging/references/lessons-2026-11.md#a-stereo-call-retired-on-purpose-order-551-milestone-2)).
  **Found by:** asking, with a three-hour build about to start, what the gate would compare.
- **Symptom:** in a development image a program's core library fails to link with `undefined reference to Stereo::FileChoiceMenu::setFiles(...)` and every other function newer than the packaged layer, while two smaller programs linked in a sister image.
  **Cause:** the image holds the packaged layer and a newer one installed over it with `cmake --install`; the CMake package then has two target files, `StereoLayerTargets-none.cmake` (the package's build type) and `StereoLayerTargets-relwithdebinfo.cmake` (the hand build's), and a program configured as `Release` takes the first, which names the old library file.
  **Fix:** remove the stale target file in that throwaway container and configure again; or configure the program with the build type the newer layer was built with. A package build never meets this.
  **Found by:** the undefined names were exactly the functions added since the packaged version.
- **Symptom:** a proof says the program's own lasting setting was not kept (`[Stereo 3D]` `View` missing from its settings file, pictures stereo again after a restart).
  **Cause:** the proof ended the program with a signal, and a KDE program writes its settings at a clean exit.
  **Fix:** leave the program as a person does (Ctrl+Q) wherever the step is about what it remembers; end it by signal only where nothing must be remembered.
- **Symptom:** making a development image stops with `Packages were downgraded and -y was used without --allow-downgrades`.
  **Cause:** the base image carries a newer build that an earlier lane installed by hand, and the edition's pin makes the published one the candidate.
  **Fix:** in a throwaway development image, `--allow-downgrades`; a proof image is upgraded by name from a repository instead.
- **Symptom:** one test of the layer aborts in a hand-made harness: `could not connect to display`, `Could not load the Qt platform plugin "xcb"`.
  **Cause:** the package's rules run the tests with `QT_QPA_PLATFORM=offscreen`; the harness did not.
- **Symptom:** a program cannot be started on one file from a command line (KPhotoAlbum opens a database).
  **Fix:** a database beside the fixtures (`-c DIR/index.xml`, Enter for "Create database"), End and Enter in the browser for the thumbnails, Home, Right as many times as the file's place in the order of names, Enter for the viewer; remove `index.xml` and `.thumbnails` before each start so the dialog always comes.
- **Symptom:** the first key sent to Showfoto or digiKam does nothing.
  **Cause:** a dialog about model files is on top at every start in a home without them.
  **Fix:** Escape first, then a click in the picture area.
