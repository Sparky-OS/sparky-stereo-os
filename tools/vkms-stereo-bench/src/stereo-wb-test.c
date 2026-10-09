// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * stereo-wb-test: checks the stereo modes of a KMS device through its
 * writeback connector. Raw DRM ioctls, no library.
 *
 *   stereo-wb-test CARD [--expect FILE] [--name NAME] [--out DIR]
 *
 * 1. Lists the connector's modes with DRM_CLIENT_CAP_STEREO_3D set and
 *    compares the stereo formats ("WxH@R layout") with FILE.
 * 2. For every listed mode, shows a frame holding a known left and right eye
 *    in the packing of the mode's layout (HDMI 1.4b 3D structures):
 *      frame packing      left eye, active space (vtotal - vdisplay lines),
 *                         right eye: vdisplay + vtotal lines
 *      side by side full  left eye, right eye: 2 x hdisplay columns
 *      side by side half  left half, right half of the mode
 *      top and bottom     top half, bottom half of the mode
 *    reads the writeback buffer back and checks every pixel.
 * 3. Per layout, the same with one plane per eye at its place in the frame.
 * 4. Refuses: a writeback buffer of one eye in a frame packing mode, a
 *    buffer of a frame packing frame in a 2D mode (TEST_ONLY commits).
 * 5. The vblank period of a frame packing mode equals that of its 2D mode.
 *
 * Results: "STEREO|check|<name>|PASS|<detail>" or FAIL lines on stdout,
 * exit status 0 when every check passed.
 */
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdarg.h>
#include <stdbool.h>
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

#define LAYOUT(m) (((m)->flags & DRM_MODE_FLAG_3D_MASK) >> 14)
#define FP 1
#define SBS_FULL 4
#define TAB 7
#define SBS_HALF 8

/* values of the plane "type" property */
#define PLANE_OVERLAY 0
#define PLANE_PRIMARY 1

static const char *const layout_names[] = {
	"2d", "fp", "field-alt", "line-alt", "sbs-full", "l-depth", "l-depth-gfx",
	"tab", "sbs-half",
};

static int fd;
static const char *dev_name = "vkms";
static const char *out_dir;
static int n_checks, n_failures;

static void check(const char *name, bool ok, const char *fmt, ...)
{
	va_list ap;

	n_checks++;
	if (!ok)
		n_failures++;
	printf("STEREO|check|%s/%s|%s|", dev_name, name, ok ? "PASS" : "FAIL");
	va_start(ap, fmt);
	vprintf(fmt, ap);
	va_end(ap);
	printf("\n");
	fflush(stdout);
}

static int xioctl(unsigned long req, void *arg)
{
	int r;

	do {
		r = ioctl(fd, req, arg);
	} while (r == -1 && (errno == EINTR || errno == EAGAIN));
	return r ? -errno : 0;
}

static const char *layout_name(int layout)
{
	return layout < 9 ? layout_names[layout] : "?";
}

static void format_name(const struct drm_mode_modeinfo *m, char *s, size_t n)
{
	snprintf(s, n, "%dx%d%s@%d %s", m->hdisplay, m->vdisplay,
		 m->flags & DRM_MODE_FLAG_INTERLACE ? "i" : "", m->vrefresh,
		 layout_name(LAYOUT(m)));
}

/* properties */

static uint32_t prop_id(uint32_t obj, uint32_t type, const char *name, uint64_t *value)
{
	struct drm_mode_obj_get_properties op = { .obj_id = obj, .obj_type = type };
	uint32_t ids[128];
	uint64_t vals[128];
	unsigned int i;

	if (xioctl(DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &op) || op.count_props > 128)
		return 0;
	op.props_ptr = (uintptr_t)ids;
	op.prop_values_ptr = (uintptr_t)vals;
	if (xioctl(DRM_IOCTL_MODE_OBJ_GETPROPERTIES, &op))
		return 0;
	for (i = 0; i < op.count_props; i++) {
		struct drm_mode_get_property p = { .prop_id = ids[i] };

		if (xioctl(DRM_IOCTL_MODE_GETPROPERTY, &p))
			continue;
		if (!strcmp(p.name, name)) {
			if (value)
				*value = vals[i];
			return ids[i];
		}
	}
	return 0;
}

