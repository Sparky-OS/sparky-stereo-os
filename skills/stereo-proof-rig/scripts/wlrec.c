/* SPDX-License-Identifier: MIT */
/*
 * wlrec: record what a Wayland client hands the compositor on its declared stereo
 * surfaces.  Preloaded into the client (LD_PRELOAD=wlrec.so), it follows the requests
 * the client marshals through libwayland-client (wl_shm pools and buffers, wl_surface
 * attach and commit, wp_viewport destinations, wl_subsurface positions and the
 * kde_stereo_content_v1 declarations) and, on each commit of a surface declared full
 * side by side, writes the attached shared-memory buffer as it is to
 * $WLREC_DIR/<pid>-<n>.raw with one JSON line per commit in $WLREC_DIR/log.jsonl:
 * the buffer's size, stride and format, the viewport destination and the position.
 * $WLREC_MAX (default 8) bounds the dumps per process.
 *
 * A surface drawn with EGL (wl_egl_window_create(), eglCreate[Platform]WindowSurface()) is read back
 * from its back buffer at eglSwapBuffers() when it is declared, as RGBA rows from the bottom up
 * ("format":"rgba-bottom-up").
 *
 * Each buffer keeps its own copy of its pool's file descriptor.  Nothing is changed: every request goes on to libwayland-client as the client made it.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client-core.h>
#include <wayland-util.h>
struct wl_surface;
struct wl_egl_window;
#include <EGL/egl.h>
#include <GLES2/gl2.h>

#define MAX_OBJECTS 4096

enum kind { K_NONE, K_POOL, K_BUFFER, K_SURFACE, K_VIEWPORT, K_SUBSURFACE, K_STEREO };

struct object {
	struct wl_proxy *proxy;
	enum kind kind;
	int fd;              /* pool */
	int32_t size;        /* pool */
	struct object *pool; /* buffer */
	int32_t offset, width, height, stride;
	uint32_t format;
	struct object *surface;  /* viewport, subsurface, stereo */
	struct object *attached; /* surface */
	int32_t dest_w, dest_h;  /* surface, from its viewport */
	int32_t pos_x, pos_y;    /* surface, from its subsurface */
	uint32_t content;        /* surface */
};

static struct object objects[MAX_OBJECTS];
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static int dumps;

static struct object *find(struct wl_proxy *proxy)
{
	for (int i = 0; i < MAX_OBJECTS; i++)
		if (objects[i].proxy == proxy && objects[i].kind != K_NONE)
			return &objects[i];
	return NULL;
}

static struct object *add(struct wl_proxy *proxy, enum kind kind)
{
	struct object *o = find(proxy);
	if (o)
		return o;
	for (int i = 0; i < MAX_OBJECTS; i++) {
		if (objects[i].kind == K_NONE) {
			memset(&objects[i], 0, sizeof(objects[i]));
			objects[i].proxy = proxy;
			objects[i].kind = kind;
			objects[i].fd = -1;
			return &objects[i];
		}
	}
	return NULL;
}

/* The arguments of a request, read with its signature (wayland's own grammar). */
static int parse_args(const char *signature, va_list ap, union wl_argument *args)
{
	int n = 0;
	for (const char *s = signature; *s; s++) {
		switch (*s) {
		case 'i': args[n++].i = va_arg(ap, int32_t); break;
		case 'u': args[n++].u = va_arg(ap, uint32_t); break;
		case 'f': args[n++].f = va_arg(ap, wl_fixed_t); break;
		case 's': args[n++].s = va_arg(ap, const char *); break;
		case 'o': args[n++].o = va_arg(ap, struct wl_object *); break;
		case 'n': args[n++].o = va_arg(ap, struct wl_object *); break;
		case 'a': args[n++].a = va_arg(ap, struct wl_array *); break;
		case 'h': args[n++].h = va_arg(ap, int32_t); break;
		default: break; /* '?' and the version digits */
		}
	}
	return n;
}

