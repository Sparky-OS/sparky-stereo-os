/* Xwayland's surface window moves from a child that presented with explicit sync to its toplevel and back,
 * with damage posted in between, so the next commit attaches the child's own flipped pixmap.
 * Usage: x11-surface-switch FRAMES MODE [managed]
 *   The toplevel T has a 32-bit (ARGB) visual; its child C has the 24-bit root visual and covers T exactly, so the
 *   server redirects C by itself (another visual than its parent's) and Xwayland makes C the surface window of T's
 *   surface (xwl_window_update_surface_window). C is presented FRAMES times with PresentPixmapSynced (DRI3 1.4 GBM
 *   buffer, timeline syncobjs), which flips: C's window pixmap is then the client's pixmap and Xwayland keeps its
 *   wp_linux_drm_syncobj_surface_v1.
 *   MODE switch: in one flush, a small ARGB sibling S is raised over C (the surface window becomes T, S is painted,
 *                T's damage is queued) and lowered below C again (the surface window is C again; C has no background,
 *                nothing is painted). The queued damage is posted with C's window pixmap, the client's.
 *        split:  the same two requests with 500 ms between them, so Xwayland posts T's damage before S goes (control).
 *        none:   only the flips (control).
 *   S stays mapped below C between switches: Xwayland walks only the first children (the top of the stack), and an
 *   unmapped or destroyed S ends or misses that walk (its clip notify runs while S is still first).
 *   managed: T is an ordinary window the window manager manages; default override-redirect (no frame around it).
 * Prints each PresentCompleteNotify's mode, then "ended with the X connection whole" or "X connection broken".
 * SPDX-License-Identifier: MIT */
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
    fprintf(stderr, "x11-surface-switch: %s\n", what);
    exit(1);
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
            } else if ((ev->response_type & 0x7f) == 0) {
                xcb_generic_error_t *e = (void *)ev;
                printf("X error %u on request %u.%u\n", e->error_code, e->major_code, e->minor_code);
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

static xcb_pixmap_t make_pixmap(xcb_window_t win, int w, int h, uint32_t colour)
{
    struct gbm_bo *bo = gbm_bo_create(gbm, w, h, GBM_FORMAT_XRGB8888, GBM_BO_USE_RENDERING | GBM_BO_USE_LINEAR);
    if (!bo)
        bo = gbm_bo_create(gbm, w, h, GBM_FORMAT_XRGB8888, GBM_BO_USE_RENDERING);
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
    }
    xcb_pixmap_t p = xcb_generate_id(c);
    xcb_generic_error_t *e = xcb_request_check(c, xcb_dri3_pixmap_from_buffer_checked(c, p, win,
        gbm_bo_get_stride(bo) * h, w, h, gbm_bo_get_stride(bo), 24, 32, gbm_bo_get_fd(bo)));
    if (e)
        die("DRI3 PixmapFromBuffer refused");
    return p;
}

static uint32_t make_syncobj(xcb_window_t win, uint32_t *handle)
{
    int fd = -1;
    if (drmSyncobjCreate(drm_fd, 0, handle) || drmSyncobjHandleToFD(drm_fd, *handle, &fd))
        die("cannot make a syncobj");
    uint32_t id = xcb_generate_id(c);
    if (xcb_request_check(c, xcb_dri3_import_syncobj_checked(c, id, win, fd)))
        die("DRI3 ImportSyncobj refused");
    return id;
}

/* S: a small ARGB sibling over C, painted when mapped or raised */
static xcb_window_t sibling(xcb_window_t top, xcb_visualid_t argb, xcb_colormap_t cmap)
{
    xcb_window_t sib = xcb_generate_id(c);
    const uint32_t sv[] = {0xff00ff00, 0, cmap};
    xcb_create_window(c, 32, sib, top, 20, 20, 60, 40, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, argb,
                      XCB_CW_BACK_PIXEL | XCB_CW_BORDER_PIXEL | XCB_CW_COLORMAP, sv);
    xcb_map_window(c, sib);
    return sib;
}

static void stack(xcb_window_t win, uint32_t mode)
{
    xcb_configure_window(c, win, XCB_CONFIG_WINDOW_STACK_MODE, &mode);
}