/* objects of the device */

struct plane {
	uint32_t id, type;
	uint32_t fb_id, crtc_id, src_x, src_y, src_w, src_h, crtc_x, crtc_y, crtc_w, crtc_h;
};

static uint32_t crtc_id, conn_id, wb_id;
static uint32_t p_mode_id, p_active, p_conn_crtc, p_wb_crtc, p_wb_fb, p_wb_fence;
static struct plane planes[16];
static int n_planes;
static struct drm_mode_modeinfo *modes;
static unsigned int n_modes;

static int find_objects(void)
{
	struct drm_mode_card_res res = { 0 };
	struct drm_mode_get_plane_res pres = { 0 };
	uint32_t ids[32], crtcs[8], plane_ids[16];
	unsigned int i;

	if (xioctl(DRM_IOCTL_MODE_GETRESOURCES, &res) || res.count_connectors > 32 ||
	    res.count_crtcs > 8 || !res.count_crtcs)
		return -1;
	res.connector_id_ptr = (uintptr_t)ids;
	res.crtc_id_ptr = (uintptr_t)crtcs;
	res.count_fbs = 0;
	res.count_encoders = 0;
	if (xioctl(DRM_IOCTL_MODE_GETRESOURCES, &res))
		return -1;
	crtc_id = crtcs[0];

	for (i = 0; i < res.count_connectors; i++) {
		struct drm_mode_get_connector c = { .connector_id = ids[i] };

		if (xioctl(DRM_IOCTL_MODE_GETCONNECTOR, &c))
			return -1;
		if (c.connector_type == DRM_MODE_CONNECTOR_WRITEBACK) {
			wb_id = ids[i];
			continue;
		}
		conn_id = ids[i];
		modes = calloc(c.count_modes, sizeof(*modes));
		c.count_props = 0;
		c.count_encoders = 0;
		c.modes_ptr = (uintptr_t)modes;
		if (xioctl(DRM_IOCTL_MODE_GETCONNECTOR, &c))
			return -1;
		n_modes = c.count_modes;
		printf("STEREO|info|%s|connector %u type %u, %u modes\n", dev_name,
		       ids[i], c.connector_type, n_modes);
	}
	if (!conn_id || !wb_id)
		return -1;

	if (xioctl(DRM_IOCTL_MODE_GETPLANERESOURCES, &pres) || pres.count_planes > 16)
		return -1;
	pres.plane_id_ptr = (uintptr_t)plane_ids;
	if (xioctl(DRM_IOCTL_MODE_GETPLANERESOURCES, &pres))
		return -1;
	for (i = 0; i < pres.count_planes; i++) {
		struct plane *p = &planes[n_planes++];
		uint64_t type = 0;

		p->id = plane_ids[i];
		prop_id(p->id, DRM_MODE_OBJECT_PLANE, "type", &type);
		p->type = type;
		p->fb_id = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "FB_ID", NULL);
		p->crtc_id = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "CRTC_ID", NULL);
		p->src_x = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "SRC_X", NULL);
		p->src_y = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "SRC_Y", NULL);
		p->src_w = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "SRC_W", NULL);
		p->src_h = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "SRC_H", NULL);
		p->crtc_x = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "CRTC_X", NULL);
		p->crtc_y = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "CRTC_Y", NULL);
		p->crtc_w = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "CRTC_W", NULL);
		p->crtc_h = prop_id(p->id, DRM_MODE_OBJECT_PLANE, "CRTC_H", NULL);
	}

	p_mode_id = prop_id(crtc_id, DRM_MODE_OBJECT_CRTC, "MODE_ID", NULL);
	p_active = prop_id(crtc_id, DRM_MODE_OBJECT_CRTC, "ACTIVE", NULL);
	p_conn_crtc = prop_id(conn_id, DRM_MODE_OBJECT_CONNECTOR, "CRTC_ID", NULL);
	p_wb_crtc = prop_id(wb_id, DRM_MODE_OBJECT_CONNECTOR, "CRTC_ID", NULL);
	p_wb_fb = prop_id(wb_id, DRM_MODE_OBJECT_CONNECTOR, "WRITEBACK_FB_ID", NULL);
	p_wb_fence = prop_id(wb_id, DRM_MODE_OBJECT_CONNECTOR, "WRITEBACK_OUT_FENCE_PTR", NULL);
	return p_mode_id && p_active && p_conn_crtc && p_wb_crtc && p_wb_fb && p_wb_fence ? 0 : -1;
}