static void dump(struct object *surface)
{
	struct object *buffer = surface->attached;
	const char *dir = getenv("WLREC_DIR");
	const char *max = getenv("WLREC_MAX");
	if (!dir || !buffer || buffer->kind != K_BUFFER || buffer->fd < 0)
		return;
	if (dumps >= (max ? atoi(max) : 8))
		return;
	size_t length = (size_t)buffer->offset + (size_t)buffer->stride * buffer->height;
	void *map = mmap(NULL, length, PROT_READ, MAP_SHARED, buffer->fd, 0);
	if (map == MAP_FAILED)
		return;
	char path[4096];
	snprintf(path, sizeof(path), "%s/%d-%d.raw", dir, (int)getpid(), dumps);
	FILE *f = fopen(path, "wb");
	if (f) {
		fwrite((char *)map + buffer->offset, 1, (size_t)buffer->stride * buffer->height, f);
		fclose(f);
	}
	munmap(map, length);
	snprintf(path, sizeof(path), "%s/log.jsonl", dir);
	f = fopen(path, "a");
	if (f) {
		fprintf(f, "{\"pid\":%d,\"n\":%d,\"file\":\"%d-%d.raw\",\"width\":%d,\"height\":%d,\"stride\":%d,"
			   "\"format\":%u,\"content\":%u,\"destination\":[%d,%d],\"position\":[%d,%d]}\n",
			(int)getpid(), dumps, (int)getpid(), dumps, buffer->width, buffer->height, buffer->stride,
			buffer->format, surface->content, surface->dest_w, surface->dest_h, surface->pos_x, surface->pos_y);
		fclose(f);
	}
	dumps++;
}

static void track(const char *name, struct wl_proxy *proxy, uint32_t opcode, struct wl_proxy *made, const union wl_argument *args)
{
	struct object *o;
	if (!strcmp(name, "wl_shm") && opcode == 0 && made) {          /* create_pool(n, h fd, i size) */
		o = add(made, K_POOL);
		if (o) {
			o->fd = fcntl(args[1].h, F_DUPFD_CLOEXEC, 0);
			o->size = args[2].i;
		}
	} else if (!strcmp(name, "wl_shm_pool") && opcode == 0 && made) { /* create_buffer */
		o = add(made, K_BUFFER);
		if (o) {
			o->pool = find(proxy);
			/* a client may destroy the pool as soon as the buffer exists */
			o->fd = o->pool && o->pool->fd >= 0 ? fcntl(o->pool->fd, F_DUPFD_CLOEXEC, 0) : -1;
			o->offset = args[1].i;
			o->width = args[2].i;
			o->height = args[3].i;
			o->stride = args[4].i;
			o->format = args[5].u;
		}
	} else if (!strcmp(name, "wl_shm_pool") && opcode == 2) {        /* resize */
		if ((o = find(proxy)))
			o->size = args[0].i;
	} else if (!strcmp(name, "wl_compositor") && opcode == 0 && made) {
		add(made, K_SURFACE);
	} else if (!strcmp(name, "wl_surface") && opcode == 1) {         /* attach(o buffer, i, i) */
		struct object *s = add(proxy, K_SURFACE);
		if (s)
			s->attached = args[0].o ? find((struct wl_proxy *)args[0].o) : NULL;
	} else if (!strcmp(name, "wl_surface") && opcode == 6) {         /* commit */
		struct object *s = find(proxy);
		if (s && s->content == 3)
			dump(s);
	} else if (!strcmp(name, "wp_viewporter") && opcode == 1 && made) { /* get_viewport(n, o) */
		o = add(made, K_VIEWPORT);
		if (o)
			o->surface = add((struct wl_proxy *)args[1].o, K_SURFACE);
	} else if (!strcmp(name, "wp_viewport") && opcode == 2) {        /* set_destination(i, i) */
		if ((o = find(proxy)) && o->surface) {
			o->surface->dest_w = args[0].i;
			o->surface->dest_h = args[1].i;
		}
	} else if (!strcmp(name, "wl_subcompositor") && opcode == 1 && made) { /* get_subsurface(n, o, o) */
		o = add(made, K_SUBSURFACE);
		if (o)
			o->surface = add((struct wl_proxy *)args[1].o, K_SURFACE);
	} else if (!strcmp(name, "wl_subsurface") && opcode == 1) {      /* set_position(i, i) */
		if ((o = find(proxy)) && o->surface) {
			o->surface->pos_x = args[0].i;
			o->surface->pos_y = args[1].i;
		}
	} else if (!strcmp(name, "kde_stereo_content_manager_v1") && opcode == 1 && made) {
		o = add(made, K_STEREO);
		if (o)
			o->surface = add((struct wl_proxy *)args[1].o, K_SURFACE);
	} else if (!strcmp(name, "kde_stereo_content_v1") && opcode == 1) { /* set_content(u) */
		if ((o = find(proxy)) && o->surface)
			o->surface->content = args[0].u;
	} else if (!strcmp(name, "kde_stereo_content_v1") && opcode == 0) { /* destroy */
		if ((o = find(proxy)) && o->surface)
			o->surface->content = 0;
	}
}



