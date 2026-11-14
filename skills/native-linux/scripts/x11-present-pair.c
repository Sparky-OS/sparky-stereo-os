/* x11-present-pair.c: what a GL library's software path does for a stereo window from declaration version 4, without OpenGL.
 * A window W by H, declared full side by side (_KDE_NET_WM_STEREO_CONTENT_VERSION 4, then _KDE_NET_WM_STEREO_CONTENT 3),
 * and a pixmap 2W by H presented to it with the Present extension: left view red, right view blue, a green rectangle in
 * the middle of each, and a white square that moves 16 pixels with every present, at the same place in both views (so a
 * reader can tell that both eyes show the same frame).  Prints how the X server completed each present (flip: the pixmap went to the window's surface
 * whole; copy: it was copied into the one view wide window, which keeps the left view only).
 *   NODECLARE=1   the control: no declaration, so the server must copy
 *   CHILD=1       the window is a child of a plain top-level 200 wider and 100 taller, at 100,50 in it; the top-level lists
 *                 it in _KDE_NET_WM_STEREO_CONTENT_CHILDREN
 *   FRAMES=N      presents (default 200), PERIOD_MS apart (default 50)     W, H: one view's size (default 800x600)
 *   WM=1          stand in for the compositor's window manager: redirect the root's children (Composite, manual), which is
 *                 what gives a top-level its surface on a rootless Xwayland; and redirect the declared child, as a
 *                 compositor does for a child a window lists
 *   COVER=1       a 60x60 plain child window over the declared one, so the server cannot flip (the case a copy still decides)
 *   HOLD_S=N      stay N seconds after the last present
 *   EXPECT=flip|copy   exit 1 unless the last present completed that way
 * Build: cc -O1 -o x11-present-pair x11-present-pair.c -lxcb -lxcb-present -lxcb-composite
 * SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <xcb/xcb.h>
#include <xcb/composite.h>
#include <xcb/present.h>

static xcb_atom_t atom(xcb_connection_t *c, const char *n)
{
    xcb_intern_atom_reply_t *r = xcb_intern_atom_reply(c, xcb_intern_atom(c, 0, strlen(n), n), NULL);
    xcb_atom_t a = r ? r->atom : XCB_ATOM_NONE;
    free(r);
    return a;
}

static void cardinal(xcb_connection_t *c, xcb_window_t w, const char *name, xcb_atom_t type, uint32_t v)
{
    xcb_change_property(c, XCB_PROP_MODE_REPLACE, w, atom(c, name), type, 32, 1, &v);
}

int main(void)
{
    int W = getenv("W") ? atoi(getenv("W")) : 800, H = getenv("H") ? atoi(getenv("H")) : 600;
    int frames = getenv("FRAMES") ? atoi(getenv("FRAMES")) : 200, child = getenv("CHILD") != NULL;
    const char *expect = getenv("EXPECT"), *last = "none";
    int period = getenv("PERIOD_MS") ? atoi(getenv("PERIOD_MS")) * 1000 : 50000;
    int flips = 0, copies = 0, others = 0;
    xcb_connection_t *c = xcb_connect(NULL, NULL);
    if (!c || xcb_connection_has_error(c)) { printf("x11-present-pair: NO-DISPLAY\n"); return 2; }
    xcb_screen_t *s = xcb_setup_roots_iterator(xcb_get_setup(c)).data;
    const xcb_query_extension_reply_t *ext = xcb_get_extension_data(c, &xcb_present_id);
    if (!ext || !ext->present) { printf("x11-present-pair: NO-PRESENT\n"); return 2; }
    if (getenv("WM"))
        xcb_composite_redirect_subwindows(c, s->root, XCB_COMPOSITE_REDIRECT_MANUAL);
    uint32_t ev[] = { s->black_pixel, XCB_EVENT_MASK_STRUCTURE_NOTIFY | XCB_EVENT_MASK_EXPOSURE };
    xcb_window_t top = xcb_generate_id(c), win = top;
    xcb_create_window(c, XCB_COPY_FROM_PARENT, top, s->root, 100, 100, child ? W + 200 : W, child ? H + 100 : H, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, s->root_visual,
                      XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, ev);
    xcb_change_property(c, XCB_PROP_MODE_REPLACE, top, XCB_ATOM_WM_NAME, XCB_ATOM_STRING, 8, 12, "present-pair");
    if (child) {
        win = xcb_generate_id(c);
        xcb_create_window(c, XCB_COPY_FROM_PARENT, win, top, 100, 50, W, H, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, s->root_visual,
                          XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, ev);
    }
    if (!getenv("NODECLARE")) {
        cardinal(c, win, "_KDE_NET_WM_STEREO_CONTENT_VERSION", XCB_ATOM_CARDINAL, 4);
        cardinal(c, win, "_KDE_NET_WM_STEREO_CONTENT", XCB_ATOM_CARDINAL, 3);
        if (child)
            cardinal(c, top, "_KDE_NET_WM_STEREO_CONTENT_CHILDREN", XCB_ATOM_WINDOW, win);
    }
    if (getenv("COVER")) {   /* a small plain child window over the declared one: its pixmap can no longer be flipped */
        xcb_window_t cover = xcb_generate_id(c);
        uint32_t grey[] = { 0x808080 };
        xcb_create_window(c, XCB_COPY_FROM_PARENT, cover, win, 30, H / 2, 60, 60, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT, s->root_visual,
                          XCB_CW_BACK_PIXEL, grey);
        xcb_map_window(c, cover);
    }
    if (child) {
        xcb_map_window(c, win);
        if (getenv("WM") && !getenv("NODECLARE"))
            xcb_composite_redirect_window(c, win, XCB_COMPOSITE_REDIRECT_MANUAL);
    }
    xcb_map_window(c, top);
    xcb_flush(c);
    xcb_generic_event_t *e;
    while ((e = xcb_wait_for_event(c))) {   /* until the window is on the screen */
        int t = e->response_type & 0x7f;
        free(e);
        if (t == XCB_EXPOSE) break;
    }
    usleep(getenv("SETTLE_MS") ? atoi(getenv("SETTLE_MS")) * 1000 : 500000);
    xcb_present_event_t eid = xcb_generate_id(c);
    xcb_present_select_input(c, eid, win, XCB_PRESENT_EVENT_MASK_COMPLETE_NOTIFY);
    xcb_gcontext_t gc = xcb_generate_id(c);
    xcb_create_gc(c, gc, win, 0, NULL);
    for (int i = 1; i <= frames; i++) {
        xcb_pixmap_t p = xcb_generate_id(c);
        xcb_create_pixmap(c, s->root_depth, p, win, 2 * W, H);
        const uint32_t colour[] = { 0xff0000, 0x0000ff, 0x00ff00, 0xffffff };
        const int16_t mx = 20 + (i * 16) % (W - 80);
        const xcb_rectangle_t mark[] = { { mx, 20, 40, 40 }, { W + mx, 20, 40, 40 } };
        const xcb_rectangle_t left = { 0, 0, W, H }, right = { W, 0, W, H };
        const xcb_rectangle_t mid[] = { { W / 4, H / 4, W / 2, H / 2 }, { W + W / 4, H / 4, W / 2, H / 2 } };
        xcb_change_gc(c, gc, XCB_GC_FOREGROUND, &colour[0]); xcb_poly_fill_rectangle(c, p, gc, 1, &left);
        xcb_change_gc(c, gc, XCB_GC_FOREGROUND, &colour[1]); xcb_poly_fill_rectangle(c, p, gc, 1, &right);
        xcb_change_gc(c, gc, XCB_GC_FOREGROUND, &colour[2]); xcb_poly_fill_rectangle(c, p, gc, 2, mid);
        xcb_change_gc(c, gc, XCB_GC_FOREGROUND, &colour[3]); xcb_poly_fill_rectangle(c, p, gc, 2, mark);
        xcb_present_pixmap(c, win, p, i, 0, 0, 0, 0, 0, 0, 0, XCB_PRESENT_OPTION_NONE, 0, 0, 0, 0, NULL);
        xcb_free_pixmap(c, p);
        xcb_flush(c);
        for (int done = 0; !done && (e = xcb_wait_for_event(c)); free(e)) {
            xcb_ge_generic_event_t *ge = (xcb_ge_generic_event_t *) e;
            if ((e->response_type & 0x7f) != XCB_GE_GENERIC || ge->extension != ext->major_opcode ||
                ge->event_type != XCB_PRESENT_COMPLETE_NOTIFY)
                continue;
            xcb_present_complete_notify_event_t *cn = (xcb_present_complete_notify_event_t *) e;
            if (cn->kind != XCB_PRESENT_COMPLETE_KIND_PIXMAP || cn->serial != (uint32_t) i)
                continue;
            last = cn->mode == XCB_PRESENT_COMPLETE_MODE_FLIP ? "flip" : cn->mode == XCB_PRESENT_COMPLETE_MODE_COPY ? "copy" : "other";
            if (cn->mode == XCB_PRESENT_COMPLETE_MODE_FLIP) flips++;
            else if (cn->mode == XCB_PRESENT_COMPLETE_MODE_COPY) copies++;
            else others++;
            if (i <= 3 || i == frames) { printf("x11-present-pair: present %d completed as %s\n", i, last); fflush(stdout); }
            done = 1;
        }
        if (xcb_connection_has_error(c)) { printf("x11-present-pair: CONNECTION-LOST after %d presents\n", i); return 3; }
        usleep(period);
    }
    if (getenv("HOLD_S"))   /* keep the last picture on the screen (a capture of a still window) */
        sleep(atoi(getenv("HOLD_S")));
    printf("x11-present-pair: %d presents of a %dx%d pixmap to a %dx%d window: %d flips, %d copies, %d other; last %s\n",
           frames, 2 * W, H, W, H, flips, copies, others, last);
    if (expect && strcmp(expect, last)) { printf("x11-present-pair: FAIL, the last present must complete as %s\n", expect); return 1; }
    return 0;
}
