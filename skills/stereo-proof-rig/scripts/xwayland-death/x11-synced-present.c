/* Row 862, fault B: an X11 window presented with explicit sync (DRI3 1.4 PresentPixmapSynced, timeline syncobjs),
 * then touched by another path, to find which commit of Xwayland carries a buffer with no acquire point.
 * Usage: x11-synced-present WIDTH HEIGHT FRAMES AFTER [stereo|child]
 *   stereo: the window is declared full side-by-side stereo, KDE declaration version 4 (one eye wide, pixmaps of both
 *           eyes twice its width), so the edition's Xwayland flips the double-width pixmap (patch 0005)
 *   child: the same declaration on a child window half the window's size, listed in the window's
 *          _KDE_NET_WM_STEREO_CONTENT_CHILDREN; core-fill also draws in the window across the child
 *   AFTER: none | core-fill (XFillRectangle on the window) | copy-present (PresentPixmap without sync) |
 *          resize (the window grows by 16 px) | unsynced-buffer (a second pixmap presented with PresentPixmap)
 * Prints each PresentCompleteNotify's mode, and "X connection broken" with the error when Xwayland went away.
 * SPDX-License-Identifier: MIT */
#include <fcntl.h>
#include <gbm.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <xcb/dri3.h>
#include <xcb/present.h>
#include <xcb/xcb.h>
#include <xf86drm.h>

static xcb_connection_t *c;
static int drm_fd;
static struct gbm_device *gbm;

static void die(const char *what)
{
    fprintf(stderr, "x11-synced-present: %s\n", what);
    exit(1);
}

static xcb_pixmap_t make_pixmap(xcb_window_t win, int w, int h, uint32_t colour)
{
    struct gbm_bo *bo = gbm_bo_create(gbm, w, h, GBM_FORMAT_XRGB8888, GBM_BO_USE_RENDERING | GBM_BO_USE_LINEAR);
    if (!bo) {
        /* NVIDIA's GBM refuses a linear rendering buffer: the driver's own layout, contents left as they come */
        bo = gbm_bo_create(gbm, w, h, GBM_FORMAT_XRGB8888, GBM_BO_USE_RENDERING);
        if (bo)
            fprintf(stderr, "x11-synced-present: a linear buffer was refused, using the driver's layout\n");
    }
    if (!bo)
        die("gbm_bo_create failed");
    uint32_t stride = 0;
    void *map_data = NULL;
    uint32_t *px = gbm_bo_map(bo, 0, 0, w, h, GBM_BO_TRANSFER_WRITE, &stride, &map_data);
    if (px) {
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
                px[y * (stride / 4) + x] = colour;
        gbm_bo_unmap(bo, map_data);
    } else {
        fprintf(stderr, "x11-synced-present: gbm_bo_map failed, the buffer keeps its contents\n");
    }
    int fd = gbm_bo_get_fd(bo);
    xcb_pixmap_t p = xcb_generate_id(c);
    xcb_void_cookie_t ck = xcb_dri3_pixmap_from_buffer_checked(c, p, win, gbm_bo_get_stride(bo) * h, w, h,
                                                                gbm_bo_get_stride(bo), 24, 32, fd);
    xcb_generic_error_t *e = xcb_request_check(c, ck);
    if (e)
        die("DRI3 PixmapFromBuffer refused");
    return p;
}

static uint32_t make_syncobj(xcb_window_t win, uint32_t *handle)
{
    if (drmSyncobjCreate(drm_fd, 0, handle))
        die("drmSyncobjCreate failed");
    int fd = -1;
    if (drmSyncobjHandleToFD(drm_fd, *handle, &fd))
        die("drmSyncobjHandleToFD failed");
    uint32_t id = xcb_generate_id(c);
    xcb_generic_error_t *e = xcb_request_check(c, xcb_dri3_import_syncobj_checked(c, id, win, fd));
    if (e)
        die("DRI3 ImportSyncobj refused");
    return id;
}