/* The next definition of a wrapped function: after this library, or, for a library a plugin
 * loaded with dlopen() outside the global scope, in that library */
static void *next_symbol(const char *name, const char *library)
{
	void *found = dlsym(RTLD_NEXT, name);
	if (!found) {
		void *handle = dlopen(library, RTLD_NOW | RTLD_NOLOAD);
		if (handle)
			found = dlsym(handle, name);
	}
	return found;
}

/* EGL: wl_egl_window -> wl_surface, EGLSurface -> wl_egl_window */
#define MAX_EGL 64
static struct {
	void *egl_window;
	struct wl_proxy *surface;
	EGLSurface egl_surface;
} egl_windows[MAX_EGL];

struct wl_egl_window *wl_egl_window_create(struct wl_surface *surface, int width, int height)
{
	static struct wl_egl_window *(*real)(struct wl_surface *, int, int);
	if (!real)
		real = next_symbol("wl_egl_window_create", "libwayland-egl.so.1");
	struct wl_egl_window *window = real(surface, width, height);
	pthread_mutex_lock(&lock);
	for (int i = 0; i < MAX_EGL; i++) {
		if (!egl_windows[i].egl_window) {
			egl_windows[i].egl_window = window;
			egl_windows[i].surface = (struct wl_proxy *)surface;
			egl_windows[i].egl_surface = EGL_NO_SURFACE;
			break;
		}
	}
	pthread_mutex_unlock(&lock);
	return window;
}

static void egl_surface_made(void *native, EGLSurface made)
{
	pthread_mutex_lock(&lock);
	for (int i = 0; i < MAX_EGL; i++)
		if (egl_windows[i].egl_window == native)
			egl_windows[i].egl_surface = made;
	pthread_mutex_unlock(&lock);
}

EGLSurface eglCreateWindowSurface(EGLDisplay dpy, EGLConfig config, EGLNativeWindowType win, const EGLint *attrib_list)
{
	static EGLSurface (*real)(EGLDisplay, EGLConfig, EGLNativeWindowType, const EGLint *);
	if (!real)
		real = next_symbol("eglCreateWindowSurface", "libEGL.so.1");
	EGLSurface made = real(dpy, config, win, attrib_list);
	egl_surface_made((void *)win, made);
	return made;
}

EGLSurface eglCreatePlatformWindowSurface(EGLDisplay dpy, EGLConfig config, void *native, const EGLAttrib *attrib_list)
{
	static EGLSurface (*real)(EGLDisplay, EGLConfig, void *, const EGLAttrib *);
	if (!real)
		real = next_symbol("eglCreatePlatformWindowSurface", "libEGL.so.1");
	EGLSurface made = real(dpy, config, native, attrib_list);
	egl_surface_made(native, made);
	return made;
}

