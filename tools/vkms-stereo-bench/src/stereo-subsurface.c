// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * stereo-subsurface: a 2D window with a 3D area, the layout every stereo
 * program uses on the edition's desktop. The window's own surface is a plain
 * blue wl_shm buffer that declares nothing; a subsurface holds a two-view EGL
 * window surface (EGL_EXT_multiview_window), the left view red and the right
 * view green, which the edition's Mesa declares to the compositor as full
 * side by side. In a 3D mode the compositor should show the blue part the
 * same in both eyes, red only in the left eye and green only in the right.
 *
 * NO_STEREO=1 makes the subsurface an ordinary one-view surface (red): the
 * 2D control. HOLD_SECONDS (default 10) is how long it keeps drawing.
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

#define WINDOW_W 320
#define WINDOW_H 200
#define AREA_X 64
#define AREA_Y 48
#define AREA_W 128
#define AREA_H 64

struct client {
	struct wl_compositor *compositor;
	struct wl_subcompositor *subcompositor;
	struct wl_shm *shm;
	struct xdg_wm_base *wm_base;
	bool configured;
};

static void fail(const char *what)
{
	fprintf(stderr, "stereo-subsurface: %s\n", what);
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

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel, int32_t w, int32_t h,
			       struct wl_array *states)
{
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
}

static const struct xdg_toplevel_listener toplevel_listener = {
	.configure = toplevel_configure,
	.close = toplevel_close,
};

static void global(void *data, struct wl_registry *registry, uint32_t name,
		   const char *interface, uint32_t version)
{
	struct client *c = data;

	if (!strcmp(interface, wl_compositor_interface.name))
		c->compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
	else if (!strcmp(interface, wl_subcompositor_interface.name))
		c->subcompositor = wl_registry_bind(registry, name, &wl_subcompositor_interface, 1);
	else if (!strcmp(interface, wl_shm_interface.name))
		c->shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
	else if (!strcmp(interface, xdg_wm_base_interface.name))
		c->wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, 1);
}

static void global_remove(void *data, struct wl_registry *registry, uint32_t name)
{
}

static const struct wl_registry_listener registry_listener = {
	.global = global,
	.global_remove = global_remove,
};

/* The window's 2D part: opaque blue. */
static struct wl_buffer *blue_buffer(struct wl_shm *shm)
{
	int stride = WINDOW_W * 4, size = stride * WINDOW_H, fd, i;
	struct wl_shm_pool *pool;
	struct wl_buffer *buffer;
	uint32_t *pixels;

	fd = memfd_create("window", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, size))
		fail("memfd");
	pixels = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (pixels == MAP_FAILED)
		fail("mmap");
	for (i = 0; i < WINDOW_W * WINDOW_H; i++)
		pixels[i] = 0xff0000ff;
	munmap(pixels, size);
	pool = wl_shm_create_pool(shm, fd, size);
	buffer = wl_shm_pool_create_buffer(pool, 0, WINDOW_W, WINDOW_H, stride, WL_SHM_FORMAT_XRGB8888);
	wl_shm_pool_destroy(pool);
	close(fd);
	return buffer;
}

static void draw(bool stereo)
{
	if (stereo) {
		glDrawBuffer(GL_BACK_LEFT);
		glClearColor(1.0f, 0.0f, 0.0f, 1.0f);
		glClear(GL_COLOR_BUFFER_BIT);
		glDrawBuffer(GL_BACK_RIGHT);
		glClearColor(0.0f, 1.0f, 0.0f, 1.0f);
		glClear(GL_COLOR_BUFFER_BIT);
	} else {
		glDrawBuffer(GL_BACK);
		glClearColor(1.0f, 0.0f, 0.0f, 1.0f);
		glClear(GL_COLOR_BUFFER_BIT);
	}
	glFinish();
}

