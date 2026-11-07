// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * drm-planelog: polls the primary plane of the CRTC that drives CONNECTOR every 200 us for MILLISECONDS and prints a line each
 * time its framebuffer or SRC_X changes: milliseconds since start, the framebuffer's id and width, SRC_X and SRC_W in pixels.
 * Started before a mode set it shows the first scanout after the mode set. Not the DRM master (root in the test guest).
 *
 *   drm-planelog CARD CONNECTOR MILLISECONDS
 */
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#include <drm/drm.h>
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

static uint32_t crtc_of(const uint32_t *connectors, unsigned int count, const char *name)
{
	unsigned int i;

	for (i = 0; i < count; i++) {
		struct drm_mode_get_connector c = { .connector_id = connectors[i] };
		struct drm_mode_get_encoder e = { 0 };
		char buf[32];

		if (xioctl(DRM_IOCTL_MODE_GETCONNECTOR, &c) || c.connector_type != DRM_MODE_CONNECTOR_HDMIA)
			continue;
		snprintf(buf, sizeof(buf), "HDMI-A-%u", c.connector_type_id);
		if (strcmp(buf, name))
			continue;
		e.encoder_id = c.encoder_id;
		if (!c.encoder_id || xioctl(DRM_IOCTL_MODE_GETENCODER, &e))
			return 0;
		return e.crtc_id;
	}
	return 0;
}

static int prop_ids(uint32_t plane, uint32_t *type_id, uint32_t *x_id, uint32_t *w_id)
{
	struct drm_mode_obj_get_properties props = { .obj_id = plane, .obj_type = DRM_MODE_OBJECT_PLANE };
	uint32_t ids[64];
	uint64_t values[64];
	unsigned int i;

	if (xioctl(DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &props) || props.count_props > 64)
		return -1;
	props.props_ptr = (uintptr_t)ids;
	props.prop_values_ptr = (uintptr_t)values;
	if (xioctl(DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &props))
		return -1;
	*type_id = *x_id = *w_id = 0;
	for (i = 0; i < props.count_props; i++) {
		struct drm_mode_get_property p = { .prop_id = ids[i] };

		if (xioctl(DRM_IOCTL_MODE_GETPROPERTY, &p))
			continue;
		if (!strcmp(p.name, "type"))
			*type_id = ids[i];
		else if (!strcmp(p.name, "SRC_X"))
			*x_id = ids[i];
		else if (!strcmp(p.name, "SRC_W"))
			*w_id = ids[i];
	}
	return *x_id && *w_id ? 0 : -1;
}

static int values(uint32_t plane, uint32_t x_id, uint32_t w_id, int64_t *x, int64_t *w, uint64_t *type_of, uint32_t type_id)
{
	struct drm_mode_obj_get_properties props = { .obj_id = plane, .obj_type = DRM_MODE_OBJECT_PLANE };
	uint32_t ids[64];
	uint64_t vals[64];
	unsigned int i;

	if (xioctl(DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &props) || props.count_props > 64)
		return -1;
	props.props_ptr = (uintptr_t)ids;
	props.prop_values_ptr = (uintptr_t)vals;
	if (xioctl(DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &props))
		return -1;
	for (i = 0; i < props.count_props; i++) {
		if (ids[i] == x_id)
			*x = vals[i] >> 16;
		else if (ids[i] == w_id)
			*w = vals[i] >> 16;
		else if (ids[i] == type_id && type_of)
			*type_of = vals[i];
	}
	return 0;
}

int main(int argc, char **argv)
{
	struct drm_mode_card_res res = { 0 };
	struct drm_mode_get_plane_res pres = { 0 };
	uint32_t crtcs[8], connectors[8], planes[32], plane = 0, crtc_id, type_id, x_id, w_id, last_fb = 0xffffffff;
	int64_t x = -1, w = -1, last_x = -2;
	unsigned int i;
	struct timespec t0, t;
	long ms;

	if (argc != 4) {
		fprintf(stderr, "usage: %s CARD CONNECTOR MILLISECONDS\n", argv[0]);
		return 2;
	}
	ms = atol(argv[3]);
	fd = open(argv[1], O_RDWR | O_CLOEXEC);
	if (fd < 0) {
		perror(argv[1]);
		return 1;
	}
	xioctl(DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_UNIVERSAL_PLANES, 1 });
	xioctl(DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_ATOMIC, 1 });
	if (xioctl(DRM_IOCTL_MODE_GETRESOURCES, &res) || res.count_crtcs > 8 || res.count_connectors > 8)
		return 1;
	res.crtc_id_ptr = (uintptr_t)crtcs;
	res.connector_id_ptr = (uintptr_t)connectors;
	res.count_encoders = res.count_fbs = 0;
	if (xioctl(DRM_IOCTL_MODE_GETRESOURCES, &res))
		return 1;
	crtc_id = crtc_of(connectors, res.count_connectors, argv[2]);
	if (!crtc_id || xioctl(DRM_IOCTL_MODE_GETPLANERESOURCES, &pres) || pres.count_planes > 32)
		return 1;
	pres.plane_id_ptr = (uintptr_t)planes;
	if (xioctl(DRM_IOCTL_MODE_GETPLANERESOURCES, &pres))
		return 1;
	for (i = 0; i < pres.count_planes && !plane; i++) {
		struct drm_mode_get_plane p = { .plane_id = planes[i] };
		uint32_t a, b, c;
		uint64_t type = 0;
		int64_t xx = 0, ww = 0;

		if (xioctl(DRM_IOCTL_MODE_GETPLANE, &p) || prop_ids(planes[i], &a, &b, &c))
			continue;
		values(planes[i], b, c, &xx, &ww, &type, a);
		if (type == 1 && (p.possible_crtcs & 1))
			plane = planes[i];
	}
	if (!plane || prop_ids(plane, &type_id, &x_id, &w_id)) {
		fprintf(stderr, "no primary plane\n");
		return 1;
	}
	printf("plane %u crtc %u\n", plane, crtc_id);
	clock_gettime(CLOCK_MONOTONIC, &t0);
	for (;;) {
		struct drm_mode_get_plane p = { .plane_id = plane };

		clock_gettime(CLOCK_MONOTONIC, &t);
		if ((t.tv_sec - t0.tv_sec) * 1000 + (t.tv_nsec - t0.tv_nsec) / 1000000 >= ms)
			break;
		if (!xioctl(DRM_IOCTL_MODE_GETPLANE, &p) && !values(plane, x_id, w_id, &x, &w, NULL, type_id)
		    && (p.fb_id != last_fb || x != last_x)) {
			struct drm_mode_fb_cmd2 fb = { .fb_id = p.fb_id };
			int width = p.fb_id && !xioctl(DRM_IOCTL_MODE_GETFB2, &fb) ? (int)fb.width : -1;

			printf("%ld fb %u width %d src_x %lld src_w %lld\n", (long)((t.tv_sec - t0.tv_sec) * 1000 + (t.tv_nsec - t0.tv_nsec) / 1000000),
			       p.fb_id, width, (long long)x, (long long)w);
			last_fb = p.fb_id;
			last_x = x;
		}
		usleep(200);
	}
	return 0;
}
