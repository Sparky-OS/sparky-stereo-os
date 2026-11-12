# Procedural Texture Rendering: the demo, its tools and its proofs

**For** anyone who wants to run, host or check the demo: where each part lies and the one command for each job.

A 3D scene whose surfaces are first drawn from small procedures and then from their pictures, as one static web page.
An individual contribution by Daniel Campos Ramos, offered as input to the W3C Procedural Memory Knowledge Representation Community Group; the format is a proposal for glTF, not part of glTF.

| Folder | What it holds |
|---|---|
| `site/` | The page as plain files: copy it to any static host, at any path. `site/extension/KHR_texture_procedural_rendering/` is the proposal in glTF's extension template, with its JSON schemas. |
| `player/` | The WebAssembly procedure player's source (the twelve operators and a small root) and its build script. |
| `tools/` | The scene's writer and validator, the local server, the proof drivers, the accessibility checks, the tests. |
| `github-pages/` | A GitHub Actions workflow that deploys a `demos/` folder to GitHub Pages, its check, and a small index page. |

## Run it

```sh
python3 -m http.server 8000 --directory site      # any static server will do; open http://127.0.0.1:8000/
python3 tools/serve.py                            # the local server: the same page, and a link of its own to compare with
```

The page simulates the connection speed itself: the browser downloads each file at its own speed and the page releases the bytes at the chosen rate.
With `tools/serve.py` the panel offers a second link, the local server's, which limits the real transfer.

## Check it

```sh
python3 tools/ptr_texture.py validate site/scene/scene.gltf            # the scene against the proposal
python3 tools/tests/validator_tests.py site/scene NEW-FOLDER           # 18 red and green cases
python3 tools/check_strings.py                                         # the ten languages: keys and placeholders
python3 github-pages/.github/scripts/check_site.py site                # every file the page names, every size, no root address
sh tools/run-proof.sh amd OUT TAG 'speed=d56&conns=6&fps=5' 1700       # one run in Chromium in a container (WebGPU on the GPU)
HOST=static sh tools/run-proof.sh cpu OUT TAG 'speed=dsl8&conns=6' 400 # a plain static server at a sub-path, a browser without WebGPU
DRIVER=a11y.py sh tools/run-proof.sh cpu OUT TAG 'speed=dsl8&conns=6&fps=5' 900     # the WCAG 2.2 checks
sh tools/matrix.sh OUTBASE A && python3 tools/summary.py OUTBASE       # the page's link against the local server's
```

## Build the player

```sh
ZIG=/path/to/zig sh player/build.sh site/player/ptr-player.wasm       # Zig 0.16; about 85 KB, no imports
python3 tools/wasm_sections.py site/player/ptr-player.wasm             # its imports (none) and exports
```

Licence: BSD 2-clause for the code (`site/LICENSE.txt`); the scene's pictures are CC0 from Poly Haven (`site/CREDITS.md`).