static struct plane *plane_of_type(uint32_t type)
{
	int i;

	for (i = 0; i < n_planes; i++)
		if (planes[i].type == type)
			return &planes[i];
	return NULL;
}

/* buffers */

struct buf {
	uint32_t handle, pitch, fb;
	uint64_t size;
	uint32_t *map;
	int w, h;
};

static int buf_create(struct buf *b, int w, int h)
{
	struct drm_mode_create_dumb c = { .width = w, .height = h, .bpp = 32 };
	struct drm_mode_fb_cmd2 f = { .width = w, .height = h,
				      .pixel_format = DRM_FORMAT_XRGB8888 };
	struct drm_mode_map_dumb m = { 0 };
	int ret;

	memset(b, 0, sizeof(*b));
	ret = xioctl(DRM_IOCTL_MODE_CREATE_DUMB, &c);
	if (ret)
		return ret;
	b->handle = c.handle;
	b->pitch = c.pitch;
	b->size = c.size;
	b->w = w;
	b->h = h;
	f.handles[0] = c.handle;
	f.pitches[0] = c.pitch;
	ret = xioctl(DRM_IOCTL_MODE_ADDFB2, &f);
	if (ret)
		return ret;
	b->fb = f.fb_id;
	m.handle = c.handle;
	ret = xioctl(DRM_IOCTL_MODE_MAP_DUMB, &m);
	if (ret)
		return ret;
	b->map = mmap(NULL, c.size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, m.offset);
	return b->map == MAP_FAILED ? -errno : 0;
}

static void buf_destroy(struct buf *b)
{
	struct drm_mode_destroy_dumb d = { .handle = b->handle };

	if (b->map && b->map != MAP_FAILED)
		munmap(b->map, b->size);
	if (b->fb)
		xioctl(DRM_IOCTL_MODE_RMFB, &b->fb);
	if (b->handle)
		xioctl(DRM_IOCTL_MODE_DESTROY_DUMB, &d);
	memset(b, 0, sizeof(*b));
}

static uint32_t *px(struct buf *b, int x, int y)
{
	return &b->map[y * (b->pitch / 4) + x];
}

/*
 * The test picture of one eye: red holds the eye (0xa_ left, 0x5_ right,
 * 0xf_ 2D) and the high bits of x and y, green and blue the low bits.
 */
static uint32_t eye_pixel(int eye, int x, int y)
{
	static const uint32_t marker[] = { 0xa, 0x5, 0xf };
	uint32_t r = marker[eye] << 4 | (((x >> 8) ^ (y >> 8)) & 0xf);

	return 0xff000000 | r << 16 | (x & 0xff) << 8 | (y & 0xff);
}

struct region {
	int x, y, w, h;
};

/* The frame of a mode and where each eye sits in it (HDMI 1.4b). */
static void frame_layout(const struct drm_mode_modeinfo *m, int *fw, int *fh,
			 struct region *l, struct region *r)
{
	int h = m->hdisplay, v = m->vdisplay;

	*fw = h;
	*fh = v;
	*l = (struct region){ 0, 0, h, v };
	*r = (struct region){ 0, 0, 0, 0 };
	switch (LAYOUT(m)) {
	case FP:
		*fh = v + m->vtotal;
		*r = (struct region){ 0, m->vtotal, h, v };
		break;
	case SBS_FULL:
		*fw = 2 * h;
		*r = (struct region){ h, 0, h, v };
		break;
	case SBS_HALF:
		*l = (struct region){ 0, 0, h / 2, v };
		*r = (struct region){ h / 2, 0, h / 2, v };
		break;
	case TAB:
		*l = (struct region){ 0, 0, h, v / 2 };
		*r = (struct region){ 0, v / 2, h, v / 2 };
		break;
	}
}

static uint32_t expected_pixel(int x, int y, const struct region *l, const struct region *r,
			       bool stereo)
{
	if (x >= l->x && x < l->x + l->w && y >= l->y && y < l->y + l->h)
		return eye_pixel(stereo ? 0 : 2, x - l->x, y - l->y);
	if (x >= r->x && x < r->x + r->w && y >= r->y && y < r->y + r->h)
		return eye_pixel(1, x - r->x, y - r->y);
	return 0;	/* active space, and the CRTC's black background */
}

