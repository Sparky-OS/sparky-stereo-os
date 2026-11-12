# The mixed texture: a procedure and a picture in one glTF 2.0 texture

Draft by the ORDER 508 lane, 2026-11-11, for Daniel's decision; nothing filed.
The extension's name in this draft is a working name, `SPARKY_texture_mixed`: the `SPARKY` prefix is not registered (glTF's `extensions/Prefixes.md` lists none of ours), and the name, the prefix and the container are Daniel's call (see "Names and where they come from" and "Other containers").

## What it is for

Daniel's words (2026-11-11): "the final form of this that we're doing is a mixed texture format, that we can then embed into a web scene, and this scene MUST load first all procedures, start the drawing along side the multiconnection texture download that said procedures will blent to and stop being computed".
One texture asset carries both parts: the procedure (kilobytes), and the reference to the full picture.
A scene that uses it loads in five steps:

1. every procedure of the scene arrives first;
2. drawing starts at once from the procedures;
3. the pictures download beside it, over several connections;
4. each procedure blends into its picture as the picture arrives;
5. that procedure then stops being computed.

This is the last layer of Dynamic Procedural Foveated Rendering (DPFR, Daniel's term, 2026-10-26: "the last layer of it is a hi res texture, that loads while the procedural does its thing").

## The fields

On a texture (glTF 2.0, 5.29 `texture`):

```json
{
  "name": "brick wall",
  "sampler": 0,
  "source": 0,
  "extensions": {
    "SPARKY_texture_mixed": { "procedure": 0 }
  }
}
```

- `source` is the ordinary glTF picture (glTF 2.0, 3.8.2 and 5.29.2), a JPEG or PNG in `images`. It MUST be present: it is what a viewer that ignores the extension shows, and it is the picture the procedure blends into.
- `procedure` (integer, required): the index of the procedure in the root object's `procedures` array.

On the asset's root `extensions`:

```json
{
  "extensionsUsed": ["SPARKY_texture_mixed"],
  "extensions": {
    "SPARKY_texture_mixed": {
      "version": 1,
      "procedures": [
        { "name": "brick wall procedure", "uri": "procedures/red_brick_03.p2p", "language": "p2p", "version": 1, "byteLength": 1069 }
      ]
    }
  }
}
```

- `version` (integer, required): the version word of this extension object, 1 here. A reader that does not know the version treats every mixed texture as an ordinary texture (it shows the pictures) and says so.
- `procedures` (array, required, at least one entry). Each procedure is referenced as glTF 2.0 references an image (5.18 `image`): exactly one of `uri` (a relative path, an absolute URI or a `data:` URI) and `bufferView` (then `mimeType` is required).
- `language` (string, required): the procedure's language. `p2p` is the fitter's typed script of ORDER 508 (one operator per line: `ID OPERATOR INPUTS WORDS...`, the inputs `-` or `ID,ID`, the words 32-bit hexadecimal, an `out ID` line naming the result); werkkzeug3's operators (Farbrausch) keep their own words, and every modern operator's first word is its own version word.
- `version` (integer, required): the version word of the language, 1 here. A reader checks it, and then each operator's own version word against what it can draw; anything it does not know is said, and that texture shows its picture alone.
- `byteLength` (integer, optional): the procedure's size in bytes, so a reader can state the scene's procedure total before fetching (as Dreamweaver's download time does).
- `name` (string, optional): how the scene names the procedure.

The extension is listed in `extensionsUsed` and NOT in `extensionsRequired` (glTF 2.0, 3.12): every mixed texture keeps its picture, so a viewer without the extension still draws the scene.
The validator refuses a scene that lists it as required while every mixed texture has its picture.

## What a reader that ignores it sees

The scene as glTF 2.0 defines it: each texture with its `source` picture.
Nothing else changes; the procedures are files the viewer never fetches.
Checked with the Khronos glTF-Validator and with three.js's GLTFLoader (see the lane's report).

## What a reader that knows it does

Fetch every procedure before any picture (step 1); draw each from its procedure at once (step 2); fetch the pictures beside the drawing over several connections (step 3); when a texture's picture has arrived and is decoded, blend from the procedure's drawing into the picture (step 4); when the blend ends, release the procedure's drawing and give it no more work (step 5).
How the blend runs is the player's (and the person's) choice, not the file's: the scene tester offers a cross-fade and a blend that takes the picture's coarse levels first and its detail last.

## One procedure and one picture per eye

For a stereo texture the texture's extension object carries `views`, exactly two entries, one per eye:

```json
"SPARKY_texture_mixed": {
  "procedure": 0,
  "views": [
    { "eye": "left", "procedure": 0, "source": 0 },
    { "eye": "right", "procedure": 7, "source": 7 }
  ]
}
```

