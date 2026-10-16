// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * depth-cam-test: checks the depth formats of vivid, the virtual video driver,
 * as a RealSense camera gives them through uvcvideo. Raw V4L2 ioctls.
 *
 *   depth-cam-test
 *
 * 1. vivid's capture node lists V4L2_PIX_FMT_Z16 (16-bit depth),
 *    V4L2_PIX_FMT_INZI (10-bit infrared, then 16-bit depth) and
 *    V4L2_PIX_FMT_CNF4 (4-bit confidence, two pixels a byte).
 * 2. With the "Gray Ramp" test pattern and no on-screen text, one frame of
 *    each, and of V4L2_PIX_FMT_Y16 as the reference, is read and one line
 *    compared pixel by pixel: Z16 equals Y16, INZI's depth plane equals Z16,
 *    its infrared plane is Z16's top byte shifted to 10 bits (as the pattern
 *    generator writes V4L2_PIX_FMT_Y10), CNF4 is the top
 *    four bits; the ramp rises from left to right.
 *
 * Results: "STEREO|check|<name>|PASS|<detail>" or FAIL lines on stdout.
 */
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include <linux/videodev2.h>

#define W 640
#define H 480
#define ROW 400

static int n_checks, n_failures;

static void check(const char *name, bool ok, const char *fmt, ...)
{
	char detail[256];
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(detail, sizeof(detail), fmt, ap);
	va_end(ap);
	printf("STEREO|check|depth-cam/%s|%s|%s\n", name, ok ? "PASS" : "FAIL", detail);
	n_checks++;
	n_failures += !ok;
}

static int open_vivid(void)
{
	char path[32];
	int i, fd;

	for (i = 0; i < 16; i++) {
		struct v4l2_capability cap = { 0 };

		snprintf(path, sizeof(path), "/dev/video%d", i);
		fd = open(path, O_RDWR);
		if (fd < 0)
			continue;
		if (!ioctl(fd, VIDIOC_QUERYCAP, &cap) && !strcmp((char *)cap.driver, "vivid") &&
		    (cap.device_caps & V4L2_CAP_VIDEO_CAPTURE) &&
		    (cap.device_caps & V4L2_CAP_READWRITE))
			return fd;
		close(fd);
	}
	return -1;
}

static bool listed(int fd, uint32_t fourcc)
{
	struct v4l2_fmtdesc d = { .type = V4L2_BUF_TYPE_VIDEO_CAPTURE };

	for (d.index = 0; !ioctl(fd, VIDIOC_ENUM_FMT, &d); d.index++)
		if (d.pixelformat == fourcc)
			return true;
	return false;
}

/* sets a menu control, found by its name, to the item of that name */
static bool set_menu(int fd, const char *ctrl, const char *item)
{
	struct v4l2_queryctrl q = { .id = V4L2_CTRL_FLAG_NEXT_CTRL };

	while (!ioctl(fd, VIDIOC_QUERYCTRL, &q)) {
		if (q.type == V4L2_CTRL_TYPE_MENU && !strcmp((char *)q.name, ctrl)) {
			struct v4l2_querymenu m = { .id = q.id };

			for (m.index = q.minimum; m.index <= (uint32_t)q.maximum; m.index++) {
				if (ioctl(fd, VIDIOC_QUERYMENU, &m) || strcmp((char *)m.name, item))
					continue;
				struct v4l2_control c = { .id = q.id, .value = m.index };

				return !ioctl(fd, VIDIOC_S_CTRL, &c);
			}
			return false;
		}
		q.id |= V4L2_CTRL_FLAG_NEXT_CTRL;
	}
	return false;
}

/*
 * One frame of @fourcc, on a node of its own (read() keeps the queue until
 * the file is closed); returns its size, the line pitch in @bpl.
 */
static ssize_t grab(uint32_t fourcc, uint8_t *buf, size_t size, uint32_t *bpl)
{
	struct v4l2_format f = { .type = V4L2_BUF_TYPE_VIDEO_CAPTURE };
	ssize_t n = -1;
	int tries, fd;

	fd = open_vivid();
	if (fd < 0)
		return -1;

	f.fmt.pix.width = W;
	f.fmt.pix.height = H;
	f.fmt.pix.pixelformat = fourcc;
	f.fmt.pix.field = V4L2_FIELD_NONE;
	if (ioctl(fd, VIDIOC_S_FMT, &f) || f.fmt.pix.pixelformat != fourcc ||
	    f.fmt.pix.width != W || f.fmt.pix.height != H || f.fmt.pix.sizeimage > size)
		goto out;
	*bpl = f.fmt.pix.bytesperline;
	/* the first frames can be from before the pattern changed */
	for (tries = 0; tries < 3; tries++) {
		n = read(fd, buf, f.fmt.pix.sizeimage);
		if (n != (ssize_t)f.fmt.pix.sizeimage) {
			n = -1;
			break;
		}
	}
out:
	close(fd);
	return n;
}

