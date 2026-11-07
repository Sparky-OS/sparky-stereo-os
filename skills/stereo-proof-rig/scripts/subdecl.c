/* SPDX-License-Identifier: GPL-2.0-or-later */
/* subdecl: a window shaped like a player in the edition. The window's own surface is the 2D part
 * (grey, with a transparent hole); a subsurface below it is the 3D area, placed at the hole with
 * wp_viewporter, desynchronized, holding both eyes side by side (left red, right blue, each at its
 * own resolution), declared full side by side once through libstereo-declare, and given a new frame
 * on each of its frame callbacks, as a video would. The order follows Qt Multimedia's stereo layer:
 * the window is mapped first, then the subsurface is made, declared and committed, then the window
 * commits again.
 * Usage: subdecl [--fullscreen] [--window WxH] [--eye WxH] [--pid FILE] [--no-declare]
 * --no-declare is the negative control: the same surfaces and buffers, nothing declared.
 * SIGUSR1 tears the 3D area down as Qt Multimedia's layer does when it goes (the declaration removed, then the
 * viewport, the subsurface and the surface destroyed) and makes it again on the same window; the new area prints
 * "presented N" (N counting the areas made) on its first frame callback.
 * Prints "declared" (or "not declared"), then "presented" when the first frame callback of the 3D area arrives. */
#define _GNU_SOURCE
#include <stereo-declare.h>
#include <wayland-client.h>
#include "viewporter-client.h"
#include "xdg-shell-client.h"

#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/signalfd.h>
#include <unistd.h>

static struct wl_compositor *compositor;
static struct wl_subcompositor *subcompositor;
static struct wl_shm *shm;
static struct xdg_wm_base *wm_base;
static struct wp_viewporter *viewporter;
static int configured, closed, conf_width, conf_height;

struct buffer {
    struct wl_buffer *buffer;
    uint32_t *pixels;
    int busy;
};

static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
    (void)data;
    (void)version;
    if (!strcmp(interface, wl_compositor_interface.name)) {
        compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
    } else if (!strcmp(interface, wl_subcompositor_interface.name)) {
        subcompositor = wl_registry_bind(registry, name, &wl_subcompositor_interface, 1);
    } else if (!strcmp(interface, wl_shm_interface.name)) {
        shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
    } else if (!strcmp(interface, xdg_wm_base_interface.name)) {
        wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, 1);
    } else if (!strcmp(interface, wp_viewporter_interface.name)) {
        viewporter = wl_registry_bind(registry, name, &wp_viewporter_interface, 1);
    }
}

static void global_remove(void *data, struct wl_registry *registry, uint32_t name)
{
    (void)data;
    (void)registry;
    (void)name;
}

static void ping(void *data, struct xdg_wm_base *base, uint32_t serial)
{
    (void)data;
    xdg_wm_base_pong(base, serial);
}

static void surface_configure(void *data, struct xdg_surface *surface, uint32_t serial)
{
    (void)data;
    xdg_surface_ack_configure(surface, serial);
    configured = 1;
}

static void toplevel_configure(void *data, struct xdg_toplevel *toplevel, int32_t width, int32_t height, struct wl_array *states)
{
    (void)data;
    (void)toplevel;
    (void)states;
    if (width > 0 && height > 0) {
        conf_width = width;
        conf_height = height;
    }
}

static void toplevel_close(void *data, struct xdg_toplevel *toplevel)
{
    (void)data;
    (void)toplevel;
    closed = 1;
}

static void buffer_release(void *data, struct wl_buffer *buffer)
{
    (void)buffer;
    ((struct buffer *)data)->busy = 0;
}

static int make_buffer(struct buffer *b, int width, int height, uint32_t format)
{
    static const struct wl_buffer_listener listener = {buffer_release};
    const int stride = width * 4, size = stride * height;
    int fd = memfd_create("subdecl", MFD_CLOEXEC);
    if (fd < 0 || ftruncate(fd, size) < 0) {
        return -1;
    }
    b->pixels = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (b->pixels == MAP_FAILED) {
        close(fd);
        return -1;
    }
    struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, size);
    b->buffer = wl_shm_pool_create_buffer(pool, 0, width, height, stride, format);
    wl_shm_pool_destroy(pool);
    close(fd);
    wl_buffer_add_listener(b->buffer, &listener, b);
    return 0;
}

static struct wl_surface *video;
static struct buffer frames[3];
static int eye_w = 640, eye_h = 360, frame_number, presented, generation;