- `eye` is "left" or "right", each once: WebXR's `XREye` values (WebXR Device API, the `XRView.eye` attribute).
- The left eye's `procedure` and `source` are the texture's own, so a 2D reader (and a reader that ignores the extension) shows the left eye, as a 2D output shows the left eye of a full side by side frame.
- Each eye's picture is a whole picture of its own, at any resolution; nothing is packed into one image here, so there is no input packing to undo. A writer that receives a stereo photograph packed side by side, top and bottom or in any other layout unpacks it to the two pictures first.
- A player draws each eye's texture in that eye's view; in 2D it draws the left eye.

The three kinds of stereo document and how each is carried:

1. A 2D texture whose relief gives the depth below the surface for each eye (sunk or at the surface, never popped; 473y and 473z): the mono form above; the relief is the procedure's own height output. This version defines no field for it yet.
2. Two procedures, one per eye: the `views` form, each eye with its procedure and its picture.
3. A stereo photograph of a texture as the source, each eye fitted from pixels to procedure on its own (Daniel, 2026-11-11: "two regular processes, one per eye, from pixel to procedure"): the `views` form. The stereo photograph is media, so the player that shows it offers the input packing and a per-file "Swap left and right eyes" (kept where the player keeps its per-file state, written to the file only when the person chooses).
If two separate fits do not read as stereo, Daniel's next step is one eye fitted and used as the cue for the other, adding only the separation; it is built only on his verdict and would be carried in the same `views` form.

## Names and where they come from

| name here | where it comes from |
|---|---|
| `texture.source` as the picture, the extension object on the texture holding the alternative | KHR_texture_basisu (ratified): `textures[].extensions.KHR_texture_basisu.source`, with `texture.source` the fallback a client without the extension loads |
| `uri`, `bufferView`, `mimeType`, `name` of a procedure | glTF 2.0, 5.18 `image` |
| `byteLength` | glTF 2.0, 5.9 `buffer.byteLength` |
| a root array of procedures, referenced by index from a texture | KHR_texture_procedurals (Khronos draft, PR #2381): a root `procedurals` array referenced by `index` |
| "procedure" rather than "procedural" | Daniel's word ("load first all procedures"); ours differ from KHR_texture_procedurals' `procedurals`, which are node graphs written in JSON, so the same name would say they are the same thing |
| the version word | each modern operator of ORDER 508 already carries one as its first word |
| `views`, `eye`, "left", "right" | WebXR Device API: `XRViewerPose.views`, `XRView.eye`, `XREye` |
| progress per component (the tester's bars) | X3D 4.0's LoadSensor (19775-1, 9.4.3): `progress`, `isLoaded`, `loadTime` |
| DPFR | Daniel's term, 2026-10-25 and 2026-10-26 |

## Other containers (Daniel's call)

- **KHR_texture_procedurals** (Khronos draft): carry the procedure as one of its node graphs, with our operators as a definitions set, as `EXT_texture_procedurals_mx_1_39` names MaterialX 1.39's. Its texture reference keeps an `index` texture "used instead of the procedural graph" (its README, "Material Binding"); Daniel's DPFR comment on PR #2381 (26 October 2026) asked for that `index` texture to be declarable as the graph's refining last layer. That would be this extension's meaning inside their structure; the cost is writing every operator's parameters as named JSON inputs (several times the bytes of the script).
- **MSFT_lod** (vendor, complete): material or node levels of detail, "progressively loading the glTF asset starting with the lowest LOD". A procedure is not a material level, so it would need a material per texture state; the blend and the stop have no place in it.
- **KTX 2.0** beside the picture: its levels are pictures (the specification lets a reader "display a low resolution image quickly without waiting for the entire texture data"), not procedures; a key and value pair could name a procedure file, but glTF viewers read KTX 2.0 only through KHR_texture_basisu.
- **X3D 4.0**: ImageTexture's `url` field holds ordered alternatives (19775-1, 9.3.2 X3DUrlObject); Texturing (clause 18) has no procedural node. The X3D form would be a procedural texture node whose last layer is an ImageTexture, as Michalis Kamburelis offered for Castle Game Engine's ShaderTexture (x3d-public, 27 October 2026).
- **The prefix**: a vendor prefix of ours registered through an issue on KhronosGroup/glTF (`SPARKY` for the edition that ships the player, or `PMKR` for the W3C group where DPFR was presented), or `EXT` once a second implementation exists.

## Validation

`mixedtex.py validate SCENE.gltf` checks every rule above and each procedure's text (the lines parse, every input is defined above its reader, the out line names an operator, each operator is known, each version word is one this reader knows); it exits 1 on any error.
`mixedtex.py write SCENE.gltf --texture NAME --procedure FILE [--right-procedure FILE --right-picture IMAGE]` adds a mixed texture to a scene.