/* an extension's entry point: libEGL need not export it, eglGetProcAddress() gives it */
static EGLSurface (*real_platform_ext)(EGLDisplay, EGLConfig, void *, const EGLint *);
EGLSurface eglCreatePlatformWindowSurfaceEXT(EGLDisplay dpy, EGLConfig config, void *native, const EGLint *attrib_list)
{
	EGLSurface (*real)(EGLDisplay, EGLConfig, void *, const EGLint *) = real_platform_ext;
	if (!real)
		real = real_platform_ext = next_symbol("eglCreatePlatformWindowSurfaceEXT", "libEGL.so.1");
	EGLSurface made = real(dpy, config, native, attrib_list);
	egl_surface_made(native, made);
	return made;
}

static void dump_egl(EGLDisplay dpy, EGLSurface surface)
{
	const char *dir = getenv("WLREC_DIR");
	const char *max = getenv("WLREC_MAX");
	struct object *s = NULL;
	pthread_mutex_lock(&lock);
	for (int i = 0; i < MAX_EGL; i++)
		if (egl_windows[i].egl_window && egl_windows[i].egl_surface == surface)
			s = find(egl_windows[i].surface);
	int declared = s && s->content == 3;
	int32_t dest_w = s ? s->dest_w : 0, dest_h = s ? s->dest_h : 0, pos_x = s ? s->pos_x : 0, pos_y = s ? s->pos_y : 0;
	pthread_mutex_unlock(&lock);
	if (!dir || !declared || dumps >= (max ? atoi(max) : 8))
		return;
	EGLint w = 0, h = 0;
	eglQuerySurface(dpy, surface, EGL_WIDTH, &w);
	eglQuerySurface(dpy, surface, EGL_HEIGHT, &h);
	void (*readPixels)(GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, void *) = (void *)eglGetProcAddress("glReadPixels");
	void (*pixelStore)(GLenum, GLint) = (void *)eglGetProcAddress("glPixelStorei");
	if (w <= 0 || h <= 0 || !readPixels)
		return;
	unsigned char *pixels = malloc((size_t)w * h * 4);
	if (!pixels)
		return;
	if (pixelStore)
		pixelStore(GL_PACK_ALIGNMENT, 1);
	readPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
	char path[4096];
	snprintf(path, sizeof(path), "%s/%d-%d.raw", dir, (int)getpid(), dumps);
	FILE *f = fopen(path, "wb");
	if (f) {
		fwrite(pixels, 1, (size_t)w * h * 4, f);
		fclose(f);
	}
	free(pixels);
	snprintf(path, sizeof(path), "%s/log.jsonl", dir);
	f = fopen(path, "a");
	if (f) {
		fprintf(f, "{\"pid\":%d,\"n\":%d,\"file\":\"%d-%d.raw\",\"width\":%d,\"height\":%d,\"stride\":%d,"
			   "\"format\":\"rgba-bottom-up\",\"content\":3,\"destination\":[%d,%d],\"position\":[%d,%d]}\n",
			(int)getpid(), dumps, (int)getpid(), dumps, w, h, w * 4, dest_w, dest_h, pos_x, pos_y);
		fclose(f);
	}
	dumps++;
}

EGLBoolean eglSwapBuffers(EGLDisplay dpy, EGLSurface surface)
{
	static EGLBoolean (*real)(EGLDisplay, EGLSurface);
	if (!real)
		real = next_symbol("eglSwapBuffers", "libEGL.so.1");
	dump_egl(dpy, surface);
	return real(dpy, surface);
}

static EGLBoolean (*real_swap_damage_ext)(EGLDisplay, EGLSurface, const EGLint *, EGLint);
static EGLBoolean swap_damage_ext(EGLDisplay dpy, EGLSurface surface, const EGLint *rects, EGLint n)
{
	dump_egl(dpy, surface);
	return real_swap_damage_ext(dpy, surface, rects, n);
}
static EGLBoolean (*real_swap_damage_khr)(EGLDisplay, EGLSurface, const EGLint *, EGLint);
static EGLBoolean swap_damage_khr(EGLDisplay dpy, EGLSurface surface, const EGLint *rects, EGLint n)
{
	dump_egl(dpy, surface);
	return real_swap_damage_khr(dpy, surface, rects, n);
}

