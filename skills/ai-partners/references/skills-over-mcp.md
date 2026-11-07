# Serving skills over MCP: what exists and what to check

**For distro developers and their partners, human or model:** the facts to have in hand before writing, registering or testing an MCP server that serves skill folders.
Everything here was read from the project's own documents on 2026-11-06 and is dated; read the source again before relying on a detail that may have moved.

## Two protocol eras, and a server must speak both

- The MCP revision `2026-07-28` is stateless: no `initialize` handshake, every request carries `_meta` with `io.modelcontextprotocol/protocolVersion` and `io.modelcontextprotocol/clientCapabilities`, results carry `resultType: "complete"`, and `server/discover` is mandatory (https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning).
- Revisions up to `2025-11-25` open with `initialize`.
  The compatibility matrix says a legacy client against a modern-only server fails, with an error the client may not show.
  Clients in use today may still be legacy, so a server that wants every assistant answers both: a request with the modern `_meta` is served statelessly, an `initialize` selects legacy behaviour for that process.
- stdio framing (both eras): one JSON-RPC message per line, no embedded newlines, nothing but MCP messages on stdout, logging only on stderr, exit when stdin closes (https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio).
- Trap, found by reading the SDK's constants: Debian's `python3-mcp` 1.28.1 has `LATEST_PROTOCOL_VERSION = "2025-11-25"` and no `server/discover`, so a server built on it is legacy-only.
  The upstream Python SDK v2 serves both eras but needs packages Debian does not have (`mcp-types`, `httpx2`, `truststore` per its own "What's new in v2" page).
  The packages exist in Debian unstable, not in testing, as of 2026-11-06 (`madison` on api.ftp-master.debian.org).
- Measured on one machine in a container, a server answering initialize, tools/list and one tools/call over 48 skills: Python stdlib alone 15 ms to the first reply and 12 MiB; the same on Debian's SDK 386 ms, 65 MiB and 41 more packages (62 MiB installed); a static Zig binary of 282 KB 0.4 ms and 0.8 MiB.
  Time the interpreter, not the protocol: most of the 15 ms is Python starting.

## The Skills extension (`io.modelcontextprotocol/skills`)

- Merged as SEP-2640 on 2026-09-13; the specification text sits in `specification/beta/` of modelcontextprotocol/ext-skills since 2026-10-29 (SEP-3392), so check its status again.
- A server declares `resources` and the extension in `server/discover`, implements `skills/list` and `skills/get`, and serves every file through `resources/read` at `skill://<skill-path>/<file-path>`.
  The last segment of `<skill-path>` must equal the skill's `name`; the entry carries the frontmatter verbatim and a complete manifest (URI, SHA-256 digest, byte size per file); at most 512 files and 16 MiB per skill.
- To a client that does not implement the extension, the `skill://` resources are ordinary resources, and many assistants show only tools, so serve the same reads as tools too.
- Hosts must not let an MCP skill silently shadow a same-named skill from another origin, and must not honour `allowed-tools` or run code from it without per-skill approval.
  A server therefore never widens permissions in a skill it serves and says where each skill comes from.
- Client support: the project's own matrix lists only partial support (ChatGPT, fast-agent, MCP Inspector) on 2026-11-06.

## The skill format

agentskills.io/specification: `name` 1-64 characters, lower case letters, digits and single hyphens, equal to the folder name; `description` 1-1024 characters; optional `license`, `compatibility`, `metadata` (string keys to string values), `allowed-tools` (experimental); `scripts/`, `references/`, `assets/` optional.
Claude Code adds more frontmatter fields it acts on (`when_to_use`, `disable-model-invocation`, `hooks`, ...); keep them out of skills that other tools must read.

## Where assistants read skills and register servers (documentation read 2026-11-06)

| Assistant | System-wide skills | Register a local stdio server | Remove |
| --- | --- | --- | --- |
| Claude Code | `/etc/claude-code/.claude/skills` (managed) | `claude mcp add --scope user NAME -- COMMAND ARGS` (stored in `~/.claude.json`) | `claude mcp remove NAME` |
| Codex | `/etc/codex/skills` (admin) | `codex mcp add NAME -- COMMAND ARGS` (`~/.codex/config.toml`, `[mcp_servers.NAME]`) | delete the table, or `enabled = false` |
| Gemini CLI | none documented | `gemini mcp add -s user NAME COMMAND ARGS` (`~/.gemini/settings.json`, `mcpServers`) | `gemini mcp remove -s user NAME` |
| OpenCode | none documented | `opencode mcp add NAME --global -- COMMAND ARGS` | delete the entry in its config |
| Cline | none documented | `cline mcp add NAME --yes -- COMMAND ARGS` (`~/.cline/data/settings/cline_mcp_settings.json`) | `cline mcp remove NAME` |
| Cursor | none documented | edit `~/.cursor/mcp.json` (`mcpServers`, `command`, `args`) | delete the entry |
| VS Code Copilot | none documented | "MCP: Add Server" (stdio); `servers` key in its own mcp.json | the same dialog |
| goose | none documented | `goose configure` (extension, command line) or `extensions:` in `~/.config/goose/config.yaml` | `goose configure`, Remove |
| Open WebUI | none | no stdio: native MCP is Streamable HTTP only, set by an administrator; its Skills import takes a ZIP of skill folders | |

