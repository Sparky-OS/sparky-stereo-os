# container-guard

**For** a machine where every partner and the person share one container daemon: a command acts only on the containers it names as its own.

## What it does

| Event | What happens |
| --- | --- |
| Before a shell command that kills, stops, removes, restarts or pauses the containers of a list no filter narrows | Refused. The list can be a command substitution, backticks or a pipe into `xargs` or a `while` loop. |
| Before a shell command that does one of those to a service listed under `protected` | Refused, whatever else the command names. |
| Before a shell command that prunes everything on the daemon, with `refuse_global_prune` on | Refused, unless the prune is filtered by a label. Off by default. |

The refusal says what to do next: act on your own containers by name, or list them with a filter on your own prefix.
Looking is never refused: listing, logs and inspection pass, for protected services too.

## Why

Every lane's containers and the services the person runs live on the same daemon.
A cleanup that takes the list of every container as its own stops them all, and an instruction such as "by container id only" does not prevent it: a loop over every id obeys it to the letter.
A service stopped this way is not started again by its restart policy.

No words of Daniel's were given to this work for this hook; the rule it enforces is in [the cleanup recipe](../../skills/system-housekeeping/references/shared-build-machine-cleanup.md): "Docker on a shared daemon, by name only."

## Configuration

One file, `private/hooks/container-guard.json`; [`config.example.json`](config.example.json) shows every key.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The whole hook. |
| `engines` | `docker`, `podman` | The programs it watches. |
| `protected` | two example names | Containers that stay running: an action that names one is refused. The names match whole words, so `my-reference-index-test` is not `reference-index`. |
| `refuse_unfiltered_lists` | `true` | The first row of the table above. |
| `refuse_global_prune` | `false` | The third row. The workstation this comes from keeps the rule in its house rules and does not enforce it with a hook, so it ships off. |

## How it fails

Open, and it says so: a failure inside the hook lets the command through, is written to `errors.log` and told to the person in one line.
It reads the shell text of one command.
A script file that holds such a loop is not seen, so the house rule stays written down as well.

Logs, in `state/hooks/container-guard/`: `refused.log`, `errors.log`.

## Try it by hand

```sh
W=$(mktemp -d) && python3 hooks/install.py init "$W" >/dev/null
E=docker   # the engine's name, kept apart so that this page can be shown where a guard of this kind is on duty
printf '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"%s kill $(%s ps -q)"},"session_id":"demo","cwd":"/"}' "$E" "$E" \
  | python3 hooks/container-guard/hook.py --config "$W/private/hooks/container-guard.json"
```

It prints the refusal as the tool would receive it; nothing is run.

## Tests

`python3 hooks/tests/run.py container-guard` runs 7 tests in [`tests/`](tests/test_container_guard.py): eight commands that are refused, eight that pass, the protected names, the prune switch, text that is only written to a file, and a refusal while another run holds the state lock.
The engine's name is put into each command while the test runs, so the test file can be written on a machine where a guard like this one is on duty.
