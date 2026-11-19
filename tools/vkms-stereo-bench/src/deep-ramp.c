// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * deep-ramp: a client whose picture is a narrow grey ramp in 16 bits per channel, so that a deep readback of the
 * output (drm-grab with DRM_GRAB_DEEP=1) can count the levels that survive the path. The ramp is the 256 values
 * BASE .. BASE+255 of a 16-bit channel (1/256 of the range): 1 level at 8 bits, 4 at 10 bits, 256 at 16 bits.
 *
 *   MODE=shm     (default) a fullscreen wl_shm window in the 16-bit format RAMP_FORMAT (ab48, xb48, ar30, xr30 or
 *                auto: the first deep format the compositor advertises); every column of the window is one value of
 *                the ramp, BASE 0x8000. The compositor shows it the same in both eyes.
 *   MODE=stereo  a window with a 3D area (EGL_EXT_multiview_window, as stereo-subsurface) in a 16 bit EGL config
 *                (fixed point first): the left view holds the ramp from 0x8000, the right view the ramp from 0x9000,
 *                so the eyes can be told apart. NO_STEREO=1 makes it a one-view surface (the 2D control).
 *
 * Prints the formats the compositor advertises ("formats:" line), the format or config used and the number of values
 * drawn. HOLD_SECONDS (default 10) is how long it keeps the picture.
 */
#define _GNU_SOURCE
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GL/gl.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include <wayland-client.h>
#include <wayland-egl.h>
#include "xdg-shell-client-protocol.h"

#ifndef EGL_MULTIVIEW_VIEW_COUNT_EXT
#define EGL_MULTIVIEW_VIEW_COUNT_EXT 0x3134
#endif
#ifndef EGL_COLOR_COMPONENT_TYPE_EXT
#define EGL_COLOR_COMPONENT_TYPE_EXT 0x3339
#define EGL_COLOR_COMPONENT_TYPE_FIXED_EXT 0x333A
#define EGL_COLOR_COMPONENT_TYPE_FLOAT_EXT 0x333B
#endif
#ifndef GL_BACK_LEFT
#define GL_BACK_LEFT 0x0402
#define GL_BACK_RIGHT 0x0403
#endif

#define FMT_ABGR16161616 0x38344241u
#define FMT_XBGR16161616 0x38344258u
#define FMT_ARGB2101010 0x30335241u
#define FMT_XRGB2101010 0x30335258u

struct client {
	struct wl_compositor *compositor;
	struct wl_subcompositor *subcompositor;
	struct wl_shm *shm;
	struct xdg_wm_base *wm_base;
	bool configured;
	int width, height;
	uint32_t formats[32];
	int nformats;
};

static void fail(const char *what)
{
	fprintf(stderr, "deep-ramp: %s\n", what);
	exit(1);
}

static void wm_ping(void *data, struct xdg_wm_base *wm_base, uint32_t serial)
{
	xdg_wm_base_pong(wm_base, serial);
}

static const struct xdg_wm_base_listener wm_listener = { .ping = wm_ping };

static void surface_configure(void *data, struct xdg_surface *surface, uint32_t serial)
{
	struct client *c = data;

	xdg_surface_ack_configure(surface, serial);
	c->configured = true;
}

static const struct xdg_surface_listener surface_listener = { .configure = surface_configure };

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel, int32_t w, int32_t h, struct wl_array *states)
{
	struct client *c = data;

	if (w > 0 && h > 0) {
		c->width = w;
		c->height = h;
	}
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
}

static const struct xdg_toplevel_listener toplevel_listener = {
	.configure = toplevel_configure,
	.close = toplevel_close,
};

static void shm_format(void *data, struct wl_shm *shm, uint32_t format)
{
	struct client *c = data;

	if (c->nformats < 32)
		c->formats[c->nformats++] = format;
}

static const struct wl_shm_listener shm_listener = { .format = shm_format };

