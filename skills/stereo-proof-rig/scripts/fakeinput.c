/* SPDX-License-Identifier: MIT */
/*
 * fakeinput: drive the focused window of a headless KWin through org_kde_kwin_fake_input (KWin needs
 * KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 to take it without asking).  Each argument is one step:
 *   k:29+35     press the evdev keys in order, then release them in reverse (here Ctrl+H)
 *   m:X,Y       move the pointer to X,Y (absolute, logical pixels)
 *   b:272       press and release a pointer button (272 = BTN_LEFT)
 *   s:MS        wait MS milliseconds
 *   d:272       a double click: press, release, 90 ms, press, release (272 = BTN_LEFT)
 * fakeinput --serve IN ACK: stay connected (KWin's fake input device, and with it the seat's pointer, lives only
 * while the client is connected) and run each line read from IN as steps, writing "ok" to ACK after each line, or
 * "error" when a step is malformed (ORDER 441: a line that was one comma-joined token used to run only its first
 * step and answer ok; a step is now read whole or refused, and the lines stop at the first refused step).
 * Steps are separated by white space; a comma belongs to a step (m:X,Y) and never separates steps.
 * Each step is printed with its CLOCK_MONOTONIC time in milliseconds (ORDER 249: the clock of the probe).
 * First written for ORDER 207 (queue/vlc-eye-swap-merge-207/tools/fakeinput.c); the d: step and the times for ORDER 249.
 * Build: wayland-scanner client-header/private-code fake-input.xml, then cc fakeinput.c fake-input-protocol.c -lwayland-client
 */
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <time.h>
#include <wayland-client.h>
#include "fake-input-client-protocol.h"

static struct org_kde_kwin_fake_input *fake;

static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
	(void)data;
	if (strcmp(interface, org_kde_kwin_fake_input_interface.name) == 0)
		fake = wl_registry_bind(registry, name, &org_kde_kwin_fake_input_interface, version < 4 ? version : 4);
}

static void global_remove(void *data, struct wl_registry *registry, uint32_t name)
{
	(void)data; (void)registry; (void)name;
}

static const struct wl_registry_listener listener = { global, global_remove };

static long now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
}

static void wait_ms(long ms)
{
	struct timespec ts = { ms / 1000, (ms % 1000) * 1000000L };
	nanosleep(&ts, NULL);
}

static int number(const char *s, unsigned long *v)
{
	char *end;
	errno = 0;
	*v = strtoul(s, &end, 10);
	return errno == 0 && end != s && *end == '\0';
}

static int step(struct wl_display *display, const char *a)
{
	printf("%ld %s\n", now_ms(), a);
	fflush(stdout);
	if (strncmp(a, "k:", 2) == 0) {
		unsigned keys[8];
		int n = 0;
		for (char *p = (char *)a + 2; *p;) {
			char *end;
			errno = 0;
			unsigned long k = strtoul(p, &end, 10);
			if (errno || end == p || n == 8 || (*end != '\0' && *end != '+')) {
				fprintf(stderr, "fakeinput: malformed step %s\n", a);
				return 2;
			}
			keys[n++] = k;
			p = *end == '+' ? end + 1 : end;
		}
		if (n == 0) {
			fprintf(stderr, "fakeinput: malformed step %s\n", a);
			return 2;
		}
		for (int j = 0; j < n; j++) {
			org_kde_kwin_fake_input_keyboard_key(fake, keys[j], WL_KEYBOARD_KEY_STATE_PRESSED);
			wl_display_flush(display);
			wait_ms(30);
		}
		for (int j = n - 1; j >= 0; j--) {
			org_kde_kwin_fake_input_keyboard_key(fake, keys[j], WL_KEYBOARD_KEY_STATE_RELEASED);
			wl_display_flush(display);
			wait_ms(30);
		}
	} else if (strncmp(a, "m:", 2) == 0) {
		double x = 0, y = 0;
		int used = 0;
		if (sscanf(a + 2, "%lf,%lf%n", &x, &y, &used) != 2 || a[2 + used] != '\0') {
			fprintf(stderr, "fakeinput: malformed step %s\n", a);
			return 2;
		}
		org_kde_kwin_fake_input_pointer_motion_absolute(fake, wl_fixed_from_double(x), wl_fixed_from_double(y));
	} else if (strncmp(a, "b:", 2) == 0) {
		unsigned long b;
		if (!number(a + 2, &b)) {
			fprintf(stderr, "fakeinput: malformed step %s\n", a);
			return 2;
		}
		org_kde_kwin_fake_input_button(fake, b, WL_POINTER_BUTTON_STATE_PRESSED);
		wl_display_flush(display);
		wait_ms(30);
		org_kde_kwin_fake_input_button(fake, b, WL_POINTER_BUTTON_STATE_RELEASED);
	} else if (strncmp(a, "d:", 2) == 0) {
		unsigned long b;
		if (!number(a + 2, &b)) {
			fprintf(stderr, "fakeinput: malformed step %s\n", a);
			return 2;
		}
		for (int c = 0; c < 2; c++) {
			org_kde_kwin_fake_input_button(fake, b, WL_POINTER_BUTTON_STATE_PRESSED);
			wl_display_flush(display);
			wait_ms(30);
			org_kde_kwin_fake_input_button(fake, b, WL_POINTER_BUTTON_STATE_RELEASED);
			wl_display_flush(display);
			if (c == 0)
				wait_ms(90);
		}
	} else if (strncmp(a, "s:", 2) == 0) {
		unsigned long ms;
		if (!number(a + 2, &ms)) {
			fprintf(stderr, "fakeinput: malformed step %s\n", a);
			return 2;
		}
		wl_display_flush(display);
		wait_ms(ms);
	} else {
		fprintf(stderr, "fakeinput: unknown step %s\n", a);
		return 2;
	}
	wl_display_roundtrip(display);
	return 0;
}

int main(int argc, char **argv)
{
	struct wl_display *display = wl_display_connect(NULL);
	if (!display) {
		fprintf(stderr, "fakeinput: no Wayland display\n");
		return 1;
	}
	struct wl_registry *registry = wl_display_get_registry(display);
	wl_registry_add_listener(registry, &listener, NULL);
	wl_display_roundtrip(display);
	if (!fake) {
		fprintf(stderr, "fakeinput: the compositor offers no org_kde_kwin_fake_input\n");
		return 1;
	}
	org_kde_kwin_fake_input_authenticate(fake, "fakeinput", "proof rig");
	if (argc == 4 && strcmp(argv[1], "--serve") == 0) {
		FILE *in = fopen(argv[2], "r");
		FILE *ack = fopen(argv[3], "w");
		char *line = NULL;
		size_t n = 0;
		while (in && ack && getline(&line, &n, in) > 0) {
			int rc = 0;
			for (char *tok = strtok(line, " \t\n"); tok && !rc; tok = strtok(NULL, " \t\n"))
				rc = step(display, tok);
			fprintf(ack, rc ? "error\n" : "ok\n");
			fflush(ack);
		}
		free(line);
	} else {
		for (int i = 1; i < argc; i++)
			if (step(display, argv[i]))
				return 2;
	}
	wl_display_roundtrip(display);
	wl_display_disconnect(display);
	return 0;
}