Use the assistant's own command to register where it has one: it writes its own format, and its remove undoes it.
A server name without underscores is safer (Gemini CLI splits tool names on the first underscore).

## What Debian ships

Debian testing (Contents-amd64, 2026-11-06) has five `SKILL.md` files, all incidental (Rust crate sources, hol-light), and no directory convention for skills; the only MCP packages are `ruby-mcp`, `libmcp-perl` and `python3-mcp` (unstable).
The conventions to follow for a data directory are FHS 3.0 through Debian Policy 9.1.1 (`/usr/share` for architecture-independent files), the freedesktop Base Directory specification 0.8 (`$XDG_DATA_HOME`, `$XDG_DATA_DIRS`, the more important directory first) and dpkg's file ownership (two packages may not ship the same path).

## Traps from checking the existing finder

- The offline finder and `context` ignore a skill's `requires-packages` header; only `link` honours it, so `find` can point to a skill whose package is not installed.
  Check eligibility in one place for every door.
- `context` reads the commit from `SOURCE` or from git; in a container without git and without `SOURCE` it prints an error and exits 2.

## Building the server in cgm-zig, hyper-modular (ORDER 430 milestone 2)

The server is Zig built with the station's cgm-zig, laid out so that a path tells its concern, its level and its owner.
The layout lives next to the code (`docs/TREE.md` of the product); the short recipe:

1. Put authored Zig under `compiled/L<n>_<name>/`, one folder per level; a level imports only lower levels (primitive, atomic, executable, organization, context, domain).
   Give each module only the imports its level may use in `build.zig`, so a wrong import fails to compile, and add a test that reads the sources and fails on an upward import.
2. Make every variant a file in a `_kinds/<registry>/` folder (protocol era, assistant, skill kind, language, tool).
   Zig cannot discover files at run time, so `build.zig` lists the folder and writes one registry module; adding a variant is adding a file.
   Test it by adding and removing a file in a scratch folder and by searching the parents for the variant's id as a string (the id of a variant must not appear outside `_kinds/`).