/* Programs that look EGL's entry points up by name get these too */
__eglMustCastToProperFunctionPointerType eglGetProcAddress(const char *name)
{
	static __eglMustCastToProperFunctionPointerType (*real)(const char *);
	if (!real)
		real = next_symbol("eglGetProcAddress", "libEGL.so.1");
	__eglMustCastToProperFunctionPointerType found = real(name);
	if (!found || !name)
		return found;
	if (!strcmp(name, "eglCreatePlatformWindowSurfaceEXT")) {
		if (found != (__eglMustCastToProperFunctionPointerType)eglCreatePlatformWindowSurfaceEXT)
			real_platform_ext = (void *)found;
		return (__eglMustCastToProperFunctionPointerType)eglCreatePlatformWindowSurfaceEXT;
	}
	if (!strcmp(name, "eglCreatePlatformWindowSurface"))
		return (__eglMustCastToProperFunctionPointerType)eglCreatePlatformWindowSurface;
	if (!strcmp(name, "eglCreateWindowSurface"))
		return (__eglMustCastToProperFunctionPointerType)eglCreateWindowSurface;
	if (!strcmp(name, "eglSwapBuffers"))
		return (__eglMustCastToProperFunctionPointerType)eglSwapBuffers;
	if (!strcmp(name, "eglSwapBuffersWithDamageEXT")) {
		real_swap_damage_ext = (void *)found;
		return (__eglMustCastToProperFunctionPointerType)swap_damage_ext;
	}
	if (!strcmp(name, "eglSwapBuffersWithDamageKHR")) {
		real_swap_damage_khr = (void *)found;
		return (__eglMustCastToProperFunctionPointerType)swap_damage_khr;
	}
	return found;
}

struct wl_proxy *wl_proxy_marshal_flags(struct wl_proxy *proxy, uint32_t opcode, const struct wl_interface *interface,
					uint32_t version, uint32_t flags, ...)
{
	static struct wl_proxy *(*real)(struct wl_proxy *, uint32_t, const struct wl_interface *, uint32_t, uint32_t,
					 union wl_argument *);
	if (!real)
		real = next_symbol("wl_proxy_marshal_array_flags", "libwayland-client.so.0");
	union wl_argument args[20]; /* WL_CLOSURE_MAX_ARGS */
	memset(args, 0, sizeof(args));
	const struct wl_interface *own = *(const struct wl_interface **)proxy; /* struct wl_object begins a proxy */
	const char *signature = own && opcode < (uint32_t)own->method_count ? own->methods[opcode].signature : "";
	va_list ap;
	va_start(ap, flags);
	parse_args(signature, ap, args);
	va_end(ap);
	/* The class before the request: a destructor frees the proxy */
	const char *name = own ? own->name : "";
	/* libwayland-client sends a copy of a pool's fd; the client's own stays open, and track() copies it */
	struct wl_proxy *made = real(proxy, opcode, interface, version, flags, args);
	if (getenv("WLREC_DEBUG"))
		fprintf(stderr, "wlrec: %s.%u -> %p\n", name, opcode, (void *)made);
	pthread_mutex_lock(&lock);
	track(name, proxy, opcode, made, args);
	if (flags & WL_MARSHAL_FLAG_DESTROY) {
		struct object *gone = find(proxy);
		if (gone) {
			if (gone->fd >= 0)
				close(gone->fd);
			for (int i = 0; i < MAX_OBJECTS; i++) {
				if (objects[i].pool == gone)
					objects[i].pool = NULL;
				if (objects[i].attached == gone)
					objects[i].attached = NULL;
				if (objects[i].surface == gone)
					objects[i].surface = NULL;
			}
			gone->kind = K_NONE;
			gone->proxy = NULL;
		}
	}
	pthread_mutex_unlock(&lock);
	return made;
}
