# Reference corpora anyone can rebuild

**For distro developers and their partners, human or model:** which public documents to keep in a local searchable index for the edition's work, and one setup that works, so a hit can be opened and quoted.
Every document here is a free download that needs no account.
The versions are the ones indexed for the edition on 2026-11-01; take the current ones when you build yours, and record which you took.

## What to index, by domain

### Debian packaging

| Document | Publisher | Version | Licence | URL |
| --- | --- | --- | --- | --- |
| Debian Policy Manual | Debian Policy Editors | 4.7.4.1 | GPL-2.0-or-later | https://www.debian.org/doc/debian-policy/ |
| Debian Developer's Reference | Debian Developers | 14.17 | GPL-2.0-or-later | https://www.debian.org/doc/manuals/developers-reference/ |
| apt manual pages: apt_preferences(5), apt.conf(5), sources.list(5), apt-get(8), apt-cache(8) and the rest | Debian (package apt) | 3.3.3 | GPL-2.0-or-later | https://manpages.debian.org/testing/apt/ |
| dpkg manual pages: dpkg(1), dpkg-query(1), dpkg-deb(1), dpkg-maintscript-helper(1) | Debian (package dpkg) | 1.23.11 | GPL-2.0-or-later | https://manpages.debian.org/testing/dpkg/ |
| dpkg-dev manual pages: deb-control(5), deb-conffiles(5), deb-changelog(5), dpkg-buildpackage(1), dpkg-source(1), dpkg-shlibdeps(1) | Debian (package dpkg-dev) | 1.23.11 | GPL-2.0-or-later | https://manpages.debian.org/testing/dpkg-dev/ |
| debhelper(7), dh(1) and every dh_* page | Debian (package debhelper) | 14.5 | GPL-2.0-or-later | https://manpages.debian.org/testing/debhelper/ |
| Lintian tag descriptions | Lintian maintainers | 2.143.0 | GPL-2.0-or-later | https://lintian.debian.org/tags/ |
| Multiarch, Multiarch/HOWTO and Multiarch/Implementation | Debian wiki | retrieved 2026-10-31 | CC-BY-SA-4.0 for edits since 2025-07-24, older text under the wiki's earlier terms (page footer) | https://wiki.debian.org/Multiarch |
| Multi-Arch specification (MultiarchSpec) | Ubuntu wiki, through the Internet Archive (the original page is gone) | retrieved 2026-10-31 | CC-BY-SA-3.0 | https://web.archive.org/web/2024/https://wiki.ubuntu.com/MultiarchSpec |

### The kernel's display stack (DRM and KMS)

