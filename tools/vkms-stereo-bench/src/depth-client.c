// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * depth-client: a window for the picture and depth checks of the bench.
 *
 * The window is WINDOW_W x WINDOW_H, plain in its colour (COLOR, default
 * 0000ff) with a textured patch: the same grey noise in both views, the
 * right view's moved PARALLAX pixels to the right (default 8), so the patch
 * lies PARALLAX pixels of parallax behind the window (the right eye's copy to
 * the right of the left eye's). The window's surface is declared full side by
 * side with kde_stereo_content_v1 version 2 (one eye wide, its buffer both
 * eyes); NO_STEREO=1 makes it a plain 2D window showing the left view, the
 * patch without parallax. POPUP=1 opens a yellow popup over the window, which
 * the desktop draws with its chrome. HOLD_SECONDS (default 10) is how long it
 * stays.
 */
#define _GNU_SOURCE
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include <wayland-client.h>
#include "kde-stereo-content-v1-client-protocol.h"
#include "xdg-shell-client-protocol.h"

#define WINDOW_W 480
#define WINDOW_H 240
#define PATCH_X 80
#define PATCH_Y 40
#define PATCH_W 320
#define PATCH_H 160
#define POPUP_W 120
#define POPUP_H 60

struct client {
	struct wl_compositor *compositor;
	struct wl_shm *shm;
	struct xdg_wm_base *wm_base;
	struct kde_stereo_content_manager_v1 *stereo;
	bool configured;
	bool popup_configured;
};

static void fail(const char *what)
{
	fprintf(stderr, "depth-client: %s\n", what);
	exit(1);
}

static void wm_ping(void *data, struct xdg_wm_base *wm_base, uint32_t serial)
{
	xdg_wm_base_pong(wm_base, serial);
}

static const struct xdg_wm_base_listener wm_listener = { .ping = wm_ping };

static void surface_configure(void *data, struct xdg_surface *surface, uint32_t serial)
{
	xdg_surface_ack_configure(surface, serial);
	*(bool *)data = true;
}

static const struct xdg_surface_listener surface_listener = { .configure = surface_configure };

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel, int32_t w, int32_t h, struct wl_array *states)
{
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
}

static const struct xdg_toplevel_listener toplevel_listener = {
	.configure = toplevel_configure,
	.close = toplevel_close,
};

static void popup_configure(void *data, struct xdg_popup *popup, int32_t x, int32_t y, int32_t w, int32_t h)
{
}

static void popup_done(void *data, struct xdg_popup *popup)
{
}

static void popup_repositioned(void *data, struct xdg_popup *popup, uint32_t token)
{
}

static const struct xdg_popup_listener popup_listener = {
	.configure = popup_configure,
	.popup_done = popup_done,
	.repositioned = popup_repositioned,
};

static void registry_global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
	struct client *c = data;

	if (!strcmp(interface, wl_compositor_interface.name))
		c->compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
	else if (!strcmp(interface, wl_shm_interface.name))
		c->shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
	else if (!strcmp(interface, xdg_wm_base_interface.name)) {
		c->wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, 1);
		xdg_wm_base_add_listener(c->wm_base, &wm_listener, c);
	} else if (!strcmp(interface, kde_stereo_content_manager_v1_interface.name) && version >= 2)
		c->stereo = wl_registry_bind(registry, name, &kde_stereo_content_manager_v1_interface, 2);
}

static void registry_global_remove(void *data, struct wl_registry *registry, uint32_t name)
{
}

static const struct wl_registry_listener registry_listener = {
	.global = registry_global,
	.global_remove = registry_global_remove,
};

// grey noise, the same for the same point of the patch in either view
static uint32_t noise(int u, int v)
{
	uint32_t h = (uint32_t)u * 374761393u + (uint32_t)v * 668265263u;
	h = (h ^ (h >> 13)) * 1274126177u;
	const uint32_t grey = (h ^ (h >> 16)) & 0xff;
	return 0xff000000u | grey << 16 | grey << 8 | grey;
}

static struct wl_buffer *create_buffer(struct client *c, int width, int height, uint32_t **pixels)
{
	const int stride = width * 4;
	const int size = stride * height;
	const int fd = memfd_create("depth-client", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, size) < 0)
		fail("no shared memory");
	*pixels = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (*pixels == MAP_FAILED)
		fail("mmap failed");
	struct wl_shm_pool *pool = wl_shm_create_pool(c->shm, fd, size);
	struct wl_buffer *buffer = wl_shm_pool_create_buffer(pool, 0, width, height, stride, WL_SHM_FORMAT_ARGB8888);
	wl_shm_pool_destroy(pool);
	close(fd);
	return buffer;
}