static unsigned int le16(const uint8_t *p)
{
	return p[0] | p[1] << 8;
}

int main(void)
{
	static uint8_t y16[W * H * 2], z16[W * H * 2], inzi[W * H * 4], cnf4[W * H];
	uint32_t bpl_y, bpl_z, bpl_i, bpl_c;
	long bad_z = 0, bad_ir = 0, bad_d = 0, bad_c = 0;
	int fd, x;

	fd = open_vivid();
	check("node", fd >= 0, "vivid capture node %s", fd >= 0 ? "found" : "missing");
	if (fd < 0)
		goto out;

	check("z16-listed", listed(fd, V4L2_PIX_FMT_Z16), "V4L2_PIX_FMT_Z16 in VIDIOC_ENUM_FMT");
	check("inzi-listed", listed(fd, V4L2_PIX_FMT_INZI), "V4L2_PIX_FMT_INZI in VIDIOC_ENUM_FMT");
	check("cnf4-listed", listed(fd, V4L2_PIX_FMT_CNF4), "V4L2_PIX_FMT_CNF4 in VIDIOC_ENUM_FMT");

	check("pattern", set_menu(fd, "Test Pattern", "Gray Ramp"), "Test Pattern: Gray Ramp");
	set_menu(fd, "OSD Text Mode", "None");

	close(fd);
	fd = -1;
	if (grab(V4L2_PIX_FMT_Y16, y16, sizeof(y16), &bpl_y) < 0 ||
	    grab(V4L2_PIX_FMT_Z16, z16, sizeof(z16), &bpl_z) < 0 ||
	    grab(V4L2_PIX_FMT_INZI, inzi, sizeof(inzi), &bpl_i) < 0 ||
	    grab(V4L2_PIX_FMT_CNF4, cnf4, sizeof(cnf4), &bpl_c) < 0) {
		check("frames", false, "could not read a %dx%d frame of each format: %s", W, H,
		      strerror(errno));
		goto out;
	}
	check("pitch", bpl_y == 2 * W && bpl_z == 2 * W && bpl_i == 2 * W && bpl_c == W / 2,
	      "bytes per line Y16 %u, Z16 %u, INZI %u per plane, CNF4 %u", bpl_y, bpl_z, bpl_i,
	      bpl_c);

	for (x = 0; x < W; x++) {
		unsigned int y = le16(&y16[ROW * bpl_y + 2 * x]);
		unsigned int z = le16(&z16[ROW * bpl_z + 2 * x]);
		unsigned int ir = le16(&inzi[ROW * bpl_i + 2 * x]);
		unsigned int d = le16(&inzi[H * bpl_i + ROW * bpl_i + 2 * x]);
		unsigned int c = cnf4[ROW * bpl_c + x / 2] >> (x & 1 ? 4 : 0) & 0xf;
		unsigned int top = z >> 8;

		bad_z += z != y;
		bad_d += d != z;
		bad_ir += ir != top << 2;	/* as the generator writes Y10 */
		bad_c += c != top >> 4;
	}
	check("z16", !bad_z, "line %d: Z16 equals Y16 at %ld of %d pixels", ROW, W - bad_z, W);
	check("inzi-depth", !bad_d, "line %d: INZI's depth plane equals Z16 at %ld of %d pixels",
	      ROW, W - bad_d, W);
	check("inzi-infrared", !bad_ir, "line %d: INZI's infrared plane is Z16's top byte shifted to 10 bits at %ld of %d pixels",
	      ROW, W - bad_ir, W);
	check("cnf4", !bad_c, "line %d: CNF4 is Z16's top four bits at %ld of %d pixels", ROW,
	      W - bad_c, W);
	check("ramp", le16(&z16[ROW * bpl_z]) < le16(&z16[ROW * bpl_z + 2 * (W - 1)]),
	      "depth at the left %u, at the right %u", le16(&z16[ROW * bpl_z]),
	      le16(&z16[ROW * bpl_z + 2 * (W - 1)]));
out:
	printf("STEREO|summary|depth-cam|%d checks, %d failed\n", n_checks, n_failures);
	return n_failures ? 1 : 0;
}