static void drain(int wait_ms)
{
    for (int i = 0; i < wait_ms / 10; i++) {
        xcb_generic_event_t *ev;
        while ((ev = xcb_poll_for_event(c))) {
            if ((ev->response_type & 0x7f) == XCB_GE_GENERIC) {
                xcb_present_complete_notify_event_t *pe = (void *)ev;
                if (pe->event_type == XCB_PRESENT_EVENT_COMPLETE_NOTIFY)
                    printf("present complete serial %u mode %s\n", pe->serial,
                           pe->mode == XCB_PRESENT_COMPLETE_MODE_FLIP ? "flip"
                           : pe->mode == XCB_PRESENT_COMPLETE_MODE_COPY ? "copy"
                           : pe->mode == XCB_PRESENT_COMPLETE_MODE_SKIP ? "skip" : "suboptimal-copy");
            }
            free(ev);
        }
        if (xcb_connection_has_error(c)) {
            printf("X connection broken (error %d)\n", xcb_connection_has_error(c));
            fflush(stdout);
            exit(3);
        }
        usleep(10000);
    }
    fflush(stdout);
}

int main(int argc, char **argv)
{
    if (argc < 5) {
        fprintf(stderr, "usage: x11-synced-present WIDTH HEIGHT FRAMES none|core-fill|copy-present|resize|unsynced-buffer [stereo]\n");
        return 2;
    }
    const int w = atoi(argv[1]), h = atoi(argv[2]), frames = atoi(argv[3]);
    const char *after = argv[4];
    /* child: the presents go to a child window of the window, declared and listed as the stereo child (the edition's
     * Xwayland gives a redirected child a surface of its own, patches 0001 to 0003; 0014 keeps its 2D cover) */
    const int child = argc > 5 && !strcmp(argv[5], "child");
    const int stereo = child || (argc > 5 && !strcmp(argv[5], "stereo"));
    const int tw = child ? w / 2 : w, th = child ? h / 2 : h;
    const int pw = stereo ? 2 * tw : tw;
    c = xcb_connect(NULL, NULL);
    if (xcb_connection_has_error(c))
        die("cannot connect to the X server");
    xcb_dri3_query_version_reply_t *dv = xcb_dri3_query_version_reply(c, xcb_dri3_query_version(c, 1, 4), NULL);
    xcb_present_query_version_reply_t *pv = xcb_present_query_version_reply(c, xcb_present_query_version(c, 1, 4), NULL);
    if (!dv || !pv)
        die("no DRI3 or Present");
    printf("DRI3 %u.%u Present %u.%u\n", dv->major_version, dv->minor_version, pv->major_version, pv->minor_version);
    xcb_screen_t *s = xcb_setup_roots_iterator(xcb_get_setup(c)).data;
    xcb_window_t top = xcb_generate_id(c);
    const uint32_t values[] = {0x000000, XCB_EVENT_MASK_EXPOSURE | XCB_EVENT_MASK_STRUCTURE_NOTIFY};
    xcb_create_window(c, 24, top, s->root, 0, 0, w, h, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, s->root_visual,
                      XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, values);
    xcb_change_property(c, XCB_PROP_MODE_REPLACE, top, XCB_ATOM_WM_NAME, XCB_ATOM_STRING, 8, 15, "synced-present");
    xcb_window_t win = top;
    if (child) {
        win = xcb_generate_id(c);
        const uint32_t cv[] = {0x00202020, XCB_EVENT_MASK_EXPOSURE};
        xcb_create_window(c, 24, win, top, 40, 40, tw, th, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, s->root_visual,
                          XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, cv);
        xcb_map_window(c, win);
    }
    if (stereo) {
        const char *names[] = {"_KDE_NET_WM_STEREO_CONTENT", "_KDE_NET_WM_STEREO_CONTENT_VERSION"};
        const uint32_t vals[] = {3, 4};
        for (int i = 0; i < 2; i++) {
            xcb_intern_atom_reply_t *a = xcb_intern_atom_reply(c, xcb_intern_atom(c, 0, strlen(names[i]), names[i]), NULL);
            xcb_change_property(c, XCB_PROP_MODE_REPLACE, win, a->atom, XCB_ATOM_CARDINAL, 32, 1, &vals[i]);
            free(a);
        }
        printf("declared full side by side, version 4%s; pixmaps %dx%d\n", child ? " on a child window" : "", pw, th);
    }
    xcb_map_window(c, top);
    xcb_flush(c);
    drain(800);
    if (child) {
        /* listed once the window is managed, as Mesa's GLX lists its stereo child at the first swap */
        xcb_intern_atom_reply_t *a = xcb_intern_atom_reply(c, xcb_intern_atom(c, 0, 32, "_KDE_NET_WM_STEREO_CONTENT_CHILDREN"), NULL);
        xcb_change_property(c, XCB_PROP_MODE_REPLACE, top, a->atom, XCB_ATOM_WINDOW, 32, 1, &win);
        free(a);
        xcb_flush(c);
        drain(800);
    }

    xcb_present_query_capabilities_reply_t *caps =
        xcb_present_query_capabilities_reply(c, xcb_present_query_capabilities(c, win), NULL);
    printf("present capabilities 0x%x (syncobj %s)\n", caps ? caps->capabilities : 0,
           caps && (caps->capabilities & XCB_PRESENT_CAPABILITY_SYNCOBJ) ? "yes" : "no");
    if (!caps || !(caps->capabilities & XCB_PRESENT_CAPABILITY_SYNCOBJ))
        die("Xwayland offers no explicit sync here (the compositor or the GPU gives it no syncobj timelines)");

    xcb_dri3_open_reply_t *open = xcb_dri3_open_reply(c, xcb_dri3_open(c, s->root, 0), NULL);
    if (!open)
        die("DRI3 Open failed");
    drm_fd = xcb_dri3_open_reply_fds(c, open)[0];
    gbm = gbm_create_device(drm_fd);
    if (!gbm)
        die("gbm_create_device failed");
    printf("render node driver %s\n", gbm_device_get_backend_name(gbm));

    const uint32_t eid = xcb_generate_id(c);
    xcb_present_select_input(c, eid, win, XCB_PRESENT_EVENT_MASK_COMPLETE_NOTIFY);
    xcb_pixmap_t pix = make_pixmap(win, pw, th, 0x00ff0000);
    uint32_t acquire_handle, release_handle;
    const uint32_t acquire = make_syncobj(win, &acquire_handle), release = make_syncobj(win, &release_handle);
    uint64_t point = 0;
    for (int i = 0; i < frames; i++) {
        point++;
        if (drmSyncobjTimelineSignal(drm_fd, &acquire_handle, &point, 1))
            die("drmSyncobjTimelineSignal failed");
        xcb_present_pixmap_synced(c, win, pix, i + 1, 0, 0, 0, 0, 0, acquire, release, point, point, 0, 0, 0, 0, 0, NULL);
        xcb_flush(c);
        drain(100);
    }
    drain(400);
    printf("after %s\n", after);
    fflush(stdout);
    if (!strcmp(after, "core-fill")) {
        xcb_gcontext_t gc = xcb_generate_id(c);
        const uint32_t fg = 0x0000ff00;
        xcb_create_gc(c, gc, win, XCB_GC_FOREGROUND, &fg);
        xcb_rectangle_t r = {10, 10, (uint16_t)(tw / 2), (uint16_t)(th / 2)};
        if (child) {
            /* the parent draws across the child's place first (the child's 2D cover), then the child is drawn on */
            xcb_rectangle_t across = {20, 20, (uint16_t)(w - 40), (uint16_t)(h / 3)};
            xcb_poly_fill_rectangle(c, top, gc, 1, &across);
        }
        xcb_poly_fill_rectangle(c, win, gc, 1, &r);
    } else if (!strcmp(after, "copy-present")) {
        xcb_present_pixmap(c, win, pix, frames + 1, 0, 0, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, NULL);
    } else if (!strcmp(after, "resize")) {
        const uint32_t size[] = {(uint32_t)tw + 16, (uint32_t)th + 16};
        xcb_configure_window(c, win, XCB_CONFIG_WINDOW_WIDTH | XCB_CONFIG_WINDOW_HEIGHT, size);
    } else if (!strcmp(after, "unsynced-buffer")) {
        xcb_pixmap_t other = make_pixmap(win, pw, th, 0x000000ff);
        xcb_present_pixmap(c, win, other, frames + 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, NULL);
    }
    xcb_flush(c);
    drain(2000);
    printf("ended with the X connection whole\n");
    return 0;
}