// one view: the window's colour, and the patch moved @parallax pixels to the right
static void draw_view(uint32_t *pixels, int stride, int x0, uint32_t colour, int parallax)
{
	for (int y = 0; y < WINDOW_H; y++) {
		for (int x = 0; x < WINDOW_W; x++) {
			uint32_t value = colour;
			const int u = x - PATCH_X - parallax;
			const int v = y - PATCH_Y;
			if (x >= PATCH_X && x < PATCH_X + PATCH_W && v >= 0 && v < PATCH_H && u >= 0 && u < PATCH_W)
				value = noise(u, v);
			pixels[y * stride + x0 + x] = value;
		}
	}
}

int main(void)
{
	const bool stereo = !getenv("NO_STEREO");
	const bool popup = getenv("POPUP") != NULL;
	const int parallax = getenv("PARALLAX") ? atoi(getenv("PARALLAX")) : 8;
	const uint32_t colour = 0xff000000u | (getenv("COLOR") ? (uint32_t)strtoul(getenv("COLOR"), NULL, 16) : 0x0000ffu);
	const int hold = getenv("HOLD_SECONDS") ? atoi(getenv("HOLD_SECONDS")) : 10;
	struct client c = { 0 };

	struct wl_display *display = wl_display_connect(NULL);
	if (!display)
		fail("no Wayland display");
	struct wl_registry *registry = wl_display_get_registry(display);
	wl_registry_add_listener(registry, &registry_listener, &c);
	wl_display_roundtrip(display);
	if (!c.compositor || !c.shm || !c.wm_base)
		fail("missing globals");
	if (stereo && !c.stereo)
		fail("no kde_stereo_content_manager_v1 version 2");

	struct wl_surface *surface = wl_compositor_create_surface(c.compositor);
	struct xdg_surface *xdg_surface = xdg_wm_base_get_xdg_surface(c.wm_base, surface);
	xdg_surface_add_listener(xdg_surface, &surface_listener, &c.configured);
	struct xdg_toplevel *toplevel = xdg_surface_get_toplevel(xdg_surface);
	xdg_toplevel_add_listener(toplevel, &toplevel_listener, NULL);
	xdg_toplevel_set_title(toplevel, "depth-client");
	if (stereo) {
		struct kde_stereo_content_v1 *declaration = kde_stereo_content_manager_v1_create(c.stereo, surface);
		kde_stereo_content_v1_set_content(declaration, KDE_STEREO_CONTENT_V1_CONTENT_SIDE_BY_SIDE_FULL);
	}
	wl_surface_commit(surface);
	while (!c.configured && wl_display_dispatch(display) != -1) {
	}

	// both eyes in one buffer, left first; one eye without stereo
	const int width = stereo ? 2 * WINDOW_W : WINDOW_W;
	uint32_t *pixels;
	struct wl_buffer *buffer = create_buffer(&c, width, WINDOW_H, &pixels);
	draw_view(pixels, width, 0, colour, 0);
	if (stereo)
		draw_view(pixels, width, WINDOW_W, colour, parallax);
	wl_surface_attach(surface, buffer, 0, 0);
	wl_surface_damage_buffer(surface, 0, 0, width, WINDOW_H);
	wl_surface_commit(surface);

	if (popup) {
		struct wl_surface *popup_surface = wl_compositor_create_surface(c.compositor);
		struct xdg_surface *popup_xdg = xdg_wm_base_get_xdg_surface(c.wm_base, popup_surface);
		xdg_surface_add_listener(popup_xdg, &surface_listener, &c.popup_configured);
		struct xdg_positioner *positioner = xdg_wm_base_create_positioner(c.wm_base);
		xdg_positioner_set_size(positioner, POPUP_W, POPUP_H);
		xdg_positioner_set_anchor_rect(positioner, 16, 16, 1, 1);
		xdg_positioner_set_anchor(positioner, XDG_POSITIONER_ANCHOR_TOP_LEFT);
		xdg_positioner_set_gravity(positioner, XDG_POSITIONER_GRAVITY_BOTTOM_RIGHT);
		struct xdg_popup *xdg_popup = xdg_surface_get_popup(popup_xdg, xdg_surface, positioner);
		xdg_popup_add_listener(xdg_popup, &popup_listener, NULL);
		wl_surface_commit(popup_surface);
		while (!c.popup_configured && wl_display_dispatch(display) != -1) {
		}
		uint32_t *popup_pixels;
		struct wl_buffer *popup_buffer = create_buffer(&c, POPUP_W, POPUP_H, &popup_pixels);
		for (int i = 0; i < POPUP_W * POPUP_H; i++)
			popup_pixels[i] = 0xffffff00u;
		wl_surface_attach(popup_surface, popup_buffer, 0, 0);
		wl_surface_damage_buffer(popup_surface, 0, 0, POPUP_W, POPUP_H);
		wl_surface_commit(popup_surface);
	}

	const time_t end = time(NULL) + hold;
	while (time(NULL) < end) {
		wl_display_flush(display);
		if (wl_display_dispatch_pending(display) == -1)
			break;
		usleep(50000);
		wl_display_roundtrip(display);
	}
	return 0;
}