static void registry_global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
	struct client *c = data;

	if (!strcmp(interface, wl_compositor_interface.name))
		c->compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
	else if (!strcmp(interface, wl_subcompositor_interface.name))
		c->subcompositor = wl_registry_bind(registry, name, &wl_subcompositor_interface, 1);
	else if (!strcmp(interface, wl_shm_interface.name)) {
		c->shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
		wl_shm_add_listener(c->shm, &shm_listener, c);
	} else if (!strcmp(interface, xdg_wm_base_interface.name))
		c->wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, 1);
}

static void registry_remove(void *data, struct wl_registry *registry, uint32_t name)
{
}

static const struct wl_registry_listener registry_listener = {
	.global = registry_global,
	.global_remove = registry_remove,
};

static bool has_format(const struct client *c, uint32_t f)
{
	for (int i = 0; i < c->nformats; i++)
		if (c->formats[i] == f)
			return true;
	return false;
}

static void hold_loop(struct wl_display *display, int seconds)
{
	time_t end = time(NULL) + seconds;

	while (time(NULL) < end) {
		wl_display_dispatch_pending(display);
		wl_display_flush(display);
		usleep(100000);
	}
}

/* the wl_shm window: the columns are the 256 values of the ramp */
static int run_shm(struct client *c, struct wl_display *display, struct wl_surface *surface, int hold)
{
	const char *want = getenv("RAMP_FORMAT");
	uint32_t format = 0;
	int bits = 8;

	if (!want || !strcmp(want, "auto")) {
		if (has_format(c, FMT_ABGR16161616))
			want = "ab48";
		else if (has_format(c, FMT_XBGR16161616))
			want = "xb48";
		else if (has_format(c, FMT_ARGB2101010))
			want = "ar30";
		else if (has_format(c, FMT_XRGB2101010))
			want = "xr30";
		else
			want = "xr24";
	}
	if (!strcmp(want, "ab48")) { format = FMT_ABGR16161616; bits = 16; }
	else if (!strcmp(want, "xb48")) { format = FMT_XBGR16161616; bits = 16; }
	else if (!strcmp(want, "ar30")) { format = FMT_ARGB2101010; bits = 10; }
	else if (!strcmp(want, "xr30")) { format = FMT_XRGB2101010; bits = 10; }
	else { format = WL_SHM_FORMAT_XRGB8888; bits = 8; }
	if (format != WL_SHM_FORMAT_XRGB8888 && !has_format(c, format)) {
		printf("format %s not advertised\n", want);
		return 3;
	}
	int bpp = bits == 16 ? 8 : 4;
	int stride = c->width * bpp, size = stride * c->height;
	int fd = memfd_create("ramp", MFD_CLOEXEC);

	if (fd < 0 || ftruncate(fd, size))
		fail("memfd");
	uint8_t *px = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

	if (px == MAP_FAILED)
		fail("mmap");
	for (int y = 0; y < c->height; y++) {
		for (int x = 0; x < c->width; x++) {
			uint32_t v16 = 0x8000 + (uint32_t)((uint64_t)x * 256 / c->width);
			uint8_t *p = px + (size_t)y * stride + (size_t)x * bpp;

			if (bits == 16) {
				uint64_t q = (uint64_t)0xffff << 48 | (uint64_t)v16 << 32 | (uint64_t)v16 << 16 | v16;
				memcpy(p, &q, 8);
			} else if (bits == 10) {
				uint32_t v = v16 >> 6;
				uint32_t q = (format == FMT_ARGB2101010 ? 3u << 30 : 0) | v << 20 | v << 10 | v;
				memcpy(p, &q, 4);
			} else {
				uint32_t v = v16 >> 8;
				uint32_t q = 0xff000000u | v << 16 | v << 8 | v;
				memcpy(p, &q, 4);
			}
		}
	}
	struct wl_shm_pool *pool = wl_shm_create_pool(c->shm, fd, size);
	struct wl_buffer *buffer = wl_shm_pool_create_buffer(pool, 0, c->width, c->height, stride, format);

	wl_surface_attach(surface, buffer, 0, 0);
	wl_surface_damage(surface, 0, 0, c->width, c->height);
	wl_surface_commit(surface);
	wl_display_roundtrip(display);
	printf("shm %dx%d format %s (%d bits), ramp 0x8000..0x80ff\n", c->width, c->height, want, bits);
	fflush(stdout);
	hold_loop(display, hold);
	return 0;
}

