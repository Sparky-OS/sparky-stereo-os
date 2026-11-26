# Making a stage whole after the fact

**For whoever finds a stage of packages without their sources, buildinfo, changes or build records** and must make it a set of source closures a round can take.
Written on 2026-11-26 from queue row 742b: Stereo HandBrake's stage held 101 checksum-correct packages of six sources and none of the rest.
The rule it answers (Daniel's design, recorded after row 794 found the gap): a stage is accepted as a source closure, not as a folder of packages; for each source, the `.dsc`, every file it names, the buildinfo, the changes and the build record are in the stage and agree with `SHA256SUMS`.

## Recipe

1. **Inventory before touching anything.** Hash every staged `.deb` and every `.dsc`, `.buildinfo`, `.changes`, `*.tar.*` and `*.sparky-build.json` the earlier lane left anywhere (its evidence folders, its scratch, its old stages; read only). Match each build record's `debs` list (name and sha256) against the staged files, and each record's `files` list against the pieces found (`reconcile-pieces.py` in the lane's scripts). The result says, per source and architecture: which record produced the staged binaries, which of its files still exist, and which staged binaries no record names.
2. **A record names its source's sum: regenerate the source until it matches.** Check out the record's `recipeCommit` in a worktree (an old commit may be reachable only through an `archive/` tag after a history rewrite), give the build its date (`SOURCE_DATE_EPOCH` = the record's `sourceDateEpoch`, the last commit touching the recipe folder at that commit), fetch the upstream source through its signed index, run the recipe's prepare step, then pack it as the recipe's build did (`dpkg-buildpackage -S -sa -d`). Compare the `.dsc` sum with the record's. Equal bytes recover that piece exactly.
3. **What a record never names cannot be recovered, only rebuilt.** A `.buildinfo` and a `.changes` describe one build; when they are gone, rebuild from the recovered source with the same recipe commit and date, compare every package with the staged one member by member (`deb-members.py`: ar members, control fields and files, every data entry's type, mode, owner, size and content hash, and for ELF files the sections that differ), explain each difference, and stage the rebuild's complete set.
4. **No record at all** (the source was never recorded): rebuild from the recipe commit the lane's report names, compare member by member, and write the record with the rebuild.
4b. **A standalone package** (packed by `lean.standalone`, no `dpkg-buildpackage`) has no `.buildinfo` or `.changes` by its recipe; the round's provenance lists both as gaps. Rerun its `build.sh` at the recipe commit with the facts of `build-provenance.sh` (`sparky_provenance_init IMAGE RECIPE`, its `SPARKY_PROV_ARGS` on `docker run`), unpack the `.dsc` it wrote, write `debian/files` (one line per `.deb`: name, section, priority), then `dpkg-genbuildinfo --build=full -u OUT` and `dpkg-genchanges --build=full -u OUT` in that tree, and `lean.buildrecord.record(DEBS)` (lane script `fdk-closure.sh`). The packages come out byte-identical (sparky-stereo-ffmpeg-fdk 20261120.1: 2 of 2).
5. **Stage one folder per source**: `.dsc`, every file it names (checked against its `Checksums-Sha256`), the buildinfo and changes of each architecture (every file each names), the build record (every sum it holds), the binaries, `SHA256SUMS` per folder and over the whole stage, and `.keep` first.

## What the HandBrake stage gave (row 742b, 26 November 2026)

| Source | Source regenerated equal to the record | Packages byte-identical | Packages that differ |
|---|---|---|---|
| x264-dmo +stereo3d1 | yes (.dsc 2a294a29...) | 10 of 10 (amd64, i386) | none |
| x265-dmo +stereo3d2 | yes (.dsc fc7a5772...) | 11 of 11 | none |
| sparky-stereo-ffmpeg-fdk 20261120.1 | no record existed | 2 of 2 | none |
| stereo-layer 1.23.2 | no record existed | 16 of 20 | libstereo-gtk1, libstereo-layer1 and their dbgsym: build ID only |
| handbrake-dmo +stereo3d2 | no record existed | 3 of 5 | handbrake-gtk and its dbgsym: build ID only |

All builder images of the first builds were gone; the rebuilds ran in new images from the same Debian testing base, six days later, with the same compiler (GCC 16.2.0-4).

**A package that differs only in its build ID.** `deb-members.py` lists the ELF sections whose bytes differ; when they are only `.note.gnu.build-id` and `.gnu_debuglink`, the code and data are identical and the build ID moved because the debug information moved (the build ID hashes it). Prove what moved: `objcopy --decompress-debug-sections` on both `.debug` files from the dbgsym packages, `readelf --debug-dump=info` of each with addresses and offsets stripped, then count the differing attribute kinds. Seen here: the same number of entries with the same names, and only `DW_AT_location`/`DW_AT_GNU_locviews` offsets into `.debug_loclists` (the Qt and GTK layer libraries), or `DW_AT_decl_line` values of declarations from installed headers and the `DW_AT_stmt_list` offsets after them (ghb). Stage the rebuild's complete set, and say which packages replace staged ones with a different build ID.

## Traps

| Symptom | Cause | Fix, and how it was found |
|---|---|---|
| `reproducible: ... is in no git repository` inside a container | a worktree's `.git` is a file pointing to a host path the container does not have | compute the epoch on the host (`reproducible.py epoch RECIPE_DIR` in the worktree) and pass `SOURCE_DATE_EPOCH`, which `epoch()` honours |
| The source build stops at `dh: error: unable to load addon bash-completion` | `debian/rules clean` needs the package's build dependencies | pack without the clean step (`-nc`) on a freshly prepared tree; the sum must still equal the record's (it did for x264) |
| The rebuild's packages are byte-identical to the staged ones, but its `.dsc` differs from the record's | the tree was unpacked on the host under umask 002; a recipe that builds with `-sa` packs the source again with the tree's file modes (rw-rw-r-- against rw-r--r--); `dh_fixperms` hides it in the packages | unpack under `umask 022` before the build; found by listing both Debian tarballs with `tar -tvf --numeric-owner` and `diff -r` of their contents (equal) |
| A container's `apt-get download` fails: "Could not load certificates from /run/host-ca.crt" | the builder's apt configuration (from `https-only-apt.sh`) reads the host CA bundle at run time | mount `/etc/ssl/certs/ca-certificates.crt` at `/run/host-ca.crt` in every container that fetches |
| `rm -rf` of a scratch clone is refused by the branch-keeper hook | its branches exist nowhere else | bundle the branches into the lane folder first, or keep the clone and say so in Kept |