int main(void)
{
	static const EGLint config_attrs[] = {
		EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
		EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_NONE,
	};
	static const EGLint two_views[] = { EGL_MULTIVIEW_VIEW_COUNT_EXT, 2, EGL_NONE };
	bool stereo = !getenv("NO_STEREO");
	const char *hold = getenv("HOLD_SECONDS");
	struct client c = { 0 };
	struct wl_display *display;
	struct wl_surface *window, *area;
	struct wl_subsurface *subsurface;
	struct xdg_surface *xdg_surface;
	struct xdg_toplevel *toplevel;
	struct wl_egl_window *egl_window;
	EGLDisplay egl;
	EGLConfig config;
	EGLSurface surface;
	EGLContext context;
	EGLint count;
	GLint gl_stereo = 0;
	unsigned int frames = 0;
	time_t end;

	display = wl_display_connect(NULL);
	if (!display)
		fail("no Wayland display");
	wl_registry_add_listener(wl_display_get_registry(display), &registry_listener, &c);
	wl_display_roundtrip(display);
	if (!c.compositor || !c.subcompositor || !c.shm || !c.wm_base)
		fail("missing globals");
	xdg_wm_base_add_listener(c.wm_base, &wm_listener, &c);

	window = wl_compositor_create_surface(c.compositor);
	xdg_surface = xdg_wm_base_get_xdg_surface(c.wm_base, window);
	toplevel = xdg_surface_get_toplevel(xdg_surface);
	xdg_surface_add_listener(xdg_surface, &surface_listener, &c);
	xdg_toplevel_add_listener(toplevel, &toplevel_listener, &c);
	xdg_toplevel_set_title(toplevel, "stereo-subsurface");
	wl_surface_commit(window);
	while (!c.configured)
		if (wl_display_dispatch(display) < 0)
			fail("dispatch");

	area = wl_compositor_create_surface(c.compositor);
	subsurface = wl_subcompositor_get_subsurface(c.subcompositor, area, window);
	wl_subsurface_set_position(subsurface, AREA_X, AREA_Y);
	wl_subsurface_set_desync(subsurface);

	egl_window = wl_egl_window_create(area, AREA_W, AREA_H);
	egl = eglGetPlatformDisplay(EGL_PLATFORM_WAYLAND_KHR, display, NULL);
	if (egl == EGL_NO_DISPLAY || !eglInitialize(egl, NULL, NULL) || !eglBindAPI(EGL_OPENGL_API))
		fail("EGL");
	if (stereo && !strstr(eglQueryString(egl, EGL_EXTENSIONS), "EGL_EXT_multiview_window"))
		fail("no EGL_EXT_multiview_window");
	if (!eglChooseConfig(egl, config_attrs, &config, 1, &count) || count != 1)
		fail("EGL config");
	surface = eglCreateWindowSurface(egl, config, (EGLNativeWindowType)egl_window,
					 stereo ? two_views : NULL);
	context = eglCreateContext(egl, config, EGL_NO_CONTEXT, NULL);
	if (surface == EGL_NO_SURFACE || context == EGL_NO_CONTEXT ||
	    !eglMakeCurrent(egl, surface, surface, context))
		fail("EGL surface");
	glGetIntegerv(GL_STEREO, &gl_stereo);
	if (!gl_stereo != !stereo)
		fail("GL_STEREO does not match the surface");

	draw(stereo);
	eglSwapBuffers(egl, surface);
	wl_surface_attach(window, blue_buffer(c.shm), 0, 0);
	wl_surface_damage(window, 0, 0, WINDOW_W, WINDOW_H);
	wl_surface_commit(window);
	wl_display_roundtrip(display);
	printf("window %dx%d, 3D area %dx%d at %d,%d, stereo %d\n", WINDOW_W, WINDOW_H, AREA_W,
	       AREA_H, AREA_X, AREA_Y, gl_stereo);
	fflush(stdout);

	end = time(NULL) + (hold ? atoi(hold) : 10);
	while (time(NULL) < end) {
		draw(stereo);
		eglSwapBuffers(egl, surface);
		wl_display_dispatch_pending(display);
		frames++;
	}
	printf("frames %u\n", frames);
	return 0;
}
