# Audit and translate what the package ships

**For** maintainers filling a language gap in the edition. Use the installed locale data to find the words people already see and to check the effect of a rebuild.

## Count the published baseline

1. Record the archive revision, signed release and index checksums, recipe commit, package version and architecture.
   Select the indexed binary for each package and extract it with `dpkg-deb -x PACKAGE.deb DESTINATION`.
   A source can produce several binary packages and only one may own a catalogue.
2. Match the English text to each of `en pl pt_BR fr de es ja ko zh_CN zh_TW`.
   Record one row per binary, resource, key and language, with the English value and status.
   Empty or missing locale values, incomplete plurals and English prose in another locale are gaps.
   Record unchanged program and format names separately.
3. Use the matching procedure below for each format.
   Credit only the edition's own text, including the addition in an applied fork patch.
   Record surfaces without a known denominator as unmeasured.
4. Compare the published gap against the same English key and locale in the current recipe, including any referenced source snapshot.
   Keep changes with matched source and already localized values out of the translation queue.
   Recheck English values that changed since publication.
   Record which version would deliver each closure.
   Run the baseline counter against the rebuilt payload and account for every remaining row.

| Format | Match by |
|---|---|
| PO and MO | Domain, context and msgid, counting one unit per msgid. Take the denominator from the template and the applied edition changes. Use `msgunfmt` or a gettext reader on the actual MO. Require every plural form. A union of compiled keys can omit strings absent in every language. |
| Qt TS, QM and QML | Context, disambiguation and source. Convert the delivered QM with `/usr/lib/qt6/bin/lconvert -if qm -of ts -i FILE.qm -o FILE.ts`. Match QML lookups and the labels and bodies of each installer slide. Inspect compiled RCC resources when the translations are embedded. |
| Desktop, notifyrc and KDE JSON | Installed file, group and localized field such as `Name[es]`. Read embedded KPlugin metadata with `qtplugininfo --full-json PLUGIN.so`. |
| Shell and JSON | Match tables by their own locale lookup, by stable key or by documented position. Read shell assignments as data. Exclude URLs, asset paths and fields that the interface never displays. |
| XML and journal | Match PolicyKit actions by action ID and field, AppStream blocks by element and position, and shared MIME comments by type and `xml:lang`. Match journal message IDs with Subjects and bodies in their locale catalogues. |
| Tasksel and APT | Check tasksel's exact description and label keys against the installed gettext domain. Compare APT description blocks with the archive translation indexes, when available. Count these as different resources. |
| Fluent and LNG | Compare actual Fluent keys and label attributes, including each maintained browser locale variant, inside the shipped archive. Match sView's numeric IDs against the pinned upstream base and skip commented-out entries. |
| Markdown | Pin the revision and compare visible blocks and alternative text with the translated page. Record absent pages by their English blocks. Keep structural coverage separate from the reading of the translation. |

## Reconcile program catalogues before writing strings

Keep the published gap identities fixed while comparing recipe main and staged release reports. A report that gives a total or mentions a program does not establish that a particular locale and key are present. Confirm existing translations by compiling the applicable catalogue against the receiving source. Record these keys as ready to carry forward and keep their publication status open until a package contains them.