#define AREA_X 64
#define AREA_Y 48
#define AREA_W 1024
#define AREA_H 256

static void draw_ramp(uint32_t base)
{
	glEnable(GL_SCISSOR_TEST);
	for (int i = 0; i < 256; i++) {
		float v = (float)(base + i) / 65535.0f;

		glScissor(i * (AREA_W / 256), 0, AREA_W / 256, AREA_H);
		glClearColor(v, v, v, 1.0f);
		glClear(GL_COLOR_BUFFER_BIT);
	}
	glDisable(GL_SCISSOR_TEST);
}

static void draw(bool stereo)
{
	if (stereo) {
		glDrawBuffer(GL_BACK_LEFT);
		draw_ramp(0x8000);
		glDrawBuffer(GL_BACK_RIGHT);
		draw_ramp(0x9000);
	} else {
		glDrawBuffer(GL_BACK);
		draw_ramp(0x8000);
	}
	glFinish();
}

static struct wl_buffer *plain_buffer(struct wl_shm *shm, int w, int h)
{
	int stride = w * 4, size = stride * h;
	int fd = memfd_create("window", MFD_CLOEXEC);

	if (fd < 0 || ftruncate(fd, size))
		fail("memfd");
	uint32_t *px = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

	if (px == MAP_FAILED)
		fail("mmap");
	for (int i = 0; i < w * h; i++)
		px[i] = 0xff000040;
	return wl_shm_pool_create_buffer(wl_shm_create_pool(shm, fd, size), 0, w, h, stride, WL_SHM_FORMAT_XRGB8888);
}

