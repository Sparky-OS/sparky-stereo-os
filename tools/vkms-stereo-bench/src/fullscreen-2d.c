// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * fullscreen-2d: a plain 2D Wayland client (wl_shm, xdg-shell) that asks for
 * fullscreen and fills the size it gets with a gradient: red grows with x,
 * green with y, blue is 0x80. In a 3D mode the compositor should show it the
 * same in both eyes. Runs for HOLD_SECONDS (default 10), then exits.
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
#include "xdg-shell-client-protocol.h"

struct state {
	struct wl_compositor *compositor;
	struct wl_shm *shm;
	struct xdg_wm_base *wm_base;
	int width, height;
	bool configured;
};

static void wm_ping(void *data, struct xdg_wm_base *wm_base, uint32_t serial)
{
	xdg_wm_base_pong(wm_base, serial);
}

static const struct xdg_wm_base_listener wm_listener = { .ping = wm_ping };

static void surface_configure(void *data, struct xdg_surface *surface, uint32_t serial)
{
	struct state *state = data;

	xdg_surface_ack_configure(surface, serial);
	state->configured = true;
}

static const struct xdg_surface_listener surface_listener = { .configure = surface_configure };

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel, int32_t w, int32_t h,
			       struct wl_array *states)
{
	struct state *state = data;

	if (w > 0 && h > 0) {
		state->width = w;
		state->height = h;
	}
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
}

static const struct xdg_toplevel_listener toplevel_listener = {
	.configure = toplevel_configure,
	.close = toplevel_close,
};

static void registry_global(void *data, struct wl_registry *registry, uint32_t name,
			    const char *interface, uint32_t version)
{
	struct state *state = data;

	if (!strcmp(interface, wl_compositor_interface.name))
		state->compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
	else if (!strcmp(interface, wl_shm_interface.name))
		state->shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
	else if (!strcmp(interface, xdg_wm_base_interface.name))
		state->wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, 1);
}

static void registry_remove(void *data, struct wl_registry *registry, uint32_t name)
{
}

static const struct wl_registry_listener registry_listener = {
	.global = registry_global,
	.global_remove = registry_remove,
};

int main(void)
{
	struct state state = { .width = 640, .height = 480 };
	struct wl_display *display = wl_display_connect(NULL);
	const char *hold = getenv("HOLD_SECONDS");
	struct wl_shm_pool *pool;
	struct wl_buffer *buffer;
	uint32_t *pixels;
	int fd, x, y, stride, size;
	time_t end;

	if (!display)
		return 1;
	wl_registry_add_listener(wl_display_get_registry(display), &registry_listener, &state);
	wl_display_roundtrip(display);
	if (!state.compositor || !state.shm || !state.wm_base)
		return 1;
	xdg_wm_base_add_listener(state.wm_base, &wm_listener, &state);

	struct wl_surface *surface = wl_compositor_create_surface(state.compositor);
	struct xdg_surface *xdg_surface = xdg_wm_base_get_xdg_surface(state.wm_base, surface);
	struct xdg_toplevel *toplevel = xdg_surface_get_toplevel(xdg_surface);

	xdg_surface_add_listener(xdg_surface, &surface_listener, &state);
	xdg_toplevel_add_listener(toplevel, &toplevel_listener, &state);
	xdg_toplevel_set_title(toplevel, "fullscreen 2D gradient");
	xdg_toplevel_set_fullscreen(toplevel, NULL);
	wl_surface_commit(surface);
	while (!state.configured)
		if (wl_display_dispatch(display) < 0)
			return 1;

	stride = state.width * 4;
	size = stride * state.height;
	fd = memfd_create("gradient", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, size))
		return 1;
	pixels = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (pixels == MAP_FAILED)
		return 1;
	for (y = 0; y < state.height; y++)
		for (x = 0; x < state.width; x++)
			pixels[y * state.width + x] = 0xff000080 |
				(x * 255 / (state.width - 1)) << 16 | (y * 255 / (state.height - 1)) << 8;
	pool = wl_shm_create_pool(state.shm, fd, size);
	buffer = wl_shm_pool_create_buffer(pool, 0, state.width, state.height, stride,
					   WL_SHM_FORMAT_XRGB8888);
	wl_surface_attach(surface, buffer, 0, 0);
	wl_surface_damage(surface, 0, 0, state.width, state.height);
	wl_surface_commit(surface);
	wl_display_roundtrip(display);
	printf("fullscreen %dx%d\n", state.width, state.height);
	fflush(stdout);

	end = time(NULL) + (hold ? atoi(hold) : 10);
	while (time(NULL) < end) {
		wl_display_dispatch_pending(display);
		wl_display_flush(display);
		usleep(100000);
	}
	return 0;
}