static void fill_eye(struct buf *b, int eye)
{
	int x, y;

	for (y = 0; y < b->h; y++)
		for (x = 0; x < b->w; x++)
			*px(b, x, y) = eye_pixel(eye, x, y);
}

/* commits */

struct req {
	uint32_t objs[32], counts[32], props[128];
	uint64_t vals[128];
	int n_objs, n_props;
};

static void add(struct req *r, uint32_t obj, uint32_t prop, uint64_t val)
{
	if (!r->n_objs || r->objs[r->n_objs - 1] != obj) {
		r->objs[r->n_objs] = obj;
		r->counts[r->n_objs++] = 0;
	}
	r->counts[r->n_objs - 1]++;
	r->props[r->n_props] = prop;
	r->vals[r->n_props++] = val;
}

struct show {
	struct plane *plane;
	struct buf *buf;
	int x, y;
};

/* Sets the mode with the given planes (all others off) and a writeback job. */
static int commit(const struct drm_mode_modeinfo *m, struct show *shows, int n_shows,
		  struct buf *wb, int *fence, uint32_t flags)
{
	struct drm_mode_create_blob blob = { .data = (uintptr_t)m, .length = sizeof(*m) };
	struct drm_mode_atomic a = { 0 };
	struct req r = { 0 };
	int i, j, ret;

	ret = xioctl(DRM_IOCTL_MODE_CREATEPROPBLOB, &blob);
	if (ret)
		return ret;
	add(&r, crtc_id, p_mode_id, blob.blob_id);
	add(&r, crtc_id, p_active, 1);
	add(&r, conn_id, p_conn_crtc, crtc_id);
	for (i = 0; i < n_planes; i++) {
		struct plane *p = &planes[i];
		struct show *s = NULL;

		for (j = 0; j < n_shows; j++)
			if (shows[j].plane == p)
				s = &shows[j];
		if (!s) {
			add(&r, p->id, p->fb_id, 0);
			add(&r, p->id, p->crtc_id, 0);
			continue;
		}
		add(&r, p->id, p->fb_id, s->buf->fb);
		add(&r, p->id, p->crtc_id, crtc_id);
		add(&r, p->id, p->src_x, 0);
		add(&r, p->id, p->src_y, 0);
		add(&r, p->id, p->src_w, (uint64_t)s->buf->w << 16);
		add(&r, p->id, p->src_h, (uint64_t)s->buf->h << 16);
		add(&r, p->id, p->crtc_x, s->x);
		add(&r, p->id, p->crtc_y, s->y);
		add(&r, p->id, p->crtc_w, s->buf->w);
		add(&r, p->id, p->crtc_h, s->buf->h);
	}
	add(&r, wb_id, p_wb_crtc, crtc_id);
	add(&r, wb_id, p_wb_fb, wb->fb);
	if (fence) {
		*fence = -1;
		add(&r, wb_id, p_wb_fence, (uintptr_t)fence);
	}
	a.flags = DRM_MODE_ATOMIC_ALLOW_MODESET | flags;
	a.count_objs = r.n_objs;
	a.objs_ptr = (uintptr_t)r.objs;
	a.count_props_ptr = (uintptr_t)r.counts;
	a.props_ptr = (uintptr_t)r.props;
	a.prop_values_ptr = (uintptr_t)r.vals;
	ret = xioctl(DRM_IOCTL_MODE_ATOMIC, &a);
	xioctl(DRM_IOCTL_MODE_DESTROYPROPBLOB, &(struct drm_mode_destroy_blob){ blob.blob_id });
	return ret;
}

static int wait_fence(int fence)
{
	struct pollfd p = { .fd = fence, .events = POLLIN };
	int ret = poll(&p, 1, 5000);

	close(fence);
	return ret == 1 ? 0 : -ETIMEDOUT;
}

