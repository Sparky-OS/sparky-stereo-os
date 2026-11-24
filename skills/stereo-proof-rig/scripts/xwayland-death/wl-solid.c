/* A Wayland window of one opaque colour, for measuring a window's opacity on a capture.
 * Usage: wl-solid APP_ID WIDTH HEIGHT [RRGGBB]
 * SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include <errno.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"

static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct xdg_wm_base *wm_base;
static int width, height, configured, running = 1;
static uint32_t colour = 0xffffffff;
static struct wl_surface *surface;
static struct wl_buffer *buffer;

static void ping(void *data, struct xdg_wm_base *b, uint32_t serial) { xdg_wm_base_pong(b, serial); }
static const struct xdg_wm_base_listener wm_listener = {ping};

static void global(void *data, struct wl_registry *r, uint32_t name, const char *iface, uint32_t version)
{
    if (!strcmp(iface, wl_compositor_interface.name))
        compositor = wl_registry_bind(r, name, &wl_compositor_interface, 4);
    else if (!strcmp(iface, wl_shm_interface.name))
        shm = wl_registry_bind(r, name, &wl_shm_interface, 1);
    else if (!strcmp(iface, xdg_wm_base_interface.name)) {
        wm_base = wl_registry_bind(r, name, &xdg_wm_base_interface, 1);
        xdg_wm_base_add_listener(wm_base, &wm_listener, NULL);
    }
}
static void global_remove(void *data, struct wl_registry *r, uint32_t name) {}
static const struct wl_registry_listener registry_listener = {global, global_remove};

static struct wl_buffer *make_buffer(void)
{
    const int stride = width * 4, size = stride * height;
    int fd = memfd_create("wl-solid", MFD_CLOEXEC);
    if (fd < 0 || ftruncate(fd, size) < 0) {
        perror("wl-solid: memfd");
        exit(1);
    }
    uint32_t *px = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (px == MAP_FAILED) {
        perror("wl-solid: mmap");
        exit(1);
    }
    for (int i = 0; i < width * height; i++)
        px[i] = colour;
    munmap(px, size);
    struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, size);
    struct wl_buffer *b = wl_shm_pool_create_buffer(pool, 0, width, height, stride, WL_SHM_FORMAT_XRGB8888);
    wl_shm_pool_destroy(pool);
    close(fd);
    return b;
}

static void surface_configure(void *data, struct xdg_surface *xs, uint32_t serial)
{
    xdg_surface_ack_configure(xs, serial);
    if (!buffer)
        buffer = make_buffer();
    wl_surface_attach(surface, buffer, 0, 0);
    wl_surface_damage_buffer(surface, 0, 0, width, height);
    wl_surface_commit(surface);
    configured = 1;
}
static const struct xdg_surface_listener surface_listener = {surface_configure};

static void top_configure(void *data, struct xdg_toplevel *t, int32_t w, int32_t h, struct wl_array *states) {}
static void top_close(void *data, struct xdg_toplevel *t) { running = 0; }
static const struct xdg_toplevel_listener top_listener = {top_configure, top_close};

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr, "usage: wl-solid APP_ID WIDTH HEIGHT [RRGGBB]\n");
        return 2;
    }
    width = atoi(argv[2]);
    height = atoi(argv[3]);
    if (argc > 4)
        colour = 0xff000000u | (uint32_t)strtoul(argv[4], NULL, 16);
    struct wl_display *display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "wl-solid: cannot connect to the Wayland display\n");
        return 1;
    }
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    wl_display_roundtrip(display);
    if (!compositor || !shm || !wm_base) {
        fprintf(stderr, "wl-solid: missing wl_compositor, wl_shm or xdg_wm_base\n");
        return 1;
    }
    surface = wl_compositor_create_surface(compositor);
    struct xdg_surface *xs = xdg_wm_base_get_xdg_surface(wm_base, surface);
    xdg_surface_add_listener(xs, &surface_listener, NULL);
    struct xdg_toplevel *top = xdg_surface_get_toplevel(xs);
    xdg_toplevel_add_listener(top, &top_listener, NULL);
    xdg_toplevel_set_app_id(top, argv[1]);
    xdg_toplevel_set_title(top, argv[1]);
    wl_surface_commit(surface);
    /* read the socket every turn, so KWin's pings are answered (the proof rig's trap) */
    while (running && wl_display_dispatch(display) != -1) {
    }
    return 0;
}
