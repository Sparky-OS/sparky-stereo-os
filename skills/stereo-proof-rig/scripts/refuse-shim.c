/* SPDX-License-Identifier: GPL-2.0-or-later */
/* refuse-shim.c: a compositor library that refuses the Wayland stereo declaration, to prove how a player behaves when the compositor does not take its 3D area. Preload it:
 *   STEREO_REFUSE=1            every declaration is refused (-ENOTSUP, what libstereo-declare returns when the compositor's global is gone)
 *   STEREO_REFUSE_FILE=PATH    the declaration is refused while PATH exists (a case can start refusing while the video plays)
 * Anything else goes to the real stereo_declare_wayland. Every call is counted on stderr: "stereo-shim: declare call N: refused|passed". */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int stereo_declare_wayland(void *surface, int layout, int content_class, unsigned subclass)
{
    static int (*real)(void *, int, int, unsigned);
    static int calls;
    if (!real) {
        /* the library is a dependency of a QML plugin, loaded after the player started and not in the global scope RTLD_NEXT searches: asked by its name */
        void *library = dlopen("libstereo-declare.so.1", RTLD_LAZY | RTLD_NOLOAD);
        real = library ? dlsym(library, "stereo_declare_wayland") : dlsym(RTLD_NEXT, "stereo_declare_wayland");
    }
    const char *file = getenv("STEREO_REFUSE_FILE");
    int refuse = (getenv("STEREO_REFUSE") && *getenv("STEREO_REFUSE") == '1') || (file && access(file, F_OK) == 0);
    fprintf(stderr, "stereo-shim: declare call %d: %s\n", ++calls, refuse ? "refused" : "passed");
    if (refuse)
        return -ENOTSUP;
    if (!real) { fprintf(stderr, "stereo-shim: the real stereo_declare_wayland is not found\n"); return -ENOTSUP; }
    int result = real(surface, layout, content_class, subclass);
    fprintf(stderr, "stereo-shim: the real one returned %d\n", result);
    return result;
}