static void draw_eyes(struct buffer *b, int n)
{
    const int width = 2 * eye_w;
    /* left eye red, right eye blue; a white bar moves with the frame number in both, at the same place */
    const int bar = (n * 8) % eye_w;
    for (int y = 0; y < eye_h; y++) {
        for (int x = 0; x < width; x++) {
            const int ex = x < eye_w ? x : x - eye_w;
            uint32_t c = x < eye_w ? 0xffff0000 : 0xff0000ff;
            if (y < eye_h / 10 && ex >= bar && ex < bar + 8) {
                c = 0xffffffff;
            }
            b->pixels[y * width + x] = c;
        }
    }
}

static void frame_done(void *data, struct wl_callback *callback, uint32_t time);
static const struct wl_callback_listener frame_listener = {frame_done};

static void next_frame(void)
{
    struct buffer *b = NULL;
    for (int i = 0; i < 3; i++) {
        if (!frames[i].busy) {
            b = &frames[i];
            break;
        }
    }
    struct wl_callback *callback = wl_surface_frame(video);
    wl_callback_add_listener(callback, &frame_listener, (void *)(intptr_t)generation);
    if (b) {
        draw_eyes(b, ++frame_number);
        b->busy = 1;
        wl_surface_attach(video, b->buffer, 0, 0);
        wl_surface_damage_buffer(video, 0, 0, 2 * eye_w, eye_h);
    }
    wl_surface_commit(video);
}

static void frame_done(void *data, struct wl_callback *callback, uint32_t time)
{
    (void)time;
    wl_callback_destroy(callback);
    /* a callback of an area torn down since, or of the area being torn down (its done event can arrive in the
     * roundtrip that follows the surface's destruction) */
    if ((intptr_t)data != generation || !video) {
        return;
    }
    if (!presented) {
        presented = 1;
        if (generation > 1) {
            printf("presented %d\n", generation);
        } else {
            printf("presented\n");
        }
        fflush(stdout);
    }
    next_frame();
}

/* The 3D area, as Qt Multimedia's layer makes it: a subsurface below the window, desynchronized, at the hole. */
static struct wl_subsurface *subsurface;
static struct wp_viewport *viewport;

static int make_area(struct wl_surface *parent, int x, int y, int w, int h, int declare)
{
    video = wl_compositor_create_surface(compositor);
    subsurface = wl_subcompositor_get_subsurface(subcompositor, video, parent);
    wl_subsurface_place_below(subsurface, parent);
    wl_subsurface_set_desync(subsurface);
    viewport = wp_viewporter_get_viewport(viewporter, video);
    struct wl_region *empty = wl_compositor_create_region(compositor);
    wl_surface_set_input_region(video, empty);
    wl_region_destroy(empty);
    for (int i = 0; i < 3; i++) {
        if (make_buffer(&frames[i], 2 * eye_w, eye_h, WL_SHM_FORMAT_XRGB8888)) {
            return -1;
        }
    }
    wl_subsurface_set_position(subsurface, x, y);
    wp_viewport_set_destination(viewport, w, h);
    if (declare) {
        const int result = stereo_declare_wayland(video, STEREO_SBS_FULL, STEREO_CLASS_VIDEO, STEREO_VIDEO_CURRENT);
        if (result != 0) {
            fprintf(stderr, "declaration failed: %s\n", strerror(-result));
            return -1;
        }
    }
    generation++;
    presented = 0;
    next_frame();
    /* the subsurface and its position take effect with the window's next commit */
    wl_surface_commit(parent);
    return 0;
}

static void drop_area(struct wl_display *display)
{
    stereo_remove_wayland(video);
    wp_viewport_destroy(viewport);
    wl_subsurface_destroy(subsurface);
    wl_surface_destroy(video);
    video = NULL;
    wl_display_roundtrip(display);
    for (int i = 0; i < 3; i++) {
        wl_buffer_destroy(frames[i].buffer);
        munmap(frames[i].pixels, (size_t)2 * eye_w * 4 * eye_h);
        frames[i] = (struct buffer){0};
    }
}

static int parse_size(const char *text, int *w, int *h)
{
    return sscanf(text, "%dx%d", w, h) == 2 && *w > 0 && *h > 0 ? 0 : -1;
}

