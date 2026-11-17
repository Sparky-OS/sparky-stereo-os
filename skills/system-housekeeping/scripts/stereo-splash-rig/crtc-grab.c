// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * crtc-grab: saves the frame every active CRTC scans out, as binary PPMs, and prints each CRTC's mode
 * with its connector. Adapted from vkms-stereo-bench's drm-grab (one CRTC) for screens side by side
 * (a laptop panel and a television). Root in the test guest (CAP_SYS_ADMIN gives GETFB2 the handle).
 *
 *   crtc-grab CARD OUTPREFIX     writes OUTPREFIX-CONNECTOR.ppm per lit connector
 */
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

#include <drm/drm.h>
#include <drm/drm_fourcc.h>
#include <drm/drm_mode.h>

static int fd;

static int xioctl(unsigned long req, void *arg)
{
	int r;

	do {
		r = ioctl(fd, req, arg);
	} while (r == -1 && (errno == EINTR || errno == EAGAIN));
	return r ? -errno : 0;
}

static const char *type_name(uint32_t type)
{
	switch (type) {
	case DRM_MODE_CONNECTOR_HDMIA: return "HDMI-A";
	case DRM_MODE_CONNECTOR_eDP: return "eDP";
	case DRM_MODE_CONNECTOR_DisplayPort: return "DP";
	case DRM_MODE_CONNECTOR_VIRTUAL: return "Virtual";
	case DRM_MODE_CONNECTOR_WRITEBACK: return "Writeback";
	}
	return "Unknown";
}

static int save(uint32_t fb_id, const char *path, unsigned long *nonblack)
{
	struct drm_mode_fb_cmd2 fb = { .fb_id = fb_id };
	struct drm_mode_map_dumb map = { 0 };
	unsigned int x, y;
	uint8_t *pixels, *copy;
	size_t size;
	FILE *out;

	if (xioctl(DRM_IOCTL_MODE_GETFB2, &fb) || !fb.handles[0])
		return -1;
	if (fb.pixel_format != DRM_FORMAT_XRGB8888 && fb.pixel_format != DRM_FORMAT_ARGB8888) {
		fprintf(stderr, "format %.4s not read\n", (char *)&fb.pixel_format);
		return -1;
	}
	map.handle = fb.handles[0];
	if (xioctl(DRM_IOCTL_MODE_MAP_DUMB, &map))
		return -1;
	size = (size_t)fb.pitches[0] * fb.height + fb.offsets[0];
	pixels = mmap(NULL, size, PROT_READ, MAP_SHARED, fd, map.offset);
	copy = malloc(size);
	if (pixels == MAP_FAILED || !copy)
		return -1;
	memcpy(copy, pixels, size);
	out = fopen(path, "wb");
	if (!out)
		return -1;
	fprintf(out, "P6\n%u %u\n255\n", fb.width, fb.height);
	*nonblack = 0;
	for (y = 0; y < fb.height; y++) {
		const uint32_t *row = (const uint32_t *)(copy + fb.offsets[0] + (size_t)y * fb.pitches[0]);

		for (x = 0; x < fb.width; x++) {
			uint8_t rgb[3] = { row[x] >> 16, row[x] >> 8, row[x] };

			fwrite(rgb, 1, 3, out);
			*nonblack += rgb[0] || rgb[1] || rgb[2];
		}
	}
	fclose(out);
	printf("  fb %u %ux%u pitch %u\n", fb_id, fb.width, fb.height, fb.pitches[0]);
	return 0;
}

int main(int argc, char **argv)
{
	struct drm_mode_card_res res = { 0 };
	uint32_t connectors[16], encoders[16], crtcs[16];
	unsigned int i;

	if (argc != 3) {
		fprintf(stderr, "usage: %s CARD OUTPREFIX\n", argv[0]);
		return 2;
	}
	fd = open(argv[1], O_RDWR | O_CLOEXEC);
	if (fd < 0) {
		perror(argv[1]);
		return 1;
	}
	xioctl(DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_STEREO_3D, 1 });
	if (xioctl(DRM_IOCTL_MODE_GETRESOURCES, &res) || res.count_connectors > 16 || res.count_crtcs > 16 ||
	    res.count_encoders > 16)
		return 1;
	res.connector_id_ptr = (uintptr_t)connectors;
	res.encoder_id_ptr = (uintptr_t)encoders;
	res.crtc_id_ptr = (uintptr_t)crtcs;
	res.count_fbs = 0;
	if (xioctl(DRM_IOCTL_MODE_GETRESOURCES, &res))
		return 1;
	for (i = 0; i < res.count_connectors; i++) {
		struct drm_mode_get_connector c = { .connector_id = connectors[i] };
		struct drm_mode_get_encoder e = { 0 };
		struct drm_mode_crtc crtc = { 0 };
		char name[64], path[512];
		unsigned long nonblack = 0;

		if (xioctl(DRM_IOCTL_MODE_GETCONNECTOR, &c))
			continue;
		snprintf(name, sizeof(name), "%s-%u", type_name(c.connector_type), c.connector_type_id);
		if (getenv("CRTC_GRAB_MODES") && c.count_modes > 0) {
			struct drm_mode_modeinfo *modes = calloc(c.count_modes, sizeof(*modes));
			struct drm_mode_get_connector c2 = { .connector_id = connectors[i], .count_modes = c.count_modes,
							     .modes_ptr = (uintptr_t)modes };
			unsigned int m;

			if (modes && !xioctl(DRM_IOCTL_MODE_GETCONNECTOR, &c2))
				for (m = 0; m < c2.count_modes && m < c.count_modes; m++)
					printf("%s mode %u: %ux%u clock %u htotal %u vtotal %u flags 0x%x type 0x%x\n", name, m,
					       modes[m].hdisplay, modes[m].vdisplay, modes[m].clock, modes[m].htotal,
					       modes[m].vtotal, modes[m].flags, modes[m].type);
			free(modes);
		}
		if (!c.encoder_id) {
			printf("%s: off\n", name);
			continue;
		}
		e.encoder_id = c.encoder_id;
		if (xioctl(DRM_IOCTL_MODE_GETENCODER, &e) || !e.crtc_id)
			continue;
		crtc.crtc_id = e.crtc_id;
		if (xioctl(DRM_IOCTL_MODE_GETCRTC, &crtc) || !crtc.mode_valid)
			continue;
		printf("%s: crtc %u mode \"%s\" %ux%u clock %u h %u %u %u %u v %u %u %u %u flags 0x%x 3d %u type 0x%x\n",
		       name, crtc.crtc_id, crtc.mode.name, crtc.mode.hdisplay, crtc.mode.vdisplay, crtc.mode.clock,
		       crtc.mode.hsync_start, crtc.mode.hsync_end, crtc.mode.htotal, crtc.mode.hskew,
		       crtc.mode.vsync_start, crtc.mode.vsync_end, crtc.mode.vtotal, crtc.mode.vscan,
		       crtc.mode.flags, (crtc.mode.flags & DRM_MODE_FLAG_3D_MASK) >> 14, crtc.mode.type);
		snprintf(path, sizeof(path), "%s-%s.ppm", argv[2], name);
		if (crtc.fb_id && !save(crtc.fb_id, path, &nonblack))
			printf("  saved %s nonblack %lu\n", path, nonblack);
		else
			printf("  no frame read (%s)\n", strerror(errno));
	}
	return 0;
}
