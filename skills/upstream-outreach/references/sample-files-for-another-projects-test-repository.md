# Sample files for another project's test repository (ORDER 644, 2026-11-17)

The recipe for a pull request that adds real files to a small public repository of test files (a distribution reviewer's "does a fresh install open ordinary files" folder), with the licence proven for each file.
It was written while preparing files in six formats for a public samples repository: WebM, MKV, OpenDocument, WAV, camera raw and WebP, then a folder of stereo 3D files.
The stereo files are in [stereo files that open anywhere](../../stereo-pictures/references/stereo-files-that-open-anywhere.md).

## Working recipe

1. **Read the repository first.** Clone it read-only, list its files with sizes, read its read-me and licence file (it may have none), and write down which formats it lacks. A file already there is never offered twice.
2. **One branch per subject.** The formats asked for are one branch; anything else (a stereo folder) is another, so the maintainer can take one and decline the other.
3. **Find a real file, in this order of sources.** The source must state the licence for the file, not for the site's general policy.
   - Wikimedia Commons: every file page has a licence template, an author and a history. The API (`list=search`, `srsearch=filemime:video/webm CC0 ...`, then `prop=imageinfo&iiprop=extmetadata|sha1`) gives licence, author and the SHA-1 of the original. Download from `upload.wikimedia.org` and compare the SHA-1.
   - Raw samples: raw.pixls.us lists every camera sample with its licence and SHA-256 in `json/getrepository.php?set=all`; the files are CC0 unless the row says otherwise.
   - The Internet Archive: `https://archive.org/metadata/ITEM` gives the uploader, the creator, the licence URL, each original file with its SHA-1 and which files are derivatives. Take the original, never a derivative.
   - Government publications: gov.uk's content API (`/api/content/PATH`) lists attachments with their MIME types, so `application/vnd.oasis.opendocument.*` finds ODF files; the page states the Open Government Licence v3.0.
   - A bug tracker attachment is public, not free. It counts only with the tracker's own stated licence (the Document Foundation's Bugzilla footer says contributions are released under CC BY-SA 4.0 unless otherwise specified) or the author's statement, and then it needs the author's credit.
4. **Prefer a file a public report names as failing.** Search the trackers of the programs that open the format (KDE Bugzilla, GNOME, Mozilla, FFmpeg, Wikimedia Phabricator) for the format and the symptom. A report naming a camera model, a codec or a chunk layout is enough to choose the file kind; say plainly when no report names the file itself ("no report found").
5. **Prove the licence with a saved page.** Save into `evidence/`: the API JSON or page that states the licence, the author and the hash; the in-file statement when the file has one (a `Copyright` tag, an `Artist` field). Record name, size, SHA-256, direct link, licence and where it is stated, author, and what makes the file real (camera model, recorder, the program that wrote it).
6. **Look at the file before keeping it.** View a frame, a page or a preview. Open the metadata. Reject: faces of private people, names and addresses, to-do lists and account names in a screencast, company material, GPS positions, embedded logos and crests the licence excludes.
7. **Probe without a desktop.** `ffprobe` and `ffmpeg -f null -` for media, `exiftool` for pictures and WAV chunks, a raw decoder for camera raw, `soffice --headless --convert-to pdf` for office files (below), `mkvinfo` for Matroska. Write down what each said.
8. **Size.** Each file under the brief's cap, the set under its total. A film may be cut with stream copy only when the licence allows changes; say so.
9. **Branch and commit** in the clone with the person's identity and the Assisted-by trailer. Never push. Bundle each branch.
10. **Draft the pull request text** for the person to send: the result first, one sentence per line, the credits and licences listed, AI assistance said once.

### The headless office probe

Run LibreOffice on an untrusted file with a private profile, no network and no core dumps:

```
ulimit -c 0
unshare -rn soffice -env:UserInstallation=file://$PWD/profile --headless --norestore --convert-to pdf --outdir out FILE
pdfinfo out/FILE.pdf | grep -E 'Pages|Producer|Page size'
```

`unshare -rn` gives the process an empty network namespace without privileges. A document is never opened on the desktop. Read the pages as pictures too (`pdftoppm -r 40`): a crest, a logo or a name is in the render even when the metadata is empty. `unzip -l FILE` lists embedded media before any render.

## Licences that count, and kinds that do not

- CC0, Public Domain Dedication or a government's own CC0: nothing to credit.
- Public domain by age or by origin (a US federal work, a scan of an 1870s card): say which, with the page.
- CC BY and CC BY-SA: allowed with the credit written down and the file flagged to the maintainer; a repository with no credits file has no place for it.
- Open Government Licence v3.0 (UK): credit "Contains public sector information licensed under the Open Government Licence v3.0"; it does not cover logos or crests, so a file with the department's crest embedded is flagged.
- Not enough: "public", "found online", a licence field a bulk uploader typed, a site's general policy that does not mention the file, a screenshot of a copyrighted program.

## Traps: symptom, cause, fix, how it was found

- **Symptom:** a Commons file licensed CC0 titled as a landscape photograph looks too perfect.
  **Cause:** it is a generated picture (several CC0 "photographs" are). **Fix:** view every candidate and require the camera in the EXIF or Commons' own "Taken with CAMERA" category. **Found by:** opening the picture.