| Program | Files and checks |
|---|---|
| Haruna and Dragon Player | Read the applied source and extract QML with `xgettext --language=JavaScript` and the program's Ki18n keyword signatures. Compile the PO with `msgfmt --check-format` and compare context and complete English key in the installed domain. |
| sView | Compare `StImageViewer.lng` and `StMoviePlayer.lng` independently. Spanish source files live under `lang/spanish` and install under `lang/Español`. Preserve the source file's line endings and compare the numeric keys, `{0}` and literal `\n` escapes. Check the program's language loader against the installed resources. |
| Bino | Compile the TS catalogue with Qt 6 `lrelease` and check the QM with `lconvert`. Use the `Gui` and `Mode` contexts where the input labels use them. Keep `zh_CN` and `zh_TW` separate. |
| VLC Stereo | The flat source path is `po/LOCALE.po`. Check the gettext domain under `/usr/share/vlc-stereo/locale` and the localized desktop actions independently. The VLC policy says “AI help with writing or translation is fine.” Keep edition strings in the package recipe. [VideoLAN AI policy](https://code.videolan.org/videolan/vlc/-/blob/master/doc/VideoLAN_AI_Policy.md) |
| Lutris | Meson builds the `lutris` gettext domain from `po/LOCALE.po` and `po/LINGUAS`. Preserve Python named `%()` placeholders and check the built lookup in a real locale. Lutris says contributors are “free to use any tool available to help you create your contributions” and expects validated work. Keep edition strings in the package recipe. [Contribution rules](https://github.com/lutris/lutris/blob/master/CONTRIBUTING.md) · [Translation workflow](https://github.com/lutris/lutris/blob/master/po/README.md) |
| Marble | Match core Ki18n messages in `po/LOCALE/marble.po`, QML map tooltips in `marble-maps.po`, and the Qt main-window actions in `poqm/LOCALE/marble_qt.po`. The Qt PO context uses the `Marble::MainWindow\|` encoding. Convert the latter to TS and compile to QM before checking the Qt context and ID. |
| Wine SBS View | Match the flat PO path and enable the language in the Makefile that creates the actual installed MO. Read that MO from the built package. Preserve newlines in the command's usage and diagnostic keys. |
| UMS settings | Localized `X-KDE-Keywords[LOCALE]` comes from the embedded KPlugin metadata. Extract the package and use the versioned `/usr/lib/qt6/bin/qtplugininfo --full-json` on the plugin. |
| Partners settings | Extract QML and C++ Ki18n calls and Python contextual gettext calls into the shared POT. Compare the complete context and message ID against each compiled catalogue, including argument counts and each language's plural rule. Check the KPlugin name, description and search keywords, the top-level System Settings category file, and PolicyKit prompts separately. They each have their own localized fields. |

Read the project's own current contribution and translation rules. KDE routes translations through its language teams. Its Spanish team prohibits using the output of online translation services or ChatGPT, and Krita's README bars AI use pending a decision. KDE forks carry the edition's strings in package recipes. XScreenSaver excludes contributions built with or assisted by an LLM. These programme rules apply to upstream contributions. Carry the edition’s own additions in its package recipes and keep this work local to the edition. If the checked upstream records give no AI rule, record the consulted records and keep edition changes in the recipe. [KDE Localization](https://l10n.kde.org/) · [KDE Spanish team](https://es.l10n.kde.org/responsabilidad.php) · [Krita README](https://github.com/KDE/krita#ai-moratorium) · [XScreenSaver FAQ](https://www.jwz.org/xscreensaver/faq.html#writing-savers)

## Fill and verify a gap

1. Build a glossary from the extracted packages.
   Use the 3D Depth page in Stereo KWin where its terms disagree with another catalogue.
   Keep the shipped words for the depth planes, 3D controls and frame packing.
   Write Throw and Catch as feature names, with the meaning in parentheses after the first mention in each localized string. The Brazilian Portuguese forms are “Throw (jogar)” and “Catch (receber)”. Keep the arrival notification “Receba!”.
   Record the domain, key, context, language and package version for each wording.
2. Insert translations in the programme's own format.
   For KDE forks carry the edition keys through the distribution package recipe.
   Preserve existing upstream catalogues and extend their applied package patches only where the edition added the text.
3. Run the format checker and compare the source and target placeholders for each changed key and each plural form.
   Check occurrences, order where arguments are positional only by occurrence, code and markup, accelerators and embedded line breaks.
   Use `msgfmt --check` for PO, Qt's `lconvert` for QM or TS, `desktop-file-validate` for desktop files, `bash -n` for shell, and the package's JSON or XML parser for data fields.
   Delete a placeholder or add a fake one in a disposable fixture to make sure the comparison fails.
4. Read each language against the source and glossary again.
   Record what changed and the scope of the review.
5. Rebuild with the package's recipe and version convention and run the Lean Code checks.
   Install the published build and then the staged upgrade in a clean container.
   Generate a real UTF-8 locale with `localedef -i es_ES -f UTF-8 es_ES.UTF-8`, then run each probe with its own `LANG` and clear `LC_ALL` and `LANGUAGE`.
   Compare a known localized string with the tool's output, lookup or loaded page in each language.
   For example, a MIME label goes through GIO's `content_type_get_description` after installing the package and letting dpkg run the shared MIME database trigger.
   Keep the expected and observed values for both builds.

## Check live-caption adapter catalogues

- Count the adapter's JSON keys separately from the entries extracted by Kaption and captiond's upstream `Messages.sh`. Kaption and Qaption share one upstream domain. The edition's settings adapter owns a separate key set.
- Keep the adapter's numbered JSON placeholders and the corresponding positional `%s` values in its Problems language files. Render both against distinct arguments, especially the device-mismatch and model-offer messages. Test all required locales through the adapter, including the two Chinese scripts.
- **Symptom:** the adapter's source tests pass while a built package serves captions settings only in English and Brazilian Portuguese.
  **Cause:** the gettext shipping check only read MO payloads. The adapter installs its JSON directly.
  **Fix:** register the source and payload directory in the shipping test's `JSON_CATALOGUES` map. Run `translations-shipped.py --only sparky-stereo-live-captions STAGE` and compare every key with the recipe. Check the journal catalogues separately with the Problems compiler.
  **How found:** the existing package contained 60 of the 300 expected JSON values. The same checker passed 60 of 60 when given the previous source's catalogues.

## Prove the installed sView resources

1. Build the pinned recipe with its usual Lean Code checks. Install the
   published package in the container first, then install the candidate with
   its declared dependencies.
2. Compile a small lookup probe against the pinned `StTranslations.h` and the
   installed `libStShared`. Install the probe in `/usr/bin` in the test
   container. The loader discovers resources relative to the executable.
3. Run the probe in a separate process for each real UTF-8 locale. Open the
   two module names independently and request the same numeric keys from each.
   Record Expected and Got for the locale controls and each newly added key.
   Include the absent-numbered-key control in the published Spanish package.
4. Check embedded line breaks through the loader. `StLangMap` decodes the
   written `\n` and puts a space before the line break. Keep the numbered
   source files' CRLF line endings when creating the package patch.

## Traps

- **Symptom:** the audit reports an English key ending in the middle of a sentence, and also has an entry for the whole sentence.
  **Cause:** a patch scanner stopped at the first operand of a JavaScript string concatenation in QML.
  **Fix:** extract the complete key from the applied source with `xgettext --language=JavaScript` and verify that the installed MO has no fragment lookup.
  **How found:** the compiled catalogues and extracted keys confirmed 117 Haruna and 36 Dragon Player fragment rows whose complete keys already had their own rows.
- **Symptom:** a translation audit skips Spanish hunks in a patch that visibly contains them.
  **Cause:** a hunk reader that trusts line counts across the entire file can keep reading the next target as part of a malformed or unfamiliar hunk.
  **Fix:** scan each file diff independently, then apply the relevant hunk with fuzz disabled and check the compiled result. Run the structural validator on the actual delivery patch.
  **How found:** separating the file sections exposed the existing Spanish Kalzium and Kubrick entries. Applying the Spanish hunks and compiling their PO files returned all seven values.
- **Symptom:** invoking `lconvert` says the Qt 5 executable is absent although Qt 6 is installed.
  **Cause:** the unversioned program is resolved by a Qt selector that chose Qt 5.
  **Fix:** run `/usr/lib/qt6/bin/lconvert` for this catalogue.
  **How found:** the bare command failed on the installed Stereo Layer's QM, and the Qt 6 command recovered the expected source strings.
- **Symptom:** the largest language gap in a helper package consists of web text.
  **Cause:** the package ships a snapshot of documentation and a site as well as the helper.
  **Fix:** match each resource to its owning surface before assigning translation work.
  **How found:** the skills snapshot's site keys resolve to the edition detail page and the Windows guide.
- **Symptom:** a native recipe in a container says the recipe has no commit date.
  **Cause:** the recipe cannot see the checkout metadata through its build mount.
  **Fix:** set `SOURCE_DATE_EPOCH` to the last commit touching the recipe.
  **How found:** the MIME recipe found its version and sources but failed its date lookup until the host supplied the recipe commit timestamp.
- **Symptom:** all parsed translations pass, but the terminal menu still has English paragraphs.
  **Cause:** the source scanner recognized only single-line i18n arguments.
  **Fix:** take active multiline IDs from the format's extractor, retain their line breaks, and exercise the terminal menu through a PTY.
  **How found:** the Sparky CA recount found two terminal menu variants and one fingerprint tooltip absent from the checked key list.
- **Symptom:** the tasksel recount loses all its measured keys after adding an English overlay.
  **Cause:** treating the English catalogue's absence of a key as its identity changed the denominator on the candidate.
  **Fix:** keep the published key list fixed. Read the actual merged tasksel domain and call `tasksel --task-desc` to exercise the description body.
  **How found:** the package installs the same domain for current systems and for the installer.
- **Symptom:** the compiled PolicyKit XML has an empty localized message although the KAuth action contains text.
  **Cause:** an unquoted comma in an `.actions` value makes Qt's settings parser return a list to the generator.
  **Fix:** quote the value and read the generated XML by action ID and locale.
  **How found:** the Graphics page's Polish and German messages appeared in the rebuilt action after quoting.
- **Symptom:** `msgfmt --xml` cannot find its AppStream rules, or the recount misses the Chinese values in valid generated XML.
  **Cause:** the build is missing AppStream ITS data, or the auditor recognizes only short locale names.
  **Fix:** install the declared AppStream build dependency. Accept `zh-Hans-CN` and `zh-Hant-TW` as the Chinese locale tags emitted for `zh_CN` and `zh_TW`.
  **How found:** the AppStream build dependency made the generator run, and the generated XML showed both explicit script and region tags.
- **Symptom:** a desktop file in `/etc/xdg/autostart` is absent after a successful dpkg unpack.
  **Cause:** dpkg installs the conffile at configuration time.
  **Fix:** configure the package with its exact siblings and read the final autostart path.
  **How found:** the GL stereo show desktop entry existed in the archive and was absent during the unpack-only check.
- **Symptom:** a metadata-only GL stereo change fails the saver receipt check.
  **Cause:** the plain build's stripped layer differs from the Lean Code layer named in the receipts.
  **Fix:** reproduce the published Lean Code recipe and qualify the actual stripped layer, keeping the receipt gate active.
  **How found:** the plain build rejected the layer hash. The equivalent Lean Code build passed all 132 receipts.
- **Symptom:** a context-aware Ki18n probe still returns English although the compiled MO contains the exact translation.
  **Cause:** the probe set the requested Ki18n language but started in the C locale.
  **Fix:** install the UTF-8 test locales and set a real `LANG` for each probe process, clearing `LC_ALL` and `LANGUAGE`.
  **How found:** both singular and plural KScreenLocker lookups matched after switching the process locale.
- **Symptom:** a build dependency installation with the edition pin wants to downgrade an entire Qt stack.
  **Cause:** the image already has Debian's newer Qt installed.
  **Fix:** start with a clean image that has the packaging tools and no preinstalled Qt, then resolve the pinned build dependencies together.
  **How found:** the pinned KScreenLocker dependencies installed together in the fresh base and the package built.
- **Symptom:** the PO patch validator reports a Spanish ID missing even though the patch applies and msgfmt succeeds.
  **Cause:** its old parser only recognized singular `msgstr` and read later entries while seeking one after a plural.
  **Fix:** parse the context, singular ID, plural ID, and each indexed translation. Compare every form on the applied side. Keep the structural gate and the native `msgfmt --check --check-format` check. Test that changing only the second plural form fails.
  **How found:** the exact Spanish hunk in KScreenLocker failed the old parser and passed the corrected one. The installed probe independently matched both plural forms.
- **Symptom:** a source scan says a locale is complete but the compiled catalogue falls back to English.
  **Cause:** the source has a fuzzy translation carried from an unrelated msgid. Gettext omits it from the compiled catalogue.
  **Fix:** verify the translated meaning before clearing the fuzzy flag, then compare the compiled lookup against the corrected value.
  **How found:** the Japanese KWin translation for “Unsupported compositing type” held the old “Suspend Compositing” wording and was absent from the compiled catalogue.
- **Symptom:** a well-formed catalogue patch fails on the receiving release even though the published release takes it.
  **Cause:** the staged successor changed the patch context after the measured publication.
  **Fix:** checksum every member of the receiving .dsc, reconcile its current keys, then generate a patch against that tree. Replay the quilt series through dpkg-source and directly apply changes to files under debian/ before building the new .dsc.
  **How found:** KRdp's published and staged catalogues differed in context. The rebased patch applied to the staged source and the compiler returned each expected translation.
- **Symptom:** `desktop-file-validate` flags `MimeType` and `Actions` on a KDE service menu.
  **Cause:** the freedesktop application validator treats the existing `Type=Service` entry as outside its application schema.
  **Fix:** preserve the KDE service-menu type, record those diagnostics on both builds, and prove the service action's exact localized key through the desktop key reader.
  **How found:** the published and rebuilt audio-format menu both drew the same diagnostics. The candidate's localized action values passed the installed lookup.
- **Symptom:** a catalogue-only candidate's dependency solve selects Debian's PowerDevil or cannot select the exact Qt version required by Graphics.
  **Cause:** the link-check snapshot lacks the edition's shipped APT policy and the unchanged provider or runtime siblings.
  **Fix:** give the link gate the signed published policy package and the exact unchanged siblings in both snapshots. Keep strict pinning and the package's own dependency declarations.
  **How found:** the same Power Profiles controls failed the generic archive solve. Both versions resolved once the edition policy, the versioned PowerDevil provider and its Qt runtime were supplied.

- **Symptom:** the corrected validator reports “no file section” on an old Dragon or VLC patch that GNU patch can read.
  **Cause:** plain unified sections begin with `--- a/…` and lack the Git file boundary the validator uses.
  **Fix:** add the matching `diff --git a/… b/…` header before each section. Apply both forms to the same preimage with fuzz disabled and compare bytes before carrying the normalized patch.
  **How found:** the affected sections were replayed on the published or recorded quilt preimage. All 26 applied catalogue pairs matched byte for byte.
- **Symptom:** gettext reports a duplicate key after a formerly obsolete entry is translated.
  **Cause:** the obsolete copy and a newly added active copy use the same context and msgid.
  **Fix:** replace the matching obsolete entry with one active entry. Compile the resulting catalogue and compare the exact lookup.
  **How found:** six digiKam locales already had an obsolete “View” entry.
- **Symptom:** the rewritten PO silently loses part of a translation containing a Unicode separator.
  **Cause:** splitting PO text with Python's `str.splitlines()` treats U+2028 and U+2029 as line breaks even inside a quoted PO value.
  **Fix:** split physical lines on LF and let the native compiler check the reconstructed PO.
  **How found:** Partition Manager's published Traditional Chinese PO has U+2029 inside ten quoted strings. Both sources compile with gettext. The PO patch validator's catalogue reader fails before looking up any key because it also uses `splitlines()`.
- **Symptom:** Wine SBS View's Spanish PO compiles but the package ships no Spanish MO.
  **Cause:** the recipe points at `po/LOCALE.po` and builds only the locales in the Makefile.
  **Fix:** use the flat path and carry the shipped recipe's language-list change. Inspect the candidate MO.
  **How found:** compiling an extra `po/es/wine-sbs-view.po` by hand did not affect the build output. The rebuilt candidate returned all four Spanish values.
- **Symptom:** a compiled Marble gettext value exists but the globes' Qt menu still uses English.
  **Cause:** a Qt MainWindow string lives in the Qt catalogue and is looked up with its Qt context.
  **Fix:** use the `poqm` domain for Qt, then compare the compiled QM.
  **How found:** inspecting the source calls and compiled catalogues separated 18 Qt menu labels from the Ki18n and QML values.
- **Symptom:** an sView lookup probe returns empty values in every language.
  **Cause:** the executable lives in a scratch directory, so the loader searches under the wrong resource root.
  **Fix:** install the probe in the same executable directory as sView inside the test container.
  **How found:** both published and candidate controls became readable after moving the probe to `/usr/bin`.
- **Symptom:** a catalogue-only Stereo Create build stops in the picture probe test.
  **Cause:** the test expects a blank, unmarked 400×200 picture to be flat. The installed Stereo Layer treats its 2:1 shape as side by side.
  **Fix:** keep the gate enabled and run the same test on the unmodified published source against the same library. If it reproduces, retain the translation recipe and record the package gate failure.
  **How found:** both the published source and the candidate failed only the same assertion in `EngineTest::probePictures`.

- A numeric Qt argument may touch a word. A validator using a word boundary after the digit missed `%2` in the Korean OBS value `%2입니다`. Read the complete digit run after `%` and compare the resulting argument sequence. For width and height messages, check the order of both dimensions against the call site.
- OBS's module locale and the layer catalogue can ship different parts of one dialog. The module loads `stereo-layer_qt` for shared controls like “Enable 3D” and “Display Settings…”. A published layer older than the module's minimum version can lack a shared key. Compile the catalogue from the minimum supported layer source and check the exact context and terms. Use OBS's own frontend locale for its menu and settings labels.
