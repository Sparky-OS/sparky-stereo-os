/* x11-swap-requests-shim.c: preloaded into a GLX client, it logs what the GL library hands the X server at a swap (the first
 * four of each call): the pixmap it creates, the image it puts into it, the present. The GL library is loaded privately by
 * libglvnd, so each real function is looked up in its own library when RTLD_NEXT finds nothing.
 * Build: cc -shared -fPIC -o x11-swap-requests-shim.so x11-swap-requests-shim.c -ldl   Use: LD_PRELOAD=./x11-swap-requests-shim.so PROGRAM
 * SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <X11/Xlib.h>
#include <X11/extensions/XShm.h>
#include <xcb/xcb.h>
static int n[4];
static void *find(const char *lib, const char *sym)
{
    void *f = dlsym(RTLD_NEXT, sym);
    if (!f) { void *h = dlopen(lib, RTLD_NOW); f = h ? dlsym(h, sym) : NULL; }
    if (!f) { fprintf(stderr, "x11-swap-requests-shim: no %s\n", sym); _exit(8); }
    return f;
}
Pixmap XCreatePixmap(Display *d, Drawable dr, unsigned w, unsigned h, unsigned depth)
{
    static Pixmap (*real)(Display *, Drawable, unsigned, unsigned, unsigned);
    if (!real) real = find("libX11.so.6", "XCreatePixmap");
    Pixmap p = real(d, dr, w, h, depth);
    if (n[0]++ < 4) fprintf(stderr, "x11-swap-requests-shim: XCreatePixmap %ux%u depth %u for 0x%lx -> 0x%lx\n", w, h, depth, dr, p);
    return p;
}
int XPutImage(Display *d, Drawable dr, GC gc, XImage *im, int sx, int sy, int dx, int dy, unsigned w, unsigned h)
{
    static int (*real)(Display *, Drawable, GC, XImage *, int, int, int, int, unsigned, unsigned);
    if (!real) real = find("libX11.so.6", "XPutImage");
    if (n[1]++ < 4) fprintf(stderr, "x11-swap-requests-shim: XPutImage %ux%u to 0x%lx\n", w, h, dr);
    return real(d, dr, gc, im, sx, sy, dx, dy, w, h);
}
Bool XShmPutImage(Display *d, Drawable dr, GC gc, XImage *im, int sx, int sy, int dx, int dy, unsigned w, unsigned h, Bool ev)
{
    static Bool (*real)(Display *, Drawable, GC, XImage *, int, int, int, int, unsigned, unsigned, Bool);
    if (!real) real = find("libXext.so.6", "XShmPutImage");
    if (n[2]++ < 4) fprintf(stderr, "x11-swap-requests-shim: XShmPutImage %ux%u to 0x%lx\n", w, h, dr);
    return real(d, dr, gc, im, sx, sy, dx, dy, w, h, ev);
}
typedef struct { unsigned int sequence; } cookie_t;
cookie_t xcb_present_pixmap(xcb_connection_t *c, uint32_t window, uint32_t pixmap, uint32_t serial, uint32_t valid, uint32_t update,
                            int16_t x_off, int16_t y_off, uint32_t crtc, uint32_t wait_fence, uint32_t idle_fence, uint32_t options,
                            uint64_t target_msc, uint64_t divisor, uint64_t remainder, uint32_t notifies_len, const void *notifies)
{
    static cookie_t (*real)(xcb_connection_t *, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, int16_t, int16_t, uint32_t, uint32_t,
                            uint32_t, uint32_t, uint64_t, uint64_t, uint64_t, uint32_t, const void *);
    if (!real) real = find("libxcb-present.so.0", "xcb_present_pixmap");
    if (n[3]++ < 4) fprintf(stderr, "x11-swap-requests-shim: xcb_present_pixmap window 0x%x pixmap 0x%x options %u\n", window, pixmap, options);
    return real(c, window, pixmap, serial, valid, update, x_off, y_off, crtc, wait_fence, idle_fence, options, target_msc, divisor, remainder, notifies_len, notifies);
}
