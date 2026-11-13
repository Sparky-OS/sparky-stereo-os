# Adding a front-page language after the fact

**For** anyone who has to give the front pages one more language when the others already exist: what to translate from, where the new language goes in the row, which words to settle first, and the traps met when Spanish joined.

Written on 2026-11-13 from ORDER 509, the Spanish front pages: the README, the language row of every README, the call for testers and the one-page Windows guide.
The rules of [the skill](../SKILL.md#the-rules) come first, and [adding a required language to the whole edition](../../edition-packaging/references/adding-a-required-language.md) covers the packages' strings.

## The recipe

1. **Reconcile before writing.**
   If an older draft exists, find the commit it was written on and ask git whether the English page changed since: `git diff --quiet BASE HEAD -- README.md && echo unchanged`.
   Unchanged means the draft's structure is current and only its words need the review; changed means the diff is the list of lines to redo.
2. **Translate from today's English page,** never from another translation.
   Keep its lines one to one: the same sentences on the same lines, the same pictures, the same links.
   A script that builds the new page from the English lines and a table of translated lines stops on any line it has no translation for.
3. **The glossary first.**
   Before the first sentence, write one table of the fixed vocabulary with the source of each term, and use it in every file.
   The order of sources: the desktop's own catalogue for the desktop's names, the edition's own catalogue for the edition's names, the vendor's page in that language for the vendor's names, and only then a choice of your own, marked as yours.
   `python3 scripts/catalogue-terms.py es 'Display Configuration' 'Scale:' '&Keep'` prints how each installed catalogue translates an exact English string.
   A string that prints nothing has no translation: the program shows it in English, and the page names it as the screen shows it.
4. **The form of address is a choice that shows.**
   Take it from the edition's catalogue in that language, say which you took, and list it for Daniel.
5. **The language row.**
   The row is English first, then the Latin-script languages in the order they joined, then Japanese, Korean and the two Chinese scripts.
   A new Latin-script language goes after the last one of its group, in every README at once, and the row stays byte for byte the same in all of them.
   The flag is Daniel's choice, never the writer's.
6. **The sign-up flags** gain the new flag in the same place.
   While the call in that language does not exist, its link is a named placeholder (`ISSUE-ES`), which the link check counts and never resolves, so it cannot be published by accident: a search for the placeholder must find nothing before the push.
7. **Anchors.**
   Every anchor the English headings make must resolve in the translation: an explicit `<a id="english-slug"></a>` before each translated heading.
   Check it by script, not by eye (step 10).
8. **The call for testers** is translated from the English call as it stands that day, read from the tracker, with the form left in English as in every call.
   If the call's status line is older than the README's, translate it as it stands and list the sentence for the person who owns the calls.
   Hand back, as a list and not applied, the closing line of each existing call with the new language added.
9. **The guide.**
   Translate the page the README's next step links to, with the same pictures.
   Say which pictures show screens in another language.
   Where the session a guide describes starts in English, name each control as the screen shows it and give its meaning in brackets, with the desktop catalogue's own word.
   Where the vendor has the cited page in the new language, link that one and quote its own sentence in that language; keep the English original, said as such, where it has none.
10. **Check by script.**
    `python3 scripts/check-front-page-links.py . FILES --pair README.md README.es.md --placeholder ISSUE-ES --allow URL --control`
    The expected last line is `RESULT: PASS, 0 broken`, after a control line that says PASS.
    Run it once without `--placeholder`: it must fail and name the placeholder.
    Then the skills check and the publication check on every changed file.
11. **The cold reading in that language.**
    Give a reader from another lab the first screen only, in the new language, with the four questions of [the newcomer test](../SKILL.md#the-newcomer-test) and one more: which words read as unnatural in that language.
    Ask for the answers in English with the original words quoted, so the reviewer can read them.
    Replace a placeholder link with a neutral address in the reader's copy and say so.
    When no reader can be reached, record each refusal word for word and stop: a reading of your own is not a reader test.
12. **One page for Daniel** before anything is published: the first screen in full, the row, the call's title and opening, the ten most visible terms with the English beside them, and every choice that shows.

## Traps

- **Symptom:** the pair check reports `anchors of README.md that do not resolve` in a translation, for a heading nobody thought of (`more-about-the-edition`).
  **Cause:** explicit ids were added only for the headings someone remembered were linked; a translated heading makes another slug.
  **Fix:** an explicit id for every heading of the source, and the pair check on every translation.
  **How it was found:** the check compares the set of anchors the source's headings make with the set the translation resolves; on 2026-11-13 the eight older translations all lacked that one.
- **Symptom:** the first word of the page can be read as another verb.
  **Cause:** in Spanish the formal imperative of "crear", "cree", is also a form of "creer" (to believe).
  **Fix:** the infinitive for the sentence that lists what a person can do ("Crear y explorar en 3D ..."), the formal imperative where a step is given ("pruébelo", "guarde").
  **How it was found:** reading sentence one alone, as a stranger meets it.
- **Symptom:** a word of the English page has a first meaning in the new language that is not the one meant.
  **Cause:** "globos" alone is balloons before it is globes.
  **Fix:** the full noun, "globos terráqueos".
- **Symptom:** an earlier string of ours in that language uses a word that names something else ("auriculares" for a headset: it means headphones).
  **Cause:** a literal translation that nobody read on a page.
  **Fix:** do not copy it for the sake of one name everywhere; choose the right word, write it in the glossary as yours, and report the earlier string so it is corrected where it lives.
- **Symptom:** the desktop's page has two names in that language, one from the desktop's catalogue and one from ours, an article apart ("Configuración de la pantalla", "Configuración de pantalla").
  **Cause:** our strings were translated without looking the name up.
  **Fix:** the desktop's catalogue wins for the desktop's names; report the other.
  **How it was found:** `catalogue-terms.py` beside a search of our own catalogue for the same words.
- **Symptom:** a query to the reference corpus for the desktop's terms in that language returns developer documentation.
  **Cause:** the corpus holds the documentation, not the translation catalogues.
  **Fix:** read the installed catalogues with `catalogue-terms.py`, and record the corpus result as it was.
- **Symptom:** a word is right in one country and unknown in the next ("lápiz USB", "pendrive", "apuntarse").
  **Cause:** one catalogue serves every country that speaks the language.
  **Fix:** the word every country understands ("memoria USB", "inscribirse"); where the desktop's catalogue already chose a spelling ("vídeo"), follow it.
- **Symptom:** the vendor's page for one country redirects to another's.
  **Cause:** the vendor keeps one page per language (`curl -s -o /dev/null -L -w '%{http_code} %{url_effective}\n' URL` showed the Mexican address ending on the Spanish one).
  **Fix:** link the address that answers, and take the page's title and the quoted sentence from the page itself.
- **Symptom:** the publication check, or a reader, finds an address in a credit.
  **Cause:** a catalogue's `Language-Team` header holds the team's name and its list address.
  **Fix:** credit the team by the header's name only.
- **Symptom:** every reader call is refused (`429 Too Many Requests` from the cloud route, "bootstrap pending" from the other).
  **Fix:** one call per route, each refusal recorded word for word, the item reported as not done; the pages still go to Daniel with that said.
- **Symptom:** the translated guide would promise screens in the reader's language.
  **Cause:** the stick's menu offers the session in English and in German only.
  **Fix:** one sentence in the step that starts the session, then each control by its English name with the meaning in brackets.
  **How it was found:** the long guide's table of the menu's entries, and the pictures themselves.

## Perks

The pair check is the reviewer's proof that nothing was lost: external links, explicit ids, heading levels and pictures are counted on both sides.
The glossary is the reviewer's reading list for the words, and the next lane's starting point for the detail page in that language.