static void save_ppm(struct buf *b, const char *tag)
{
	char path[512];
	FILE *f;
	int x, y, step = b->w > 1000 ? 4 : 2;

	if (!out_dir)
		return;
	snprintf(path, sizeof(path), "%s/%s-%s.ppm", out_dir, dev_name, tag);
	f = fopen(path, "wb");
	if (!f)
		return;
	fprintf(f, "P6\n%d %d\n255\n", b->w / step, b->h / step);
	for (y = 0; y < b->h / step * step; y += step)
		for (x = 0; x < b->w / step * step; x += step) {
			uint32_t p = *px(b, x, y);

			fputc(p >> 16 & 0xff, f);
			fputc(p >> 8 & 0xff, f);
			fputc(p & 0xff, f);
		}
	fclose(f);
}

/* Compares the writeback frame with the expected picture; returns mismatches. */
static long compare(struct buf *wb, const struct region *l, const struct region *r,
		    bool stereo, char *first, size_t n)
{
	long bad = 0;
	int x, y;

	for (y = 0; y < wb->h; y++)
		for (x = 0; x < wb->w; x++) {
			uint32_t got = *px(wb, x, y) & 0xffffff;
			uint32_t want = expected_pixel(x, y, l, r, stereo) & 0xffffff;

			if (got != want && !bad++)
				snprintf(first, n, "first at %d,%d: 0x%06x, want 0x%06x",
					 x, y, got, want);
		}
	return bad;
}

/* One plane holding the whole packed frame, as a compositor presents it. */
static void test_packed(const struct drm_mode_modeinfo *m, bool save)
{
	struct region l, r;
	struct buf src, wb;
	char name[64], tag[64], first[96] = "";
	int fw, fh, fence, x, y, ret;
	bool stereo = LAYOUT(m) != 0;
	long bad;

	format_name(m, name, sizeof(name));
	frame_layout(m, &fw, &fh, &l, &r);
	if (buf_create(&src, fw, fh) || buf_create(&wb, fw, fh)) {
		check(name, false, "buffers %dx%d: %s", fw, fh, strerror(errno));
		return;
	}
	for (y = 0; y < fh; y++)
		for (x = 0; x < fw; x++)
			*px(&src, x, y) = expected_pixel(x, y, &l, &r, stereo);
	memset(wb.map, 0x55, wb.size);

	ret = commit(m, &(struct show){ plane_of_type(PLANE_PRIMARY), &src, 0, 0 }, 1,
		     &wb, &fence, 0);
	if (!ret)
		ret = wait_fence(fence);
	if (ret) {
		check(name, false, "packed frame %dx%d: commit or writeback: %s", fw, fh,
		      strerror(-ret));
	} else {
		bad = compare(&wb, &l, &r, stereo, first, sizeof(first));
		check(name, !bad,
		      "packed frame %dx%d, left eye %dx%d at %d,%d, right eye %dx%d at %d,%d: %ld wrong pixels %s",
		      fw, fh, l.w, l.h, l.x, l.y, r.w, r.h, r.x, r.y, bad, first);
		if (save) {
			snprintf(tag, sizeof(tag), "%dx%d-%d-%s-packed", m->hdisplay, m->vdisplay,
				 m->vrefresh, layout_name(LAYOUT(m)));
			save_ppm(&wb, tag);
		}
	}
	buf_destroy(&src);
	buf_destroy(&wb);
}

/* One plane per eye, each at its place in the frame. */
static void test_planes(const struct drm_mode_modeinfo *m)
{
	struct plane *overlay = plane_of_type(PLANE_OVERLAY);
	struct buf left, right, wb;
	struct region l, r;
	char name[96], first[96] = "";
	int fw, fh, fence, ret;
	long bad;

	format_name(m, name, sizeof(name));
	strcat(name, " two planes");
	if (!overlay) {
		check(name, false, "no overlay plane");
		return;
	}
	frame_layout(m, &fw, &fh, &l, &r);
	if (buf_create(&left, l.w, l.h) || buf_create(&right, r.w, r.h) ||
	    buf_create(&wb, fw, fh)) {
		check(name, false, "buffers: %s", strerror(errno));
		return;
	}
	fill_eye(&left, 0);
	fill_eye(&right, 1);
	memset(wb.map, 0x55, wb.size);

	ret = commit(m, (struct show[]){
			{ plane_of_type(PLANE_PRIMARY), &left, l.x, l.y },
			{ overlay, &right, r.x, r.y } }, 2, &wb, &fence, 0);
	if (!ret)
		ret = wait_fence(fence);
	if (ret) {
		check(name, false, "commit or writeback: %s", strerror(-ret));
	} else {
		bad = compare(&wb, &l, &r, true, first, sizeof(first));
		check(name, !bad, "left plane at %d,%d, right plane at %d,%d in a %dx%d frame: %ld wrong pixels %s",
		      l.x, l.y, r.x, r.y, fw, fh, bad, first);
	}
	buf_destroy(&left);
	buf_destroy(&right);
	buf_destroy(&wb);
}