static xcb_visualid_t argb_visual(xcb_screen_t *s)
{
    for (xcb_depth_iterator_t d = xcb_screen_allowed_depths_iterator(s); d.rem; xcb_depth_next(&d)) {
        if (d.data->depth != 32)
            continue;
        for (xcb_visualtype_iterator_t v = xcb_depth_visuals_iterator(d.data); v.rem; xcb_visualtype_next(&v))
            if (v.data->_class == XCB_VISUAL_CLASS_TRUE_COLOR)
                return v.data->visual_id;
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: x11-surface-switch FRAMES switch|split|none [managed]\n");
        return 2;
    }
    const int frames = atoi(argv[1]);
    const char *mode = argv[2];
    const int managed = argc > 3 && !strcmp(argv[3], "managed");
    const int w = 400, h = 300;
    c = xcb_connect(NULL, NULL);
    if (xcb_connection_has_error(c))
        die("cannot connect to the X server");
    xcb_dri3_query_version_reply_t *dv = xcb_dri3_query_version_reply(c, xcb_dri3_query_version(c, 1, 4), NULL);
    xcb_present_query_version_reply_t *pv = xcb_present_query_version_reply(c, xcb_present_query_version(c, 1, 4), NULL);
    if (!dv || !pv)
        die("no DRI3 or Present");
    xcb_screen_t *s = xcb_setup_roots_iterator(xcb_get_setup(c)).data;
    const xcb_visualid_t argb = argb_visual(s);
    if (!argb)
        die("no 32-bit TrueColor visual");
    xcb_colormap_t cmap = xcb_generate_id(c);
    xcb_create_colormap(c, XCB_COLORMAP_ALLOC_NONE, cmap, s->root, argb);

    /* T: ARGB toplevel */
    xcb_window_t top = xcb_generate_id(c);
    const uint32_t tv[] = {0xff000000, 0, (uint32_t)!managed, XCB_EVENT_MASK_EXPOSURE | XCB_EVENT_MASK_STRUCTURE_NOTIFY, cmap};
    xcb_create_window(c, 32, top, s->root, 0, 0, w, h, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, argb,
                      XCB_CW_BACK_PIXEL | XCB_CW_BORDER_PIXEL | XCB_CW_OVERRIDE_REDIRECT | XCB_CW_EVENT_MASK |
                      XCB_CW_COLORMAP, tv);
    xcb_change_property(c, XCB_PROP_MODE_REPLACE, top, XCB_ATOM_WM_NAME, XCB_ATOM_STRING, 8, 14, "surface-switch");
    /* C: 24-bit child over all of T, no background (an exposure paints nothing) */
    xcb_window_t child = xcb_generate_id(c);
    const uint32_t cv[] = {XCB_BACK_PIXMAP_NONE, 0, XCB_EVENT_MASK_EXPOSURE, s->default_colormap};
    xcb_create_window(c, s->root_depth, child, top, 0, 0, w, h, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, s->root_visual,
                      XCB_CW_BACK_PIXMAP | XCB_CW_BORDER_PIXEL | XCB_CW_EVENT_MASK | XCB_CW_COLORMAP, cv);
    xcb_map_window(c, child);
    xcb_map_window(c, top);
    xcb_flush(c);
    drain(800);
    printf("T 0x%x (depth 32%s), C 0x%x (depth %u)\n", top, managed ? ", managed" : ", override-redirect",
           child, s->root_depth);
    /* Settle: C gets its own pixmap after T's surface chose its surface window; the next clip change of C (S over it
     * and gone) makes Xwayland choose C, so C's presents can flip. */
    xcb_window_t sib = sibling(top, argb, cmap);
    xcb_flush(c);
    drain(300);
    stack(sib, XCB_STACK_MODE_BELOW);
    xcb_flush(c);
    drain(300);

    xcb_present_query_capabilities_reply_t *caps =
        xcb_present_query_capabilities_reply(c, xcb_present_query_capabilities(c, child), NULL);
    printf("present capabilities 0x%x (syncobj %s)\n", caps ? caps->capabilities : 0,
           caps && (caps->capabilities & XCB_PRESENT_CAPABILITY_SYNCOBJ) ? "yes" : "no");
    if (!caps || !(caps->capabilities & XCB_PRESENT_CAPABILITY_SYNCOBJ))
        die("Xwayland offers no explicit sync here");
    xcb_dri3_open_reply_t *open = xcb_dri3_open_reply(c, xcb_dri3_open(c, s->root, 0), NULL);
    if (!open)
        die("DRI3 Open failed");
    drm_fd = xcb_dri3_open_reply_fds(c, open)[0];
    gbm = gbm_create_device(drm_fd);
    if (!gbm)
        die("gbm_create_device failed");
    printf("render node driver %s\n", gbm_device_get_backend_name(gbm));

    const uint32_t eid = xcb_generate_id(c);
    xcb_present_select_input(c, eid, child, XCB_PRESENT_EVENT_MASK_COMPLETE_NOTIFY);
    xcb_pixmap_t pix[2] = {make_pixmap(child, w, h, 0x00ff0000), make_pixmap(child, w, h, 0x000000ff)};
    uint32_t acquire_handle, release_handle;
    const uint32_t acquire = make_syncobj(child, &acquire_handle), release = make_syncobj(child, &release_handle);
    uint64_t point = 0;
    for (int i = 0; i < frames; i++) {
        point += 2;
        uint64_t ap = point - 1;
        if (drmSyncobjTimelineSignal(drm_fd, &acquire_handle, &ap, 1))
            die("drmSyncobjTimelineSignal failed");
        xcb_present_pixmap_synced(c, child, pix[i & 1], i + 1, 0, 0, 0, 0, 0, acquire, release, ap, point,
                                  0, 0, 0, 0, 0, NULL);
        xcb_flush(c);
        drain(100);
    }
    drain(500);
    printf("after %s\n", mode);
    fflush(stdout);
    if (!strcmp(mode, "switch")) {
        stack(sib, XCB_STACK_MODE_ABOVE);
        stack(sib, XCB_STACK_MODE_BELOW);
        xcb_flush(c);
    } else if (!strcmp(mode, "split")) {
        stack(sib, XCB_STACK_MODE_ABOVE);
        xcb_flush(c);
        drain(500);
        stack(sib, XCB_STACK_MODE_BELOW);
        xcb_flush(c);
    }
    drain(2000);
    /* a round trip: a dead server shows here */
    free(xcb_get_input_focus_reply(c, xcb_get_input_focus(c), NULL));
    drain(100);
    printf("ended with the X connection whole\n");
    return 0;
}
