/* SPDX-License-Identifier: GPL-2.0-or-later */
/* refuse-shim.c: a compositor library that refuses the Wayland stereo declaration, to prove how a player behaves when the compositor does not take its 3D area. Preload it:
 *   STEREO_REFUSE=1            every declaration is refused (-ENOTSUP, what libstereo-declare returns when the compositor's global is gone)
 *   STEREO_REFUSE_FILE=PATH    the declaration is refused while PATH exists (a case can start refusing while the video plays)
 *   STEREO_REFUSE_INIT=1       stereo_declare_wayland_init() fails with -EBUSY (another component of the process holds the library's state)
 *   STEREO_NO_SUPPORT=1        stereo_supported_wayland() answers 0 although the compositor announces the global
 * Anything else goes to the real function. Every call is counted on stderr: "stereo-shim: declare|init|supported call N: ...". */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static int on(const char *name)
{
    const char *v = getenv(name);
    return v && *v == '1';
}

/* the library is a dependency of a QML plugin, loaded after the player started and not in the global scope RTLD_NEXT searches: asked by its name */
static void *real(const char *name)
{
    void *library = dlopen("libstereo-declare.so.1", RTLD_LAZY | RTLD_NOLOAD);
    return library ? dlsym(library, name) : dlsym(RTLD_NEXT, name);
}

int stereo_declare_wayland(void *surface, int layout, int content_class, unsigned subclass)
{
    static int (*fn)(void *, int, int, unsigned);
    static int calls;
    if (!fn)
        fn = real("stereo_declare_wayland");
    const char *file = getenv("STEREO_REFUSE_FILE");
    int refuse = on("STEREO_REFUSE") || (file && access(file, F_OK) == 0);
    fprintf(stderr, "stereo-shim: declare call %d: %s\n", ++calls, refuse ? "refused" : "passed");
    if (refuse)
        return -ENOTSUP;
    if (!fn) {
        fprintf(stderr, "stereo-shim: the real stereo_declare_wayland is not found\n");
        return -ENOTSUP;
    }
    int result = fn(surface, layout, content_class, subclass);
    fprintf(stderr, "stereo-shim: the real one returned %d\n", result);
    return result;
}

int stereo_declare_wayland_init(void *display, void *queue)
{
    static int (*fn)(void *, void *);
    static int calls;
    if (!fn)
        fn = real("stereo_declare_wayland_init");
    fprintf(stderr, "stereo-shim: init call %d: %s\n", ++calls, on("STEREO_REFUSE_INIT") ? "refused (EBUSY)" : "passed");
    if (on("STEREO_REFUSE_INIT"))
        return -EBUSY;
    return fn ? fn(display, queue) : -ENOTSUP;
}

unsigned stereo_supported_wayland(void)
{
    static unsigned (*fn)(void);
    static int calls;
    if (!fn)
        fn = real("stereo_supported_wayland");
    if (on("STEREO_NO_SUPPORT")) {
        if (++calls == 1)
            fprintf(stderr, "stereo-shim: supported call: answers 0\n");
        return 0;
    }
    return fn ? fn() : 0;
}