/* The writeback connector refuses a buffer that is not the frame. */
static void test_refused(const struct drm_mode_modeinfo *m, int w, int h, const char *what)
{
	struct region l, r;
	struct buf src, wb;
	char name[96];
	int fw, fh, ret;

	format_name(m, name, sizeof(name));
	strcat(name, " refuses ");
	strcat(name, what);
	frame_layout(m, &fw, &fh, &l, &r);
	if (buf_create(&src, fw, fh) || buf_create(&wb, w, h)) {
		check(name, false, "buffers: %s", strerror(errno));
		return;
	}
	ret = commit(m, &(struct show){ plane_of_type(PLANE_PRIMARY), &src, 0, 0 }, 1,
		     &wb, NULL, DRM_MODE_ATOMIC_TEST_ONLY);
	check(name, ret == -EINVAL, "writeback buffer %dx%d in a %dx%d frame: %s", w, h, fw, fh,
	      ret ? strerror(-ret) : "accepted");
	buf_destroy(&src);
	buf_destroy(&wb);
}

/* Mean vblank period over n frames, in microseconds. */
static double vblank_period(const struct drm_mode_modeinfo *m, int n)
{
	struct region l, r;
	struct buf src, wb;
	double first = 0, last = 0;
	int fw, fh, fence, i;

	frame_layout(m, &fw, &fh, &l, &r);
	if (buf_create(&src, fw, fh) || buf_create(&wb, fw, fh))
		return -1;
	if (commit(m, &(struct show){ plane_of_type(PLANE_PRIMARY), &src, 0, 0 }, 1,
		   &wb, &fence, 0) || wait_fence(fence))
		return -1;
	for (i = 0; i <= n; i++) {
		union drm_wait_vblank v = { .request = { .type = _DRM_VBLANK_RELATIVE,
							 .sequence = 1 } };

		if (xioctl(DRM_IOCTL_WAIT_VBLANK, &v))
			return -1;
		last = v.reply.tval_sec * 1e6 + v.reply.tval_usec;
		if (!i)
			first = last;
	}
	buf_destroy(&src);
	buf_destroy(&wb);
	return (last - first) / n;
}

static const struct drm_mode_modeinfo *find(int w, int h, int refresh, int layout)
{
	unsigned int i;

	for (i = 0; i < n_modes; i++)
		if (modes[i].hdisplay == w && modes[i].vdisplay == h &&
		    modes[i].vrefresh == refresh && LAYOUT(&modes[i]) == layout &&
		    !(modes[i].flags & DRM_MODE_FLAG_INTERLACE) &&
		    modes[i].clock * 1000 % (modes[i].htotal * modes[i].vtotal) == 0)
			return &modes[i];
	return NULL;
}

