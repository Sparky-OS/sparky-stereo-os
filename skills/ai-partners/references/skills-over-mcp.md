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