int main(int argc, char **argv)
{
    static const struct wl_registry_listener registry_listener = {global, global_remove};
    static const struct xdg_wm_base_listener wm_base_listener = {ping};
    static const struct xdg_surface_listener surface_listener = {surface_configure};
    static const struct xdg_toplevel_listener toplevel_listener = {.configure = toplevel_configure, .close = toplevel_close};
    int fullscreen = 0, win_w = 800, win_h = 450, declare = 1;
    const char *pid_file = NULL;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--fullscreen")) {
            fullscreen = 1;
        } else if (!strcmp(argv[i], "--window") && i + 1 < argc) {
            if (parse_size(argv[++i], &win_w, &win_h)) {
                return 2;
            }
        } else if (!strcmp(argv[i], "--eye") && i + 1 < argc) {
            if (parse_size(argv[++i], &eye_w, &eye_h)) {
                return 2;
            }
        } else if (!strcmp(argv[i], "--pid") && i + 1 < argc) {
            pid_file = argv[++i];
        } else if (!strcmp(argv[i], "--no-declare")) {
            declare = 0;
        } else {
            fprintf(stderr, "usage: subdecl [--fullscreen] [--window WxH] [--eye WxH] [--pid FILE] [--no-declare]\n");
            return 2;
        }
    }
    if (pid_file) {
        FILE *f = fopen(pid_file, "w");
        if (!f) {
            return 1;
        }
        fprintf(f, "%d\n", getpid());
        fclose(f);
    }

    struct wl_display *display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "no Wayland display\n");
        return 1;
    }
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    if (stereo_declare_wayland_init(display, NULL) != 0) {
        return 1;
    }
    wl_display_roundtrip(display);
    if (!compositor || !subcompositor || !shm || !wm_base || !viewporter || !stereo_supported_wayland()) {
        fprintf(stderr, "the compositor lacks a global this test needs\n");
        return 1;
    }
    xdg_wm_base_add_listener(wm_base, &wm_base_listener, NULL);

    struct wl_surface *surface = wl_compositor_create_surface(compositor);
    struct xdg_surface *xdg_surface = xdg_wm_base_get_xdg_surface(wm_base, surface);
    xdg_surface_add_listener(xdg_surface, &surface_listener, NULL);
    struct xdg_toplevel *toplevel = xdg_surface_get_toplevel(xdg_surface);
    xdg_toplevel_add_listener(toplevel, &toplevel_listener, NULL);
    xdg_toplevel_set_title(toplevel, "subdecl");
    if (fullscreen) {
        xdg_toplevel_set_fullscreen(toplevel, NULL);
    }
    wl_surface_commit(surface);
    while (!configured && wl_display_dispatch(display) >= 0) {
    }
    if (fullscreen && conf_width > 0) {
        win_w = conf_width;
        win_h = conf_height;
    }

    /* The 2D part: grey, with a transparent hole where the 3D area shows through. */
    const int hole_x = win_w / 16, hole_y = win_h / 16, hole_w = win_w - 2 * hole_x, hole_h = win_h - 2 * hole_y - win_h / 8;
    struct buffer window;
    if (make_buffer(&window, win_w, win_h, WL_SHM_FORMAT_ARGB8888)) {
        return 1;
    }
    for (int y = 0; y < win_h; y++) {
        for (int x = 0; x < win_w; x++) {
            const int inside = x >= hole_x && x < hole_x + hole_w && y >= hole_y && y < hole_y + hole_h;
            window.pixels[y * win_w + x] = inside ? 0x00000000 : 0xff303030;
        }
    }
    wl_surface_attach(surface, window.buffer, 0, 0);
    wl_surface_damage_buffer(surface, 0, 0, win_w, win_h);
    wl_surface_commit(surface);
    wl_display_roundtrip(display);

    sigset_t mask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGUSR1);
    sigprocmask(SIG_BLOCK, &mask, NULL);
    const int sfd = signalfd(-1, &mask, SFD_CLOEXEC);
    if (make_area(surface, hole_x, hole_y, hole_w, hole_h, declare)) {
        return 1;
    }
    printf(declare ? "declared\n" : "not declared\n");
    fflush(stdout);

    /* read the socket every frame (the proof-rig skill: a client that only dispatches pending events never answers
     * KWin's ping), and the signal that asks for a new area */
    while (!closed) {
        while (wl_display_prepare_read(display) != 0) {
            wl_display_dispatch_pending(display);
        }
        wl_display_flush(display);
        struct pollfd fds[2] = {{wl_display_get_fd(display), POLLIN, 0}, {sfd, POLLIN, 0}};
        if (poll(fds, 2, -1) < 0 && errno != EINTR) {
            wl_display_cancel_read(display);
            break;
        }
        if (fds[0].revents & POLLIN) {
            if (wl_display_read_events(display) < 0) {
                break;
            }
        } else {
            wl_display_cancel_read(display);
        }
        if (wl_display_dispatch_pending(display) < 0) {
            break;
        }
        if (fds[1].revents & POLLIN) {
            struct signalfd_siginfo info;
            if (read(sfd, &info, sizeof(info)) == sizeof(info)) {
                drop_area(display);
                if (make_area(surface, hole_x, hole_y, hole_w, hole_h, declare)) {
                    return 1;
                }
                printf("recreated %d\n", generation);
                fflush(stdout);
            }
        }
    }
    stereo_declare_wayland_finish();
    wl_display_disconnect(display);
    return 0;
}