static void check_list(const char *expect_path)
{
	char seen[64][48], want[64][48], line[96];
	int n_seen = 0, n_want = 0, i, j, missing = 0, extra = 0;
	unsigned int k;
	FILE *f;

	for (k = 0; k < n_modes; k++) {
		char s[48];

		format_name(&modes[k], s, sizeof(s));
		printf("STEREO|mode|%s|%s|%u kHz %u/%u %u/%u\n", dev_name, s, modes[k].clock,
		       modes[k].hdisplay, modes[k].htotal, modes[k].vdisplay, modes[k].vtotal);
		if (!LAYOUT(&modes[k]))
			continue;
		for (i = 0; i < n_seen && strcmp(seen[i], s); i++)
			;
		if (i == n_seen && n_seen < 64)
			strcpy(seen[n_seen++], s);
	}
	if (!expect_path) {
		check("stereo-formats", n_seen == 0, "%d stereo formats listed, none expected",
		      n_seen);
		return;
	}
	f = fopen(expect_path, "r");
	if (!f) {
		check("stereo-formats", false, "cannot open %s", expect_path);
		return;
	}
	while (fgets(line, sizeof(line), f) && n_want < 64) {
		line[strcspn(line, "\n")] = 0;
		if (line[0] && line[0] != '#')
			strcpy(want[n_want++], line);
	}
	fclose(f);
	for (i = 0; i < n_want; i++) {
		for (j = 0; j < n_seen && strcmp(want[i], seen[j]); j++)
			;
		if (j == n_seen) {
			missing++;
			printf("STEREO|info|%s|missing %s\n", dev_name, want[i]);
		}
	}
	for (j = 0; j < n_seen; j++) {
		for (i = 0; i < n_want && strcmp(want[i], seen[j]); i++)
			;
		if (i == n_want) {
			extra++;
			printf("STEREO|info|%s|unexpected %s\n", dev_name, seen[j]);
		}
	}
	check("stereo-formats", !missing && !extra,
	      "%d stereo formats listed, %d expected, %d missing, %d unexpected", n_seen, n_want,
	      missing, extra);
}

int main(int argc, char **argv)
{
	const char *expect = NULL;
	const struct drm_mode_modeinfo *fp, *flat;
	unsigned int i;
	int layouts_done = 0;

	if (argc < 2) {
		fprintf(stderr, "usage: %s CARD [--expect FILE] [--name NAME] [--out DIR]\n", argv[0]);
		return 2;
	}
	for (i = 2; i + 1 < (unsigned int)argc; i += 2) {
		if (!strcmp(argv[i], "--expect"))
			expect = argv[i + 1];
		else if (!strcmp(argv[i], "--name"))
			dev_name = argv[i + 1];
		else if (!strcmp(argv[i], "--out"))
			out_dir = argv[i + 1];
	}
	fd = open(argv[1], O_RDWR | O_CLOEXEC);
	if (fd < 0) {
		perror(argv[1]);
		return 2;
	}
	if (xioctl(DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_STEREO_3D, 1 }) ||
	    xioctl(DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_UNIVERSAL_PLANES, 1 }) ||
	    xioctl(DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_ATOMIC, 1 }) ||
	    xioctl(DRM_IOCTL_SET_CLIENT_CAP, &(struct drm_set_client_cap){ DRM_CLIENT_CAP_WRITEBACK_CONNECTORS, 1 })) {
		check("caps", false, "SET_CLIENT_CAP: %s", strerror(errno));
		return 1;
	}
	if (find_objects()) {
		check("objects", false, "connector, writeback connector or properties missing");
		return 1;
	}

	check_list(expect);

	for (i = 0; i < n_modes; i++) {
		int layout = LAYOUT(&modes[i]);

		if (!layout && !(modes[i].hdisplay == 1920 && modes[i].vdisplay == 1080))
			continue;
		test_packed(&modes[i], !(layouts_done & 1 << layout));
		if (layout && !(layouts_done & 1 << layout))
			test_planes(&modes[i]);
		layouts_done |= 1 << layout;
	}

	fp = find(1920, 1080, 24, FP);
	flat = find(1920, 1080, 24, 0);
	if (!flat)
		flat = find(1920, 1080, 60, 0);
	if (fp)
		test_refused(fp, fp->hdisplay, fp->vdisplay, "one eye");
	if (flat)
		test_refused(flat, flat->hdisplay, flat->vdisplay + flat->vtotal,
			     "a frame packing frame");
	if (fp && (flat = find(1920, 1080, 24, 0))) {
		double want = (double)fp->htotal * fp->vtotal * 1000 / fp->clock;
		double t_fp = vblank_period(fp, 24), t_2d = vblank_period(flat, 24);

		check("vblank-period", t_fp > 0 && t_2d > 0 && t_fp > want * 0.99 && t_fp < want * 1.01 &&
		      t_2d > want * 0.99 && t_2d < want * 1.01,
		      "1920x1080@24 frame packing %.1f us, 2D %.1f us, timing %.1f us", t_fp, t_2d, want);
	}

	printf("STEREO|summary|%s|%d checks, %d failed\n", dev_name, n_checks, n_failures);
	return n_failures ? 1 : 0;
}