| Document | Publisher | Version | Licence | URL |
| --- | --- | --- | --- | --- |
| `Documentation/gpu` and the DRM parts of `Documentation/userspace-api` | Linux kernel developers | 7.3 | per file (GPL-2.0-only, MIT or dual) | https://docs.kernel.org/gpu/ |
| `include/uapi/drm`, `include/linux/hdmi.h`, and the kernel-doc of `drivers/gpu/drm` (`drm_edid.c` parses the EDID's [HDMI®](https://www.hdmi.org/resource/brand) and CTA blocks) | Linux kernel developers | 7.3, from the kernel.org tarball with its signature checked | per file (SPDX line) | https://www.kernel.org/ |

The HDMI® specification, CTA-861 and VESA E-EDID are not in this list: index them only if their publisher offers them without an account.
Until then the kernel's implementation above is the public text to cite, with the specification's own clause named where the code names it.

### Video, containers and their stereo marks

| Document | Publisher | Version | Licence | URL |
| --- | --- | --- | --- | --- |
| H.264, Advanced video coding (Annex D: the frame packing arrangement SEI) | ITU-T | the edition in force (V15 08/2024 numbers the packing table D-8, V16 06/2026 D-9) | © ITU, free download | https://www.itu.int/rec/T-REC-H.264 |
| H.265, High efficiency video coding (Annex D) | ITU-T | the edition in force | © ITU, free download | https://www.itu.int/rec/T-REC-H.265 |
| H.274, Versatile supplemental enhancement information messages | ITU-T | the edition in force | © ITU, free download | https://www.itu.int/rec/T-REC-H.274 |
| RFC 9559, Matroska Media Container Format Specification (`StereoMode`) | IETF | RFC 9559 | IETF Trust Legal Provisions; code components under the Revised BSD License | https://www.rfc-editor.org/rfc/rfc9559 |
| Matroska registries (StereoMode values, Track Plane Types) | IANA | live registry | free to read | https://www.iana.org/assignments/matroska |

### Graphics: Vulkan, OpenGL, EGL, Mesa, Wayland, Qt and KDE

| Document | Publisher | Version | Licence | URL |
| --- | --- | --- | --- | --- |
| The Vulkan specification and its extension proposals | Khronos Group | the current release | CC-BY-4.0 (specification text) | https://registry.khronos.org/vulkan/ |
| OpenGL 4.6 core specification and GLSL 4.60 | Khronos Group | 4.6, 4.60 | © Khronos, free download | https://registry.khronos.org/OpenGL/ |
| EGL specification and extensions | Khronos Group | the current release | © Khronos, free download | https://registry.khronos.org/EGL/ |
| Mesa documentation | The Mesa project | the release you build | Mesa's licence page | https://docs.mesa3d.org/ |
| Wayland documentation and the core protocol | freedesktop.org | the release you build | MIT | https://wayland.freedesktop.org/docs/html/ |
| wayland-protocols, plasma-wayland-protocols | freedesktop.org, KDE | the release you build | MIT; LGPL-2.1-or-later | https://gitlab.freedesktop.org/wayland/wayland-protocols, https://invent.kde.org/libraries/plasma-wayland-protocols |
| Qt 6 documentation | The Qt Company and contributors | the version you build against (the edition's index still holds 6.6.3: rebuild it for 6.11) | GNU FDL 1.3 | https://doc.qt.io/qt-6/ |
| KDE developer documentation | KDE | the website's source repository | CC-BY-SA-4.0 | https://develop.kde.org/docs/ |
| KWin, KIO, Kirigami, KCoreAddons, libplasma and the other frameworks the patches touch: the API comments in their source | KDE | the commit you build | per file (GPL-2.0-or-later, LGPL variants) | https://invent.kde.org/ |

### Wine, Proton and DXVK

| Document | Publisher | Version | Licence | URL |
| --- | --- | --- | --- | --- |
| Wine's README, documentation and manual pages, from the release tarball with its signature checked | WineHQ | the version you build (10.0 indexed) | LGPL-2.1-or-later | https://dl.winehq.org/wine/source/ |
| WineHQ wiki developer pages | WineHQ wiki contributors | retrieved with the date | licence not stated: index for reference, quote briefly | https://gitlab.winehq.org/wine/wine/-/wikis/ |
| DXVK README and wiki | Philip Rebohle (doitsujin) and contributors | the commit you build | Zlib | https://github.com/doitsujin/dxvk |
| vkd3d-proton README and documentation | Hans-Kristian Arntzen and contributors | the commit you build | LGPL-2.1-or-later | https://github.com/HansKristian-Work/vkd3d-proton |
| Proton README and wiki | Valve | the commit you build | the repository's LICENSE.proton (BSD-style), bundled parts under their own | https://github.com/ValveSoftware/Proton |

### Virtual machines: SPICE, QEMU and libvirt

| Document | Publisher | Version | Licence | URL |
| --- | --- | --- | --- | --- |
| spice-protocol headers and changelog | The SPICE project | the commit you build | BSD-3-Clause | https://gitlab.freedesktop.org/spice/spice-protocol |
| SPICE User Manual and Spice Protocol pages | The SPICE project | retrieved with the date | CC-BY-SA-3.0-US (as the pages state) | https://www.spice-space.org/documentation.html |
| QEMU documentation: display, virtio-gpu, SPICE and migration | The QEMU project | the commit you build | GPL-2.0-or-later | https://www.qemu.org/docs/master/ |
| libvirt domain XML: graphics, video and input devices | The libvirt project | the commit you build | LGPL-2.1-or-later | https://libvirt.org/formatdomain.html |

## One working setup

This is the setup of the edition's own index; any vector store and model can do the same job.

- **Store:** [Qdrant](https://qdrant.tech/), one collection per domain (`debian_packaging_corpus`, `linux_drm_kms_corpus` and so on).
- **Embedding:** sentence-transformers/all-MiniLM-L6-v2 through FastEmbed, 384 dimensions, cosine distance, in one named vector (`fast-all-minilm-l6-v2`, the name qdrant-client's FastEmbed integration gives it).
- **Chunks:** 1,000 characters with 100 characters of overlap, cut within one page of one document, so every chunk belongs to a page.
- **Identity:** each point's id is a UUID 5 of the document, its page and the chunk's number, so a rebuild replaces points instead of adding copies.
- **Shards first, then ingest:** extract each document into shards (`{source_doc, shard_id, pages: [{page, content}]}`), count the chunks per shard in a dry run, then ingest in batches (64 at a time worked).

```python
import uuid

def chunks(text, size=1000, overlap=100):
    step = size - overlap
    for n, start in enumerate(range(0, max(len(text) - overlap, 1), step)):
        yield n, text[start:start + size]

def point_id(source_url, page, n):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'{source_url}#page={page}&chunk={n}'))
```

## What makes a hit citable

Store these payload fields with every chunk:

| Field | Holds |
| --- | --- |
| `source_doc` | the document's own name (`apt_preferences.5`, `debian-policy-4.7.4.1`) |
| `page` | the page, chapter or section number within it |
| `source_url` | the public page or file, so the reader can open the original |
| `licence` | the reuse terms, so the reader knows what may be quoted or shared |

A hit without `source_url` can be read but not checked; the edition's older collections lacked it, and their citations came back empty until the tool read `source_doc` and `page` as well (2026-11-01).

**Golden queries:** keep ten questions per collection, each with the `source_doc` that must come back in the top three, and run them after every ingest; a rebuild that loses one has lost a document.

**Gaps measured on 2026-11-01:** a query for H.264's frame packing SEI returned the AV1 specification, because the edition's video collection holds neither ITU-T H.264 nor H.265; and its Qt collection holds Qt 6.6.3, five minor versions behind the Qt the edition builds.

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
