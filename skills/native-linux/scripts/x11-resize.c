/* SPDX-License-Identifier: MIT
 * Resize the X11 window named NAME (WM_NAME or _NET_WM_NAME, searched through the tree) to WxH, then print
 * its geometry.
 * A managed window's request goes to the window manager, as a person's resize does.
 * Build: cc -O1 -Wall -o x11-resize x11-resize.c -lxcb ; usage: x11-resize NAME W H */
#include <stdbool.h>
#include <xcb/xcb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static xcb_atom_t net_wm_name;

/* The window's name: WM_NAME, or _NET_WM_NAME (UTF8_STRING), which vkcube sets alone. */
static bool named(xcb_connection_t *c, xcb_window_t w, xcb_atom_t atom, const char *name)
{
   xcb_get_property_reply_t *p = xcb_get_property_reply(c, xcb_get_property(c, 0, w, atom, XCB_GET_PROPERTY_TYPE_ANY, 0, 64), NULL);
   bool yes = p && xcb_get_property_value_length(p) == (int)strlen(name) && !memcmp(xcb_get_property_value(p), name, strlen(name));
   free(p);
   return yes;
}

static xcb_window_t find(xcb_connection_t *c, xcb_window_t w, const char *name)
{
   if (named(c, w, XCB_ATOM_WM_NAME, name) || (net_wm_name && named(c, w, net_wm_name, name)))
      return w;
   xcb_query_tree_reply_t *t = xcb_query_tree_reply(c, xcb_query_tree(c, w), NULL);
   xcb_window_t found = 0;
   if (t) {
      xcb_window_t *kids = xcb_query_tree_children(t);
      for (int i = 0; i < xcb_query_tree_children_length(t) && !found; i++)
         found = find(c, kids[i], name);
      free(t);
   }
   return found;
}

int main(int argc, char **argv)
{
   if (argc != 4) { fprintf(stderr, "usage: x11-resize NAME W H\n"); return 2; }
   xcb_connection_t *c = xcb_connect(NULL, NULL);
   if (xcb_connection_has_error(c)) return 1;
   xcb_intern_atom_reply_t *a = xcb_intern_atom_reply(c, xcb_intern_atom(c, 1, 12, "_NET_WM_NAME"), NULL);
   net_wm_name = a ? a->atom : 0;
   free(a);
   xcb_window_t w = find(c, xcb_setup_roots_iterator(xcb_get_setup(c)).data->root, argv[1]);
   if (!w) { fprintf(stderr, "no window %s\n", argv[1]); return 1; }
   uint32_t size[] = { (uint32_t)atoi(argv[2]), (uint32_t)atoi(argv[3]) };
   xcb_configure_window(c, w, XCB_CONFIG_WINDOW_WIDTH | XCB_CONFIG_WINDOW_HEIGHT, size);
   xcb_flush(c);
   usleep(500000);
   xcb_get_geometry_reply_t *g = xcb_get_geometry_reply(c, xcb_get_geometry(c, w), NULL);
   printf("x11-resize %s 0x%x asked %ux%u now %ux%u\n", argv[1], w, size[0], size[1], g ? g->width : 0, g ? g->height : 0);
   free(g);
   return 0;
}
