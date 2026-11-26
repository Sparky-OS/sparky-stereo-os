// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * glasses-sbs: a full-screen Wayland window declared full side by side, two address-coded eyes in one wl_shm
 * buffer twice the window's width (Stereo KWin's form: the window is one eye wide, the buffer holds both eyes, left
 * first). Every sample says its eye and its place in that eye, so a capture of the scanned-out frame can be read
 * sample by sample: R = x & 0xff, G = y & 0xff, B = eye << 7 | ((y >> 8) & 7) << 4 | ((x >> 8) & 15), eye 0 left, 1 right.
 * Each eye is drawn at the size the compositor gives the window (one eye), never resized.
 * NO_STEREO=1 declares nothing and draws the left eye alone in a buffer of the window's size: the 2D control.
 * HOLD_SECONDS (default 30) is how long it stays. Prints "configured WxH" and "committed BWxBH declared D".
 * Written for queue row 132 after lane 233's glasses-sbs.c (removed with its scratch), on the bench's fullscreen-2d.c.
 */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>
#include <wayland-client.h>
#include <stereo-declare.h>
#include "xdg-shell-client-protocol.h"

static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct xdg_wm_base *wm_base;
static int width, height, configured;

static void registry_global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
	(void)data;
	if (!strcmp(interface, wl_compositor_interface.name))
		compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
	else if (!strcmp(interface, wl_shm_interface.name))
		shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
	else if (!strcmp(interface, xdg_wm_base_interface.name))
		wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, version < 2 ? version : 2);
}

static void registry_remove(void *data, struct wl_registry *registry, uint32_t name)
{
	(void)data; (void)registry; (void)name;
}

static const struct wl_registry_listener registry_listener = {registry_global, registry_remove};

static void wm_ping(void *data, struct xdg_wm_base *base, uint32_t serial)
{
	(void)data;
	xdg_wm_base_pong(base, serial);
}

static const struct xdg_wm_base_listener wm_listener = {wm_ping};

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel, int32_t w, int32_t h, struct wl_array *states)
{
	(void)data; (void)toplevel; (void)states;
	if (w > 0 && h > 0) {
		width = w;
		height = h;
	}
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
	(void)data; (void)toplevel;
}

static const struct xdg_toplevel_listener toplevel_listener = {toplevel_configure, toplevel_close};

static void surface_configure(void *data, struct xdg_surface *surface, uint32_t serial)
{
	(void)data;
	xdg_surface_ack_configure(surface, serial);
	configured = 1;
}

static const struct xdg_surface_listener surface_listener = {surface_configure};

static uint32_t sample(int eye, int x, int y)
{
	const uint32_t r = x & 0xff, g = y & 0xff;
	const uint32_t b = (uint32_t)eye << 7 | (uint32_t)((y >> 8) & 7) << 4 | (uint32_t)((x >> 8) & 15);
	return 0xff000000u | r << 16 | g << 8 | b;
}

int main(void)
{
	const int stereo = !getenv("NO_STEREO");
	const int hold = getenv("HOLD_SECONDS") ? atoi(getenv("HOLD_SECONDS")) : 30;
	struct wl_display *display = wl_display_connect(NULL);
	if (!display) {
		fprintf(stderr, "no Wayland display\n");
		return 1;
	}
	struct wl_registry *registry = wl_display_get_registry(display);
	wl_registry_add_listener(registry, &registry_listener, NULL);
	wl_display_roundtrip(display);
	if (!compositor || !shm || !wm_base) {
		fprintf(stderr, "missing wl_compositor, wl_shm or xdg_wm_base\n");
		return 1;
	}
	xdg_wm_base_add_listener(wm_base, &wm_listener, NULL);
	if (stereo && stereo_declare_wayland_init(display, NULL) != 0) {
		fprintf(stderr, "stereo_declare_wayland_init failed\n");
		return 1;
	}
	/* the library binds the compositor's declaration global on this roundtrip (its API.md example does the same) */
	wl_display_roundtrip(display);
	if (stereo && !stereo_supported_wayland()) {
		fprintf(stderr, "the compositor offers no stereo declaration\n");
		return 1;
	}
	struct wl_surface *surface = wl_compositor_create_surface(compositor);
	struct xdg_surface *xsurface = xdg_wm_base_get_xdg_surface(wm_base, surface);
	xdg_surface_add_listener(xsurface, &surface_listener, NULL);
	struct xdg_toplevel *toplevel = xdg_surface_get_toplevel(xsurface);
	xdg_toplevel_add_listener(toplevel, &toplevel_listener, NULL);
	xdg_toplevel_set_title(toplevel, "glasses-sbs");
	xdg_toplevel_set_fullscreen(toplevel, NULL);
	int declared = 0;
	if (stereo) {
		declared = stereo_declare_wayland(surface, STEREO_SBS_FULL, STEREO_CLASS_GAME, STEREO_GAME_3D) == 0;
	}
	wl_surface_commit(surface);
	while (!configured && wl_display_dispatch(display) != -1) {
	}
	if (width <= 0 || height <= 0) {
		fprintf(stderr, "the compositor gave no size\n");
		return 1;
	}
	printf("configured %dx%d\n", width, height);
	const int views = stereo ? 2 : 1;
	const int bw = width * views, bh = height, stride = bw * 4;
	const size_t size = (size_t)stride * bh;
	int fd = memfd_create("glasses-sbs", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, size) != 0) {
		perror("memfd");
		return 1;
	}
	uint32_t *pixels = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (pixels == MAP_FAILED) {
		perror("mmap");
		return 1;
	}
	for (int y = 0; y < bh; y++) {
		for (int x = 0; x < bw; x++) {
			const int eye = x / width;
			pixels[y * bw + x] = sample(eye, x - eye * width, y);
		}
	}
	struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, size);
	struct wl_buffer *buffer = wl_shm_pool_create_buffer(pool, 0, bw, bh, stride, WL_SHM_FORMAT_XRGB8888);
	wl_surface_attach(surface, buffer, 0, 0);
	wl_surface_damage_buffer(surface, 0, 0, bw, bh);
	wl_surface_commit(surface);
	wl_display_roundtrip(display);
	printf("committed %dx%d declared %d supported %u\n", bw, bh, declared, stereo ? stereo_supported_wayland() : 0);
	fflush(stdout);
	const time_t end = time(NULL) + hold;
	while (time(NULL) < end) {
		wl_display_dispatch_pending(display);
		wl_display_flush(display);
		usleep(100000);
	}
	if (stereo) {
		stereo_declare_wayland_finish();
	}
	wl_display_disconnect(display);
	return 0;
}
