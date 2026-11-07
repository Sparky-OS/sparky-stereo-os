/* SPDX-License-Identifier: GPL-2.0-or-later */
/* ext510116: the steps of KWin BUG 510116 as a plain Wayland client.
 * One wl_surface. Round after round, the client makes a pointer confinement on it, commits, destroys the confinement,
 * makes a pointer lock on it (another surface extension, another state type) and commits, destroys it. The compositor
 * frees one extension object and allocates the next, which often lands at the same address; before upstream 5f587fb72b
 * the surface's current state still held the freed extension's state under that address and handed it to the new one.
 * Usage: ext510116 [ROUNDS]. Prints "rounds N" when it finishes; exits 1 when the connection to the compositor is lost. */
#include <wayland-client.h>
#include "pointer-constraints-unstable-v1-client.h"
#include "fake-input-client.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static struct wl_compositor *compositor;
static struct zwp_pointer_constraints_v1 *constraints;
static struct wl_seat *seat;
static int has_pointer;
static struct org_kde_kwin_fake_input *fake;

static void seat_capabilities(void *data, struct wl_seat *s, uint32_t capabilities)
{
    (void)data;
    (void)s;
    has_pointer = capabilities & WL_SEAT_CAPABILITY_POINTER;
}
static void seat_name(void *data, struct wl_seat *s, const char *name) { (void)data; (void)s; (void)name; }
static const struct wl_seat_listener seat_listener = {seat_capabilities, seat_name};

static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
    (void)data;
    (void)version;
    if (!strcmp(interface, wl_compositor_interface.name)) {
        compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
    } else if (!strcmp(interface, wl_seat_interface.name)) {
        seat = wl_registry_bind(registry, name, &wl_seat_interface, 1);
        wl_seat_add_listener(seat, &seat_listener, NULL);
    } else if (!strcmp(interface, org_kde_kwin_fake_input_interface.name)) {
        fake = wl_registry_bind(registry, name, &org_kde_kwin_fake_input_interface, 4);
    } else if (!strcmp(interface, zwp_pointer_constraints_v1_interface.name)) {
        constraints = wl_registry_bind(registry, name, &zwp_pointer_constraints_v1_interface, 1);
    }
}

static void global_remove(void *data, struct wl_registry *registry, uint32_t name)
{
    (void)data;
    (void)registry;
    (void)name;
}

static const struct wl_registry_listener registry_listener = {global, global_remove};

static void confined(void *d, struct zwp_confined_pointer_v1 *p) { (void)d; (void)p; }
static void unconfined(void *d, struct zwp_confined_pointer_v1 *p) { (void)d; (void)p; }
static const struct zwp_confined_pointer_v1_listener confined_listener = {confined, unconfined};
static void locked(void *d, struct zwp_locked_pointer_v1 *p) { (void)d; (void)p; }
static void unlocked(void *d, struct zwp_locked_pointer_v1 *p) { (void)d; (void)p; }
static const struct zwp_locked_pointer_v1_listener locked_listener = {locked, unlocked};

static int sync_or_die(struct wl_display *display)
{
    if (wl_display_roundtrip(display) < 0) {
        fprintf(stderr, "ext510116: the connection to the compositor was lost\n");
        return -1;
    }
    return 0;
}

int main(int argc, char **argv)
{
    int rounds = argc > 1 ? atoi(argv[1]) : 200;
    struct wl_display *display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "ext510116: no Wayland display\n");
        return 2;
    }
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    wl_display_roundtrip(display);
    /* The virtual compositor has no pointer until an input device exists: the fake input protocol makes one. */
    if (fake) {
        org_kde_kwin_fake_input_authenticate(fake, "ext510116", "BUG 510116");
        org_kde_kwin_fake_input_pointer_motion(fake, wl_fixed_from_int(1), wl_fixed_from_int(1));
        wl_display_roundtrip(display);
    }
    for (int i = 0; seat && i < 20 && !has_pointer; ++i) {
        wl_display_roundtrip(display);
        if (!has_pointer) {
            struct timespec t = {0, 100000000};
            nanosleep(&t, NULL);
        }
    }
    struct wl_pointer *pointer = has_pointer ? wl_seat_get_pointer(seat) : NULL;
    if (!compositor || !constraints || !pointer) {
        fprintf(stderr, "ext510116: the compositor has no wl_compositor, zwp_pointer_constraints_v1 or pointer\n");
        return 2;
    }
    struct wl_surface *surface = wl_compositor_create_surface(compositor);
    for (int i = 1; i <= rounds; ++i) {
        struct zwp_confined_pointer_v1 *confinement = zwp_pointer_constraints_v1_confine_pointer(constraints, surface, pointer, NULL, ZWP_POINTER_CONSTRAINTS_V1_LIFETIME_PERSISTENT);
        zwp_confined_pointer_v1_add_listener(confinement, &confined_listener, NULL);
        wl_surface_commit(surface);
        if (sync_or_die(display) < 0) {
            printf("lost at round %d\n", i);
            return 1;
        }
        zwp_confined_pointer_v1_destroy(confinement);

        struct zwp_locked_pointer_v1 *lock = zwp_pointer_constraints_v1_lock_pointer(constraints, surface, pointer, NULL, ZWP_POINTER_CONSTRAINTS_V1_LIFETIME_PERSISTENT);
        zwp_locked_pointer_v1_add_listener(lock, &locked_listener, NULL);
        wl_surface_commit(surface);
        if (sync_or_die(display) < 0) {
            printf("lost at round %d\n", i);
            return 1;
        }
        zwp_locked_pointer_v1_destroy(lock);
    }
    wl_surface_commit(surface);
    if (sync_or_die(display) < 0) {
        printf("lost at the end\n");
        return 1;
    }
    printf("rounds %d\n", rounds);
    return 0;
}
