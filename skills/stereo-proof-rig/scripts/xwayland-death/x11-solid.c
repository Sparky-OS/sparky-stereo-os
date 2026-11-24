/* An X11 window of one opaque colour, for the X11 side of the opacity cases.
 * Usage: x11-solid NAME WIDTH HEIGHT [RRGGBB]
 * SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xcb/xcb.h>

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr, "usage: x11-solid NAME WIDTH HEIGHT [RRGGBB]\n");
        return 2;
    }
    const uint16_t w = atoi(argv[2]), h = atoi(argv[3]);
    const uint32_t colour = argc > 4 ? (uint32_t)strtoul(argv[4], NULL, 16) : 0xffffff;
    xcb_connection_t *c = xcb_connect(NULL, NULL);
    if (xcb_connection_has_error(c)) {
        fprintf(stderr, "x11-solid: cannot connect to the X server\n");
        return 1;
    }
    xcb_screen_t *s = xcb_setup_roots_iterator(xcb_get_setup(c)).data;
    xcb_window_t win = xcb_generate_id(c);
    const uint32_t values[] = {colour, XCB_EVENT_MASK_EXPOSURE | XCB_EVENT_MASK_STRUCTURE_NOTIFY};
    xcb_create_window(c, XCB_COPY_FROM_PARENT, win, s->root, 0, 0, w, h, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT,
                      s->root_visual, XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, values);
    xcb_change_property(c, XCB_PROP_MODE_REPLACE, win, XCB_ATOM_WM_NAME, XCB_ATOM_STRING, 8, strlen(argv[1]), argv[1]);
    /* WM_CLASS: instance and class, both the name */
    char cls[256];
    const int n = snprintf(cls, sizeof cls, "%s%c%s", argv[1], 0, argv[1]);
    xcb_change_property(c, XCB_PROP_MODE_REPLACE, win, XCB_ATOM_WM_CLASS, XCB_ATOM_STRING, 8, n + 1, cls);
    xcb_map_window(c, win);
    xcb_flush(c);
    xcb_generic_event_t *e;
    while ((e = xcb_wait_for_event(c)))
        free(e);
    fprintf(stderr, "x11-solid: the X connection ended (error %d)\n", xcb_connection_has_error(c));
    return 3;
}
