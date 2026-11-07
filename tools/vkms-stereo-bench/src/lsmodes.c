// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * lsmodes CARD NAME [EXPECT]: the modes of the card's first non-writeback connector, read with
 * DRM_CLIENT_CAP_STEREO_3D set, as "WxH@R layout" (the format names of the vkms-stereo-bench); compares the stereo
 * formats with the lines of EXPECT (made from edid-decode's text by expect-from-decode.py, not from the kernel).
 * Prints STEREO|mode lines, STEREO|info missing/unexpected lines and one STEREO|check|NAME/stereo-formats line.
 * A second run without the capability shows that stereo modes are hidden from clients that do not ask for them.
 */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>

static const char *const lay[] = { "2d", "fp", "field-alt", "line-alt", "sbs-full", "l-depth", "l-depth-gfx", "tab", "sbs-half" };

static void fmt(const struct drm_mode_modeinfo *m, char *s, size_t n)
{
	unsigned int l = (m->flags & DRM_MODE_FLAG_3D_MASK) >> 14;
	double hz = m->clock * 1000.0 / (m->htotal * m->vtotal);
	/* the format's own rate, as 60 for 59.94: the list holds both */
	snprintf(s, n, "%ux%u@%d %s", m->hdisplay, m->vdisplay, (int)(hz + 0.5), l < 9 ? lay[l] : "?");
}

int main(int argc, char **argv)
{
	int fd, cap = !getenv("NOCAP");
	struct drm_mode_card_res res = {0};
	uint32_t *conns;
	char seen[96][48], want[96][48], line[96];
	int n_seen = 0, n_want = 0, i, j, missing = 0, extra = 0, n2d = 0, nst = 0;
	unsigned int k, c;
	FILE *f;

	if (argc < 3)
		return 2;
	fd = open(argv[1], O_RDWR | O_CLOEXEC);
	if (fd < 0)
		return perror(argv[1]), 2;
	if (cap)
		ioctl(fd, DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_STEREO_3D, 1 });
	ioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &res);
	conns = calloc(res.count_connectors, 4);
	res.connector_id_ptr = (uintptr_t)conns;
	res.count_fbs = res.count_crtcs = res.count_encoders = 0;
	ioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &res);
	for (c = 0; c < res.count_connectors; c++) {
		struct drm_mode_get_connector gc = { .connector_id = conns[c] };
		struct drm_mode_modeinfo *modes;

		ioctl(fd, DRM_IOCTL_MODE_GETCONNECTOR, &gc);	/* count */
		if (gc.connector_type == DRM_MODE_CONNECTOR_WRITEBACK)
			continue;
		modes = calloc(gc.count_modes + 1, sizeof(*modes));
		gc.modes_ptr = (uintptr_t)modes;
		gc.count_props = gc.count_encoders = 0;
		gc.count_modes = gc.count_modes;
		ioctl(fd, DRM_IOCTL_MODE_GETCONNECTOR, &gc);
		for (k = 0; k < gc.count_modes; k++) {
			char s[48];

			fmt(&modes[k], s, sizeof(s));
			printf("STEREO|mode|%s|%s|%u kHz %u/%u %u/%u\n", argv[2], s, modes[k].clock,
			       modes[k].hdisplay, modes[k].htotal, modes[k].vdisplay, modes[k].vtotal);
			if (!(modes[k].flags & DRM_MODE_FLAG_3D_MASK)) {
				n2d++;
				continue;
			}
			nst++;
			for (i = 0; i < n_seen && strcmp(seen[i], s); i++)
				;
			if (i == n_seen && n_seen < 96)
				strcpy(seen[n_seen++], s);
		}
		break;
	}
	printf("STEREO|info|%s|%d 2D modes, %d stereo modes (%d stereo formats), stereo cap %s\n", argv[2], n2d, nst, n_seen,
	       cap ? "set" : "not set");
	f = argc > 3 ? fopen(argv[3], "r") : NULL;
	if (argc > 3 && !f)
		return printf("STEREO|check|%s/stereo-formats|FAIL|cannot open %s\n", argv[2], argv[3]), 1;
	while (f && fgets(line, sizeof(line), f) && n_want < 96) {
		line[strcspn(line, "\n")] = 0;
		if (line[0] && line[0] != '#')
			strcpy(want[n_want++], line);
	}
	for (i = 0; i < n_want; i++) {
		for (j = 0; j < n_seen && strcmp(want[i], seen[j]); j++)
			;
		if (j == n_seen)
			missing++, printf("STEREO|info|%s|missing %s\n", argv[2], want[i]);
	}
	for (j = 0; j < n_seen; j++) {
		for (i = 0; i < n_want && strcmp(want[i], seen[j]); i++)
			;
		if (i == n_want)
			extra++, printf("STEREO|info|%s|unexpected %s\n", argv[2], seen[j]);
	}
	printf("STEREO|check|%s/stereo-formats|%s|%d stereo formats listed, %d expected, %d missing, %d unexpected\n", argv[2],
	       !missing && !extra ? "PASS" : "FAIL", n_seen, n_want, missing, extra);
	return missing || extra;
}