/* a 3D area: the EGL config with 16 bits per channel (fixed point first) and, for the pair, two views */
static int run_stereo(struct client *c, struct wl_display *display, struct wl_surface *window, int hold)
{
	static const EGLint two_views[] = { EGL_MULTIVIEW_VIEW_COUNT_EXT, 2, EGL_NONE };
	bool stereo = !getenv("NO_STEREO");
	EGLDisplay egl;
	EGLConfig configs[256], config = NULL;
	EGLint count = 0, type = 0, fixed_found = 0, float_found = 0;
	GLint gl_stereo = 0;
	static const EGLint attrs[] = {
		EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
		EGL_RED_SIZE, 16, EGL_GREEN_SIZE, 16, EGL_BLUE_SIZE, 16, EGL_NONE,
	};
	struct wl_surface *area = wl_compositor_create_surface(c->compositor);
	struct wl_subsurface *sub = wl_subcompositor_get_subsurface(c->subcompositor, area, window);
	struct wl_egl_window *egl_window;
	EGLSurface surface;
	EGLContext context;

	wl_subsurface_set_position(sub, AREA_X, AREA_Y);
	wl_subsurface_set_desync(sub);
	egl_window = wl_egl_window_create(area, AREA_W, AREA_H);
	egl = eglGetPlatformDisplay(EGL_PLATFORM_WAYLAND_KHR, display, NULL);
	if (egl == EGL_NO_DISPLAY || !eglInitialize(egl, NULL, NULL) || !eglBindAPI(EGL_OPENGL_API))
		fail("EGL");
	if (stereo && !strstr(eglQueryString(egl, EGL_EXTENSIONS), "EGL_EXT_multiview_window"))
		fail("no EGL_EXT_multiview_window");
	if (!eglChooseConfig(egl, attrs, configs, 256, &count) || count < 1) {
		printf("no EGL window config with 16 bits per channel\n");
		return 3;
	}
	for (int i = 0; i < count; i++) {
		eglGetConfigAttrib(egl, configs[i], EGL_COLOR_COMPONENT_TYPE_EXT, &type);
		if (type == EGL_COLOR_COMPONENT_TYPE_FIXED_EXT && !fixed_found) {
			fixed_found = 1;
			config = configs[i];
		} else if (type == EGL_COLOR_COMPONENT_TYPE_FLOAT_EXT) {
			float_found = 1;
		}
	}
	printf("EGL configs with 16 bits: %d, fixed point %s, floating point %s\n", count, fixed_found ? "yes" : "no",
	       float_found ? "yes" : "no");
	if (!config) {
		printf("no fixed point 16 bit EGL config (the ramp needs one: a half float holds 2048 values per octave)\n");
		return 3;
	}
	surface = eglCreateWindowSurface(egl, config, (EGLNativeWindowType)egl_window, stereo ? two_views : NULL);
	context = eglCreateContext(egl, config, EGL_NO_CONTEXT, NULL);
	if (surface == EGL_NO_SURFACE || context == EGL_NO_CONTEXT || !eglMakeCurrent(egl, surface, surface, context))
		fail("EGL surface");
	glGetIntegerv(GL_STEREO, &gl_stereo);
	if (!gl_stereo != !stereo)
		fail("GL_STEREO does not match the surface");
	draw(stereo);
	eglSwapBuffers(egl, surface);
	wl_surface_attach(window, plain_buffer(c->shm, AREA_X * 2 + AREA_W, AREA_Y * 2 + AREA_H), 0, 0);
	wl_surface_damage(window, 0, 0, AREA_X * 2 + AREA_W, AREA_Y * 2 + AREA_H);
	wl_surface_commit(window);
	wl_display_roundtrip(display);
	printf("stereo window %dx%d, 3D area %dx%d at %d,%d, stereo %d, left ramp 0x8000..0x80ff, right ramp 0x9000..0x90ff\n",
	       AREA_X * 2 + AREA_W, AREA_Y * 2 + AREA_H, AREA_W, AREA_H, AREA_X, AREA_Y, gl_stereo);
	fflush(stdout);
	time_t end = time(NULL) + hold;

	while (time(NULL) < end) {
		draw(stereo);
		eglSwapBuffers(egl, surface);
		wl_display_dispatch_pending(display);
	}
	return 0;
}

int main(void)
{
	const char *mode = getenv("MODE");
	const char *h = getenv("HOLD_SECONDS");
	int hold = h ? atoi(h) : 10;
	bool stereo_mode = mode && !strcmp(mode, "stereo");
	struct client c = { .width = 640, .height = 480 };
	struct wl_display *display = wl_display_connect(NULL);

	if (!display)
		fail("no Wayland display");
	wl_registry_add_listener(wl_display_get_registry(display), &registry_listener, &c);
	wl_display_roundtrip(display);
	wl_display_roundtrip(display);
	if (!c.compositor || !c.shm || !c.wm_base || (stereo_mode && !c.subcompositor))
		fail("missing globals");
	printf("formats:");
	for (int i = 0; i < c.nformats; i++)
		if (c.formats[i] < 2)
			printf(" %s", c.formats[i] ? "XR24" : "AR24");
		else
			printf(" %.4s", (char *)&c.formats[i]);
	printf("\n");
	xdg_wm_base_add_listener(c.wm_base, &wm_listener, &c);
	struct wl_surface *surface = wl_compositor_create_surface(c.compositor);
	struct xdg_surface *xs = xdg_wm_base_get_xdg_surface(c.wm_base, surface);
	struct xdg_toplevel *top = xdg_surface_get_toplevel(xs);

	xdg_surface_add_listener(xs, &surface_listener, &c);
	xdg_toplevel_add_listener(top, &toplevel_listener, &c);
	xdg_toplevel_set_title(top, "deep ramp");
	if (!stereo_mode)
		xdg_toplevel_set_fullscreen(top, NULL);
	wl_surface_commit(surface);
	while (!c.configured)
		if (wl_display_dispatch(display) < 0)
			fail("dispatch");
	return stereo_mode ? run_stereo(&c, display, surface, hold) : run_shm(&c, display, surface, hold);
}
