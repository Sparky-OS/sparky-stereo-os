# A program joins the shared per-file choice

**For whoever moves one more viewer, album or player onto the shared per-file 3D choice.**
Written on 2026-11-14 from the work that moved Koko (QML), KPhotoAlbum and digiKam with Showfoto (QWidget) onto it, after Dolphin and Gwenview; stereo-layer 1.19.0.
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
6. **Keep what the program owns**: which eye is shown is a view, not a correction, and stays the program's; so does a lasting "show everything flat" (it is the program's "enable 3D").
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
4. **Shortcuts** act through the object: `fileChoice.swapEyes = !fileChoice.swapEyes` (when `fileChoice.swapEnabled`), `fileChoice.choose("not-3d")`. Entry names do not change with the language: `automatic`, `not-3d`, `side-by-side-left`, `side-by-side-right`, `top-and-bottom-left`, `top-and-bottom-right`, `anaglyph-red-cyan` and so on; `fileChoice.chosen` is the name of the file's entry.
5. **A Kirigami action list cannot hold a Controls menu.** Give the hidden-actions list one action that opens the program's 3D menu as a popup, and put the layer's menu inside that popup.
6. **Keep the stereo QML in files of their own**, loaded with `Loader.setSource(Qt.resolvedUrl(...))`, when the program must also build without the layer: a file that imports `org.sparky.stereo` does not load there.
7. **Renames need no code**: a program with a `FileChoice` keeps every file's choice with it when the desktop's file jobs move it, and `changed()` says so for the file the object names.
8. **Packaging**: the program needs the module at run time through `libstereo-layer1`, which depends on `qml6-module-qtquick-controls` and `qml6-module-qtqml-models`; a program with `dh_qmldeps` names the module in `debian/qmldeps.overrides` (`org.sparky.stereo libstereo-layer1`).

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
