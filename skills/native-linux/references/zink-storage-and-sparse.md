# zink on NVIDIA: 64-bit atomics in another buffer, and a sparse buffer's tail reading zero

Two faults that made a point cloud (StereoVista, a compute rasteriser) load and draw nothing on the RTX 3060 through zink, with no error anywhere.
Both are carried as patches in the edition's Mesa since +stereo3d20 (0035 and 0036); each has a test that fails on +stereo3d19 and passes on +stereo3d20.
Read the search first: on 2026-11-09 Mesa main still had both lines, and no merge request or issue named the first.

## Trap 1: 64-bit atomics land in another storage buffer

- Symptom: a compute shader with `atomicMin` on a `uint64_t` array in one storage block reads back the initial value (`~0ull`), the GL error queue is empty, the program links, the bindings are right. radeonsi gives the right numbers for the same shader.
- Cause: `get_bo_var()` (src/gallium/drivers/zink/zink_compiler.c) makes the 64-bit, 16-bit and 8-bit views of the storage buffers by cloning the 32-bit variable `unbreak_bos()` made, then set `driver_location = 0`. zink numbers a shader's blocks from the last binding down and starts the 32-bit view at `first_ssbo`, the lowest block the shader uses. A shader that declares a block it never reads at the highest binding has `first_ssbo = 1`, so the 64-bit view reached the buffer one place below the bound one. The descriptor it reached was valid, so nothing complained.
- Fix: the clone keeps the `driver_location` it was cloned with (patch 0035).
- How it was found: a program-side readback of the framebuffer storage buffer (0 entries set on zink, 169,904 on radeonsi) said the compute pass wrote nothing; a reduced shader with one unconditional atomic per batch still wrote nothing; the same shader outside the program reproduced it; `ZINK_DEBUG=nir` printed `ssbos@32` with driver_location 1 and its clone `ssbos@64` with 0.
- Test: `tests/egl-surfaceless-ssbo64.c` (three blocks, the 64-bit atomic in binding 1, binding 3 declared and never read). Red: the four results are `18446744073709551615`; green: 1010, 2020, 3030, 4040.

## Trap 2: a sparse buffer's last block reads zero on NVIDIA's Vulkan driver

- Symptom: `GL_ARB_sparse_buffer` data written to the end of a buffer whose size is not a whole number of pages reads back zero (864 of 864 bytes of a short buffer, the 31,424 bytes of a partial last page). The validation layers print `VUID-VkSparseMemoryBind-resourceOffset-09491`.
- Cause: `buffer_commit_single()` (zink_bo.c) cut the last sparse bind to the buffer's width (`MIN2(width0 - offset, size)`). Sparse resources bind in whole blocks of the memory requirements' alignment (Vulkan 1.3, chapter 38, `VkSparseMemoryBind`), 64 KiB here; NVIDIA's driver ignores a bind that stops inside a block, so the pages stay unbacked. Mesa issue 10220 (Paulo Zanoni) describes the same bind on Anv.
- Fix: bind up to `align64(width0, ZINK_SPARSE_BUFFER_PAGE_SIZE) - offset`, and create the sparse VkBuffer with its size rounded up to the block (`create_bci()` in zink_resource.c), both in patch 0036.
- How it was found: `VK_INSTANCE_LAYERS=VK_LAYER_KHRONOS_validation` (vulkan-validationlayers in the rig) named the VUID with the sizes 864 and 31424 against alignment 65536.
- Test: `tests/egl-surfaceless-sparse-tail.c`. Red: 864 and 31424 bytes differ; green: 0.

## Trap 3: the first form of the fix ran on NVIDIA and lost the device on RADV

- Symptom: sparse-tail passes on the RTX through zink with the bind rounded up, and fails every run through zink on the Renoir iGPU: `ZINK: vkQueueSubmit failed (VK_ERROR_DEVICE_LOST)`, `radv/amdgpu: Failed to reserve a PRT VA region (-22)`, every byte differing. +stereo3d19 passes the same test there.
- Cause: the bind ended past the VkBuffer, which was created with the size GL asked for. VUID-VkSparseMemoryBind-size-01100 (Vulkan 1.3 spec p.4166): size must be less than or equal to the size of the resource minus resourceOffset. NVIDIA's driver tolerates it, RADV does not.
- Fix: round the sparse buffer's creation size up to the block too.
- How it was found: the package test run (`MESA_LOADER_DRIVER_OVERRIDE=zink` on the AMD node) beside the NVIDIA one. radeonsi, the row the first review used for "green on AMD", never reaches zink's code, so it could not show it. Run the two tests through zink on every GPU you have, not only through each GPU's own driver.
- Dev loop that took minutes, not an hour: unpack the +N source (`dpkg-source -x`, patches applied), edit the file, build only `src/gallium/targets/dri/libgallium-VERSION.so` with `-Dgallium-drivers=zink -Dllvm=disabled -Dvulkan-drivers=` (VERSION in the tree set to the installed package's version, or libEGL_mesa refuses the library and the EGL silently falls to NVIDIA's own driver: read the renderer line), and mount the library over the installed one in a container that has the package installed.

## Running the two on the RTX through zink, in a container

```sh
docker run --rm --ulimit core=0 --network none --device nvidia.com/gpu=0 \
  -e __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json:/usr/share/glvnd/egl_vendor.d/10_nvidia.json \
  -e __GLX_VENDOR_LIBRARY_NAME=mesa -e MESA_LOADER_DRIVER_OVERRIDE=zink -e LIBGL_KOPPER_DISABLE=1 \
  IMAGE sh -c 'cc -O2 -Wall -Wextra -Werror -o /tmp/t egl-surfaceless-ssbo64.c -lEGL -lGL && /tmp/t'
```

The first line must read `renderer: zink Vulkan 1.4(NVIDIA GeForce RTX 3060 ...)`.
Without the second vendor file zink dies with VK_ERROR_INCOMPATIBLE_DRIVER.
With no GPU in the container `MESA_LOADER_DRIVER_OVERRIDE=zink` still gives llvmpipe, whose renderer line says so: a test that counts that as a pass proves nothing.

## The package's own test run

The Mesa source has debian/tests (autopkgtest): `zink-ssbo64` and `zink-sparse-tail`, two small scripts that call `debian/tests/zink-surfaceless NAME`.
That script builds `NAME.c` beside it, runs it with `MESA_LOADER_DRIVER_OVERRIDE=zink` and exits 0 only on PASS with a zink renderer; no zink renderer, or the program stopping before it could draw, exits 77 with "NOT RUN ... this is not a pass" (control: `Restrictions: skippable`, so autopkgtest reports SKIP).
Run it on the installed package in a container with the GPU, on the unpacked source:

```sh
dpkg-source -x mesa_VERSION.dsc src && cd src
autopkgtest --no-built-binaries . -- null    # exit 0 all pass, 4 a test failed, 8 all skipped
```

Expected: `+stereo3d19` fails both on the RTX (exit 4), `+stereo3d20` passes both (exit 0), a container without a GPU skips both (exit 8), and the AMD iGPU through zink over RADV passes both.
Trap: a stanza with both `Tests:` and `Test-Command:` is refused (`InvalidControl test *: Only one of "Tests" or "Test-Command" may be given`); one `Tests:` line naming executable files is the form that works. Found by running autopkgtest once, not by reading the control file.