- **Symptom:** archive.org lists thousands of items with a CC0 or public-domain licence URL for video games' match recordings and broadcast clips.
  **Cause:** the licence field is the uploader's claim and says nothing about the material inside. **Fix:** take an item only when its creator is its uploader and the work is their own (a screen recording of their own desktop); read the item's metadata JSON, not the search result. **Found by:** the titles.
- **Symptom:** a downloaded file has the SHA-1 `da39a3ee5e6b4b0d3255bfef95601890afd80709`, and `ffprobe` says "EBML header parsing failed".
  **Cause:** that is the SHA-1 of nothing; archive.org's `/download/` answered 302 and `curl` without `-L` saved an empty body. **Fix:** `curl -L`, then compare with the SHA-1 in the item's metadata.
- **Symptom:** the Wikimedia API answers `429 Too Many Requests` after a few queries.
  **Cause:** no pacing. **Fix:** a generic descriptive `User-Agent` and 6 to 8 seconds between queries; never a browser's agent string.
- **Symptom:** a screencast fit for the repository shows a to-do list with first names and projects at 10 seconds, or a user name in a wiki page.
  **Cause:** the first frame was clean. **Fix:** view three timestamps before keeping a screen recording.
- **Symptom:** `dcraw -c -w -h FILE.CR3` exits 0, writes 33 MB and warns only "Cannot use camera white balance"; the picture is all black.
  **Cause:** dcraw 9.28 has no CR3 decoder for the compressed (CRAW) raw data. **Fix:** decode with ImageMagick's LibRaw coder (`convert CR3:FILE out.png` gives the real picture) and read the camera data with exiftool. **Found by:** looking at the output; the exit status and the byte count looked right.
- **Symptom:** a government spreadsheet or document looks clean and still carries a department's crest or logo, a statistical badge, a named contact with an address, and the author's full name in the metadata.
  **Cause:** gov.uk's Open Government Licence covers the information, not logos or crests; Word and Excel save the author into `meta.xml`. **Fix:** `unzip -l` for `media/`, render the first pages, read `meta.xml`; choose the file without them, or flag them to the maintainer. A small template with no media is the cleanest.
- **Symptom:** the gov.uk search API answers `503 hostname doesn't match against certificate` once in a while.
  **Cause:** a front-end node answering with another name. **Fix:** retry after a pause; one query takes about two minutes when it fetches 40 pages at 0.4 s each, so run it in the background.
- **Symptom:** a WAV probe says the file is fine, yet old reports (GNOME bug 561580, "GStreamer does not play a specific WAV file", fixed) show that players stumbled on metadata chunks.
  **Cause:** a Broadcast Wave file from an archive carries `axml`, `bext` and `LIST INFO` chunks, here after the `data` chunk; a parser that reads a chunk's size wrongly loses the file. **Fix:** list the chunks with a ten-line walker (`RIFF` size, then id, size and the pad byte of an odd size) and write down where each chunk sits. **Found by:** `exiftool -RIFF:all` showing fields that `ffprobe` hides.
- **Symptom:** the first KDE report found for "no thumbnail" is about the wrong file type.
  **Cause:** Dolphin shows no preview for a WebP saved with a `.jpg` name (bug 499241) and for Canon CR3 raw files from the EOS R5 on (bug 489045, libkdcraw's extension list lacked `*.cr3`). **Fix:** read the report's attachments; neither had a sample with a stated licence, so the kind is chosen from the report and the file from a licensed source.
- **Symptom:** Pillow prints "Image appears to be a malformed MPO file" when it is given only the second picture of an MPO.
  **Cause:** the second picture carries no MP index, only its attribute IFD. **Fix:** open the whole file; `Image.open(path).n_frames` is 2 and `seek(1)` gives the second picture.

## What was found for the six kinds (2026-11-17)

| Kind | Source that worked | Licence evidence | Report naming the kind |
|---|---|---|---|
| WebM | Wikimedia Commons screencasts | `{{self|cc-zero}}` and the API's extmetadata | Mozilla bugs 1245775 and 1779057 (screen recordings, H.264 in WebM); Phabricator T434172 (a Commons WebM whose captions failed in Firefox) |
| MKV | Internet Archive, an author's own vokoscreen recording | the item's `licenseurl` set by its creator, CC0 | none for the file; the Matroska conformance suite is CC BY 3.0 (credit) |
| OpenDocument | gov.uk attachments | Open Government Licence v3.0 on the publication page | LibreOffice FILEOPEN reports exist for ODF, none for these files |
| WAV | Wikimedia Commons, Swedish Performing Arts Agency | `{{Cc-zero-Musikverket}}` and the file's own `Copyright` tag | GNOME 561580 (a specific WAV not played by GStreamer, fixed): the class of problem is the chunk layout |
| Camera raw | raw.pixls.us | CC0 in the repository's JSON, `Copyright: CC0` in the file | KDE 489045 (CR3 thumbnails in Dolphin) |
| WebP | Wikimedia Commons | `{{self|cc-zero}}` | KDE 499241 (WebP with a `.jpg` name) |