3. Write contracts and failing tests first: atoms that return `error.NotImplemented`, tests that state the expected value from an outside source (the extension's own digests, a golden recorded from the Python engine).
   A stub that refuses everything passes the "must refuse" tests vacuously; trust only the tests whose positive twin fails, and show each lint test going red on a copy that breaks its rule.
4. Run the test binaries in a container, never on the host: build them static (`-target x86_64-linux-musl`) with the station's compiler, then `docker run --network none --ulimit core=0 --tmpfs /tmp` with the product tree mounted read only.

Traps:
- cgm-zig is dynamically linked against LLVM; compile on the station, run the static result in the container.
- A directory iterated in `build.zig` is `b.build_root.handle` with `b.graph.io` (Zig 0.16 `std.Io`); `b.addTest` rejects a name that looks like a path, so name tests `<folder>_<file>`.
- `std.testing.tmpDir` writes `.zig-cache` in the working directory; with a read only mount, make the scratch folder under `/tmp` instead.
- A comment that names a variant trips the "no hardcoded variant" lint; the lint skips comment lines.
- The extension page's example skill (`pdf-processing`: 151, 29 and 35 bytes) is the fixture; re-compute its digests with `sha256sum` from the fixture files before trusting a number in notes.

### What running it taught (milestone 2b)

Recipe, in order: build with `zig build test-bins`, run every test binary in the container (`scripts/run-tests.sh`), then drive the program itself end to end (`scripts/e2e.sh`: command line against goldens recorded from the old engine, both MCP eras over pipes, stub assistants in a throwaway HOME that record their argv, the command gate both ways), then show each rule going red when removed (`scripts/mutation-controls.sh`; a mutation that fails to compile proves nothing, so the script requires the test binary to exist).
- The commands a skill may run are data (`commands.json`: id, argv with whole-argument `{slot}` tokens, slot classes `word`, `int`, `enum:a,b`, `expect.exit`, `expect.stdout_contains`, `run`: assistant or person). Zig has no regular expressions; classes cannot be made to run for ever.
- Policy `auto`: an AI assistant found (its program on PATH or its folder in the home) means the assistant's approval applies, none found means the person is asked; `mcp commands auto|assistant|ask` switches it and is saved in the same state file as the other choices, which `statefile` rewrites without touching other lines.
- Traps:
  - `docker run --tmpfs /tmp` is `noexec` by default: a stub assistant written under /tmp fails with AccessDenied; add `,exec`.
  - `set -o pipefail` with `grep -q` on the right makes a pipeline fail when the writer is cut short by the early exit: capture the output first, then grep it.
  - A test with a stub program on PATH makes "no AI tool found" false; clear PATH for that case.
  - Inline `for` over a registry cannot `continue` out of a runtime loop; look the variant up into a plain struct first.
  - A lint that searches parents for variant ids finds real slips (the hardcoded kind name in `--root`); give the engine a function that picks it from the registry instead of a literal.
  - Disk: a Zig cache grows by hundreds of MB per rebuilt test set; delete it between runs on a small scratch disk.

### The package split and a real client (milestone 2c)

Recipe:
1. Split the work between a helper and an engine package: the helper (`Architecture: all`) keeps link, unlink, the dialog and export; the engine (`Architecture: amd64`, one static program) is what the helper execs for find, list, context, sections, commands, run, mcp and serve.
   The helper Depends on the engine at its own version, because the feature needs it.
   Build both from one source package: `debian/control` lists two binary packages, `debian/rules` has `binary-indep` (the helper) and `binary-arch` (the engine) and `binary: binary-indep binary-arch`; the source carries the engine's tracked files under `engine-src/`.
   Rebuild from the `.dsc` (`dpkg-source -x`, `dpkg-buildpackage -us -uc -b`) and compare SHA-256 with the first build: both `.deb` files came out byte for byte the same.
2. Run the Lean Code link gate (`python3 -m lean.release check-link --archive-config FILE --scratch DIR --root-min-free-gib 12 HELPER.deb ENGINE.deb`) in the build image with the network, the three `--security-opt` options bubblewrap needs, and a public archive named in the config file.
3. Prove it under dpkg in a container as root: the published helper installs; the new helper alone is left unconfigured (its Depends); the pair installs over the published helper; the helper's old verbs still work; a second package that ships `usr/share/agent-skills/user/NAME/SKILL.md` adds a skill and removing it removes the skill; a third package shipping the same path is refused by dpkg ("trying to overwrite ... which is also in package ..."); removal leaves nothing of the engine.
4. Drive `serve` with the official MCP SDK client (`pip install mcp` into a virtual environment in an image built with the network, then run `--network none`): `Client(StdioServerParameters(command=..., args=["serve"]), mode=M)` with M `legacy`, `auto` (the SDK tries `server/discover`, then `initialize`) and the stateless version string.
   Record what each does: the negotiated version, the server name, the capabilities, the tools and their annotations, a call, an error, the resources.

Traps:
- A hand-written `server/discover` reply passed hand-written tests and the SDK still would have refused it: the 2026-07-28 `DiscoverResult` requires `supportedVersions`, `capabilities`, `ttlMs` and `cacheScope` (and `resultType`), and the server's name goes in `_meta` under `io.modelcontextprotocol/serverInfo`, not in a `serverInfo` field. In `auto` mode a reply that does not validate silently falls back to the legacy handshake, so check `protocol_version`, not only that the session worked.
- A client pinned to a version adopts it without asking the server: it shows no server name and no capabilities. That is the SDK, not a defect.
- `ping` is removed in 2026-07-28; the SDK warns when it is sent outside legacy mode.
- An environment variable set to an empty string is not an override: the helper tests `[ -n "$VAR" ]`, the engine must too (the dpkg test caught 2 skills the helper linked and the engine did not list).
- A log line built from a slice of a stack buffer prints garbage once the buffer's block has ended; copy the text into the log record.
- `dpkg-genchanges` fails when a binary package's `Section` differs between `debian/control`, the `.deb` and `dpkg-distaddfile`; the engine package inherits the source's section unless it sets its own.
- A source package that copies a recipe folder (`HERE=$W/recipe`) must take other trees from the original folder (`$RECIPE/../..`), not from the copy.
- `docker run --tmpfs` has no `exec`; the mutation and dpkg tests write helper programs under /tmp and need `,exec`.

Once the new engine matched the old one on recorded rankings, the old Python tool was deleted (plain git deletion, no rewritten history); its last commit is 9c834ddc312e0c92f4923bfe088e67b3cd54d0bc in Sparky-OS/sparky-stereo-os.
Work that replaces a tool this way: record the old tool's answers as data first (the goldens and the routing set), keep the tests reading that data, then delete the tool, so no test needs it afterwards.

### Rebuilding the pair (milestone 2d)

- The engine's `DEBIAN/control` is written by hand, so it must say `Source: <source package>`: without it the build record is split by binary name and the engine's record lacks the `.buildinfo`. With it, `check-debs` writes ONE record named after the source (`sparky-stereo-skills_VERSION_amd64.sparky-build.json`) that lists every `.deb` (helper, engine, HR companion), the `.buildinfo`, the `.changes` and the `.dsc`. Check with `dpkg-deb -f ENGINE.deb Source` and by reading the record's `debs`, `files` and `unrecorded` (empty).
- Date a native package's changelog entry in the past of the build. The Lean Code step clamps the files it writes to SOURCE_DATE_EPOCH only when they are newer than it; with an entry dated hours ahead of the clock their modification times are the build's own minute, and a rebuild from the `.dsc` differs from the first build in those times alone.
- A second-model review of changed strings can be blocked outside the work ("Your workspace is out of credits."): keep the packet and the exact error, leave the strings marked for native review, and use no stand-in model.
