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

## Fill and verify a gap

1. Build a glossary from the extracted packages.
   Use the 3D Depth page in Stereo KWin where its terms disagree with another catalogue.
   Keep the shipped words for the depth planes, 3D controls, Throw and frame packing.
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

## Traps

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
