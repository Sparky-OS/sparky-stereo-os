/* ORDER 471: does the dmabuf nvidia-vaapi-driver exports read back right in an EGL importer?
 *
 * Decodes frame N of an H.264/HEVC/VP9 file with ffmpeg through VA-API on one render node, exports the surface the way a browser
 * does (vaExportSurfaceHandle, DRM_PRIME_2, separate layers), imports each layer into EGL on the same node
 * (EGL_EXT_image_dma_buf_import_modifiers), samples it with GLES and prints the mean of each plane next to the software decode.
 *
 * mode "same":  the import runs in the process that decoded.
 * mode "child": the import runs in a forked child that opens the GPU only after the descriptors arrive over a socket (SCM_RIGHTS),
 *               as the browser's decoder process and compositor process are apart.
 *
 * cc -O1 -o dmabuf-import-probe dmabuf-import-probe.c $(pkg-config --cflags --libs libavformat libavcodec libavutil libva libva-drm egl glesv2)
 * dmabuf-import-probe FILE FRAME same|child /dev/dri/renderD129 [dump-prefix]
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>

#include <va/va.h>
#include <va/va_drmcommon.h>
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_vaapi.h>
#include <libavutil/imgutils.h>

#define EGL_EGLEXT_PROTOTYPES
#define GL_GLEXT_PROTOTYPES
#include <gbm.h>
#include <wayland-client.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <GLES2/gl2ext.h>

#define MAXOBJ 4
#define MAXLAY 4

struct plane_desc {
	uint32_t fourcc;
	uint32_t width, height;
	uint32_t object;
	uint32_t offset, pitch;
};
struct export_desc {
	uint32_t fourcc, width, height;
	uint32_t num_objects, num_layers;
	uint32_t size[MAXOBJ];
	uint64_t modifier[MAXOBJ];
	struct plane_desc layer[MAXLAY];
};
struct ref_stats {
	double y, u, v;
	double yc, uc, vc;
};

static void die(const char *msg)
{
	fprintf(stderr, "probe: %s\n", msg);
	exit(2);
}

static enum AVPixelFormat pick_vaapi(AVCodecContext *c, const enum AVPixelFormat *f)
{
	(void)c;
	for (; *f != AV_PIX_FMT_NONE; f++)
		if (*f == AV_PIX_FMT_VAAPI)
			return *f;
	return AV_PIX_FMT_NONE;
}

static double plane_mean(const uint8_t *p, int stride, int w, int h, double *centre)
{
	double s = 0;
	for (int y = 0; y < h; y++)
		for (int x = 0; x < w; x++)
			s += p[y * stride + x];
	double c = 0;
	int n = 0;
	for (int y = h / 4; y < 3 * h / 4; y++)
		for (int x = w / 4; x < 3 * w / 4; x++, n++)
			c += p[y * stride + x];
	*centre = c / n;
	return s / ((double)w * h);
}

/* software decode of frame N, for the reference means (yuv420p planes) */
static int software_reference(const char *file, int want, struct ref_stats *r, const char *dump)
{
	AVFormatContext *fc = NULL;
	if (avformat_open_input(&fc, file, NULL, NULL) < 0 || avformat_find_stream_info(fc, NULL) < 0)
		return -1;
	int vi = av_find_best_stream(fc, AVMEDIA_TYPE_VIDEO, -1, -1, NULL, 0);
	const AVCodec *dec = avcodec_find_decoder(fc->streams[vi]->codecpar->codec_id);
	AVCodecContext *cc = avcodec_alloc_context3(dec);
	avcodec_parameters_to_context(cc, fc->streams[vi]->codecpar);
	cc->thread_count = 1;
	if (avcodec_open2(cc, dec, NULL) < 0)
		return -1;
	AVPacket *pk = av_packet_alloc();
	AVFrame *fr = av_frame_alloc();
	int n = 0, got = 0;
	while (!got && av_read_frame(fc, pk) >= 0) {
		if (pk->stream_index == vi && avcodec_send_packet(cc, pk) >= 0)
			while (avcodec_receive_frame(cc, fr) >= 0) {
				if (n++ == want) {
					got = 1;
					break;
				}
			}
		av_packet_unref(pk);
	}
	if (!got)
		return -1;
	if (fr->format != AV_PIX_FMT_YUV420P && fr->format != AV_PIX_FMT_YUVJ420P) {
		fprintf(stderr, "probe: software frame is pixel format %d, only yuv420p is compared\n", fr->format);
		return -1;
	}
	r->y = plane_mean(fr->data[0], fr->linesize[0], fr->width, fr->height, &r->yc);
	r->u = plane_mean(fr->data[1], fr->linesize[1], fr->width / 2, fr->height / 2, &r->uc);
	r->v = plane_mean(fr->data[2], fr->linesize[2], fr->width / 2, fr->height / 2, &r->vc);
	if (dump) {
		char name[512];
		snprintf(name, sizeof name, "%s-sw-y.pgm", dump);
		FILE *f = fopen(name, "wb");
		fprintf(f, "P5\n%d %d\n255\n", fr->width, fr->height);
		for (int y = 0; y < fr->height; y++)
			fwrite(fr->data[0] + y * fr->linesize[0], 1, fr->width, f);
		fclose(f);
	}
	return 0;
}

static int send_fds(int sock, const void *data, size_t len, const int *fds, int nfds)
{
	struct iovec iov = {(void *)data, len};
	char cbuf[CMSG_SPACE(sizeof(int) * MAXOBJ)];
	memset(cbuf, 0, sizeof cbuf);
	struct msghdr m = {.msg_iov = &iov, .msg_iovlen = 1, .msg_control = cbuf, .msg_controllen = CMSG_SPACE(sizeof(int) * nfds)};
	struct cmsghdr *c = CMSG_FIRSTHDR(&m);
	c->cmsg_level = SOL_SOCKET;
	c->cmsg_type = SCM_RIGHTS;
	c->cmsg_len = CMSG_LEN(sizeof(int) * nfds);
	memcpy(CMSG_DATA(c), fds, sizeof(int) * nfds);
	return sendmsg(sock, &m, 0) < 0 ? -1 : 0;
}

static int recv_fds(int sock, void *data, size_t len, int *fds, int maxfds)
{
	struct iovec iov = {data, len};
	char cbuf[CMSG_SPACE(sizeof(int) * MAXOBJ)];
	struct msghdr m = {.msg_iov = &iov, .msg_iovlen = 1, .msg_control = cbuf, .msg_controllen = sizeof cbuf};
	if (recvmsg(sock, &m, 0) <= 0)
		return -1;
	int n = 0;
	for (struct cmsghdr *c = CMSG_FIRSTHDR(&m); c; c = CMSG_NXTHDR(&m, c))
		if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_RIGHTS) {
			n = (c->cmsg_len - CMSG_LEN(0)) / sizeof(int);
			if (n > maxfds)
				n = maxfds;
			memcpy(fds, CMSG_DATA(c), sizeof(int) * n);
		}
	return n;
}

static const char *vs_src = "#version 300 es\nout vec2 uv; void main(){ vec2 p = vec2((gl_VertexID<<1)&2, gl_VertexID&2); uv = p; gl_Position = vec4(p*2.0-1.0, 0.0, 1.0); }\n";
static const char *fs_src = "#version 300 es\nprecision highp float; in vec2 uv; uniform sampler2D t; out vec4 o; void main(){ o = texture(t, uv); }\n";

static GLuint make_prog(void)
{
	GLuint v = glCreateShader(GL_VERTEX_SHADER), f = glCreateShader(GL_FRAGMENT_SHADER), p = glCreateProgram();
	glShaderSource(v, 1, &vs_src, NULL);
	glCompileShader(v);
	glShaderSource(f, 1, &fs_src, NULL);
	glCompileShader(f);
	glAttachShader(p, v);
	glAttachShader(p, f);
	glLinkProgram(p);
	return p;
}

/* imports each layer, draws it, prints the mean of the channels. Returns 0 when every layer imported. */
static int import_and_measure(const struct export_desc *d, const int *fds, const char *node, const char *dump, const char *tag)
{
	int nodefd = open(node, O_RDWR | O_CLOEXEC);
	PFNEGLQUERYDEVICESEXTPROC qdev = (void *)eglGetProcAddress("eglQueryDevicesEXT");
	PFNEGLQUERYDEVICESTRINGEXTPROC qstr = (void *)eglGetProcAddress("eglQueryDeviceStringEXT");
	PFNEGLGETPLATFORMDISPLAYEXTPROC gpd = (void *)eglGetProcAddress("eglGetPlatformDisplayEXT");
	const char *plat = getenv("PROBE_PLATFORM");
	if (!plat)
		plat = "device";
	EGLDisplay dpy = EGL_NO_DISPLAY;
	if (!strcmp(plat, "gbm")) {
		struct gbm_device *gbm = gbm_create_device(nodefd);
		fprintf(stderr, "%s: gbm backend %s\n", tag, gbm ? gbm_device_get_backend_name(gbm) : "(none)");
		dpy = gbm ? gpd(EGL_PLATFORM_GBM_KHR, gbm, NULL) : EGL_NO_DISPLAY;
	} else if (!strcmp(plat, "wayland")) {
		struct wl_display *wd = wl_display_connect(NULL);
		fprintf(stderr, "%s: wayland display %p\n", tag, (void *)wd);
		dpy = wd ? (getenv("PROBE_LEGACY") ? eglGetDisplay((EGLNativeDisplayType)wd) : gpd(EGL_PLATFORM_WAYLAND_EXT, wd, NULL)) : EGL_NO_DISPLAY;
	} else {
		EGLDeviceEXT devs[16];
		EGLint nd = 0;
		if (qdev && qdev(16, devs, &nd)) {
			for (int i = 0; i < nd; i++) {
				const char *rn = qstr(devs[i], EGL_DRM_RENDER_NODE_FILE_EXT);
				fprintf(stderr, "%s: EGL device %d render node %s\n", tag, i, rn ? rn : "(none)");
				if (rn && !strcmp(rn, node))
					dpy = gpd(EGL_PLATFORM_DEVICE_EXT, devs[i], NULL);
			}
		}
	}
	if (dpy == EGL_NO_DISPLAY)
		die("no EGL display");
	EGLint maj, min;
	if (!eglInitialize(dpy, &maj, &min))
		die("eglInitialize");
	const char *ext = eglQueryString(dpy, EGL_EXTENSIONS);
	fprintf(stderr, "%s: EGL %d.%d vendor %s, dmabuf_import %d modifiers %d\n", tag, maj, min, eglQueryString(dpy, EGL_VENDOR),
		strstr(ext, "EGL_EXT_image_dma_buf_import") != NULL, strstr(ext, "EGL_EXT_image_dma_buf_import_modifiers") != NULL);
	eglBindAPI(EGL_OPENGL_ES_API);
	EGLint cattr[] = {EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE};
	EGLContext ctx = eglCreateContext(dpy, EGL_NO_CONFIG_KHR, EGL_NO_CONTEXT, cattr);
	if (ctx == EGL_NO_CONTEXT || !eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, ctx))
		die("context");
	fprintf(stderr, "%s: GL %s\n", tag, glGetString(GL_RENDERER));
	PFNEGLCREATEIMAGEKHRPROC cimg = (void *)eglGetProcAddress("eglCreateImageKHR");
	PFNGLEGLIMAGETARGETTEXTURE2DOESPROC target = (void *)eglGetProcAddress("glEGLImageTargetTexture2DOES");
	GLuint prog = make_prog();
	glUseProgram(prog);
	int bad = 0;
	for (uint32_t li = 0; li < d->num_layers; li++) {
		const struct plane_desc *l = &d->layer[li];
		int fd = fds[l->object];
		uint64_t mod = d->modifier[l->object];
		EGLint a[] = {EGL_WIDTH, (EGLint)l->width, EGL_HEIGHT, (EGLint)l->height, EGL_LINUX_DRM_FOURCC_EXT, (EGLint)l->fourcc,
			EGL_DMA_BUF_PLANE0_FD_EXT, fd, EGL_DMA_BUF_PLANE0_OFFSET_EXT, (EGLint)l->offset, EGL_DMA_BUF_PLANE0_PITCH_EXT, (EGLint)l->pitch,
			EGL_DMA_BUF_PLANE0_MODIFIER_LO_EXT, (EGLint)(mod & 0xffffffff), EGL_DMA_BUF_PLANE0_MODIFIER_HI_EXT, (EGLint)(mod >> 32), EGL_NONE};
		EGLImageKHR img = cimg(dpy, EGL_NO_CONTEXT, EGL_LINUX_DMA_BUF_EXT, NULL, a);
		fprintf(stderr, "%s: layer %u fourcc %.4s %ux%u offset %u pitch %u modifier 0x%llx -> image %s (egl error 0x%x)\n", tag, li,
			(const char *)&l->fourcc, l->width, l->height, l->offset, l->pitch, (unsigned long long)mod, img ? "ok" : "FAILED", eglGetError());
		if (!img) {
			bad = 1;
			continue;
		}
		GLuint tex, fbo, out;
		glGenTextures(1, &tex);
		glBindTexture(GL_TEXTURE_2D, tex);
		target(GL_TEXTURE_2D, img);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
		glGenTextures(1, &out);
		glBindTexture(GL_TEXTURE_2D, out);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, l->width, l->height, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
		glGenFramebuffers(1, &fbo);
		glBindFramebuffer(GL_FRAMEBUFFER, fbo);
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, out, 0);
		glViewport(0, 0, l->width, l->height);
		glActiveTexture(GL_TEXTURE0);
		glBindTexture(GL_TEXTURE_2D, tex);
		glUniform1i(glGetUniformLocation(prog, "t"), 0);
		glDrawArrays(GL_TRIANGLES, 0, 3);
		uint8_t *px = malloc((size_t)l->width * l->height * 4);
		glReadPixels(0, 0, l->width, l->height, GL_RGBA, GL_UNSIGNED_BYTE, px);
		double s0 = 0, s1 = 0, c0 = 0, c1 = 0;
		long n = (long)l->width * l->height, nc = 0;
		for (long i = 0; i < n; i++) {
			s0 += px[i * 4];
			s1 += px[i * 4 + 1];
		}
		for (uint32_t y = l->height / 4; y < 3 * l->height / 4; y++)
			for (uint32_t x = l->width / 4; x < 3 * l->width / 4; x++, nc++) {
				c0 += px[((long)y * l->width + x) * 4];
				c1 += px[((long)y * l->width + x) * 4 + 1];
			}
		printf("%s layer %u (%.4s %ux%u): mean r %.2f g %.2f, centre r %.2f g %.2f, GL error 0x%x\n", tag, li, (const char *)&l->fourcc, l->width, l->height,
			s0 / n, s1 / n, c0 / nc, c1 / nc, glGetError());
		if (dump) {
			char name[512];
			snprintf(name, sizeof name, "%s-%s-layer%u.ppm", dump, tag, li);
			FILE *f = fopen(name, "wb");
			fprintf(f, "P6\n%u %u\n255\n", l->width, l->height);
			for (uint32_t y = 0; y < l->height; y++)
				for (uint32_t x = 0; x < l->width; x++) {
					uint8_t *q = px + (((long)(l->height - 1 - y)) * l->width + x) * 4;
					fputc(q[0], f);
					fputc(l->fourcc == 0x38384752 ? q[1] : q[0], f);
					fputc(l->fourcc == 0x38384752 ? 0 : q[0], f);
				}
			fclose(f);
		}
		free(px);
	}
	close(nodefd);
	return bad;
}

struct cached {
	VASurfaceID surf;
	struct export_desc d;
	int fds[MAXOBJ];
};
static struct cached cache[64];
static int ncache;

static int export_surface(VADisplay vd, VASurfaceID surf, struct export_desc *d, int *fds)
{
	VADRMPRIMESurfaceDescriptor vdesc;
	VAStatus st = vaExportSurfaceHandle(vd, surf, VA_SURFACE_ATTRIB_MEM_TYPE_DRM_PRIME_2, VA_EXPORT_SURFACE_READ_ONLY | VA_EXPORT_SURFACE_SEPARATE_LAYERS, &vdesc);
	if (st != VA_STATUS_SUCCESS)
		return -1;
	memset(d, 0, sizeof *d);
	d->fourcc = vdesc.fourcc;
	d->width = vdesc.width;
	d->height = vdesc.height;
	d->num_objects = vdesc.num_objects;
	d->num_layers = vdesc.num_layers;
	for (uint32_t i = 0; i < vdesc.num_objects; i++) {
		d->size[i] = vdesc.objects[i].size;
		d->modifier[i] = vdesc.objects[i].drm_format_modifier;
		fds[i] = vdesc.objects[i].fd;
	}
	for (uint32_t i = 0; i < vdesc.num_layers; i++) {
		d->layer[i].fourcc = vdesc.layers[i].drm_format;
		d->layer[i].object = vdesc.layers[i].object_index[0];
		d->layer[i].offset = vdesc.layers[i].offset[0];
		d->layer[i].pitch = vdesc.layers[i].pitch[0];
		d->layer[i].width = i == 0 ? d->width : d->width / 2;
		d->layer[i].height = i == 0 ? d->height : d->height / 2;
	}
	return 0;
}

int main(int argc, char **argv)
{
	if (argc < 5)
		die("usage: FILE FRAME same|child NODE [dump-prefix]");
	const char *file = argv[1], *node = argv[4], *dump = argc > 5 ? argv[5] : NULL;
	int want = atoi(argv[2]), child_mode = !strcmp(argv[3], "child");
	int sp[2] = {-1, -1};
	pid_t kid = 0;
	if (child_mode) {
		if (socketpair(AF_UNIX, SOCK_STREAM, 0, sp))
			die("socketpair");
		kid = fork();
		if (kid == 0) {
			close(sp[0]);
			struct export_desc d;
			int fds[MAXOBJ];
			int n = recv_fds(sp[1], &d, sizeof d, fds, MAXOBJ);
			if (n < 1)
				_exit(3);
			int bad = import_and_measure(&d, fds, node, dump, "child");
			fflush(stdout);
			_exit(bad ? 4 : 0);
		}
		close(sp[1]);
	}

	struct ref_stats ref = {0};
	if (software_reference(file, want, &ref, dump))
		die("software reference failed");
	printf("software frame %d: mean Y %.2f U %.2f V %.2f, centre Y %.2f U %.2f V %.2f\n", want, ref.y, ref.u, ref.v, ref.yc, ref.uc, ref.vc);

	AVFormatContext *fc = NULL;
	if (avformat_open_input(&fc, file, NULL, NULL) < 0 || avformat_find_stream_info(fc, NULL) < 0)
		die("open");
	int vi = av_find_best_stream(fc, AVMEDIA_TYPE_VIDEO, -1, -1, NULL, 0);
	const AVCodec *dec = avcodec_find_decoder(fc->streams[vi]->codecpar->codec_id);
	AVCodecContext *cc = avcodec_alloc_context3(dec);
	avcodec_parameters_to_context(cc, fc->streams[vi]->codecpar);
	AVBufferRef *hw = NULL;
	char *odev = getenv("LIBVA_DRIVER_NAME");
	(void)odev;
	if (av_hwdevice_ctx_create(&hw, AV_HWDEVICE_TYPE_VAAPI, node, NULL, 0) < 0)
		die("vaapi device");
	cc->hw_device_ctx = av_buffer_ref(hw);
	cc->get_format = pick_vaapi;
	cc->thread_count = 1;
	if (avcodec_open2(cc, dec, NULL) < 0)
		die("open decoder");
	AVPacket *pk = av_packet_alloc();
	AVFrame *fr = av_frame_alloc();
	int n = 0, got = 0, reuse = getenv("PROBE_REUSE") != NULL;
	while (!got && av_read_frame(fc, pk) >= 0) {
		if (pk->stream_index == vi && avcodec_send_packet(cc, pk) >= 0)
			while (avcodec_receive_frame(cc, fr) >= 0) {
				if (reuse && fr->format == AV_PIX_FMT_VAAPI && n < want) {
					VASurfaceID sid = (VASurfaceID)(uintptr_t)fr->data[3];
					VADisplay vdd = ((AVVAAPIDeviceContext *)((AVHWDeviceContext *)hw->data)->hwctx)->display;
					int seen = 0;
					for (int i = 0; i < ncache; i++)
						seen |= cache[i].surf == sid;
					if (!seen && ncache < 64) {
						cache[ncache].surf = sid;
						if (!export_surface(vdd, sid, &cache[ncache].d, cache[ncache].fds))
							ncache++;
						vaSyncSurface(vdd, sid);
					}
				}
				if (n++ == want) {
					got = 1;
					break;
				}
				av_frame_unref(fr);
			}
		av_packet_unref(pk);
	}
	if (!got || fr->format != AV_PIX_FMT_VAAPI)
		die("no hardware frame");
	VASurfaceID surf = (VASurfaceID)(uintptr_t)fr->data[3];
	AVHWDeviceContext *dc = (AVHWDeviceContext *)hw->data;
	VADisplay vd = ((AVVAAPIDeviceContext *)dc->hwctx)->display;
	/* PROBE_EXPORT_BEFORE_SYNC=1 exports first and syncs after, the order Gecko's GetVAAPISurfaceDescriptor() uses */
	int before = getenv("PROBE_EXPORT_BEFORE_SYNC") != NULL;
	VAStatus st = VA_STATUS_SUCCESS;
	if (!before)
		st = vaSyncSurface(vd, surf);
	printf("hardware frame %d: surface %u, %s sync %s\n", want, surf, before ? "no" : "first,", vaErrorStr(st));
	struct export_desc d;
	int fds[MAXOBJ];
	int cached_export = 0;
	if (reuse)
		for (int i = 0; i < ncache; i++)
			if (cache[i].surf == surf) {
				d = cache[i].d;
				memcpy(fds, cache[i].fds, sizeof fds);
				cached_export = 1;
			}
	printf("%s\n", cached_export ? "using the export made when this surface was first seen (a recycled surface, as Gecko's frame pool does)" : "fresh export");
	if (!cached_export && export_surface(vd, surf, &d, fds))
		die("export");
	if (before) {
		st = vaSyncSurface(vd, surf);
		printf("sync after the export: %s\n", vaErrorStr(st));
	}
	printf("export: fourcc %.4s %ux%u, %u object(s), %u layer(s)\n", (const char *)&d.fourcc, d.width, d.height, d.num_objects, d.num_layers);
	for (uint32_t i = 0; i < d.num_layers; i++)
		printf("  layer %u: %.4s object %u offset %u pitch %u\n", i, (const char *)&d.layer[i].fourcc, d.layer[i].object, d.layer[i].offset, d.layer[i].pitch);
	for (uint32_t i = 0; i < d.num_objects; i++)
		printf("  object %u: size %u modifier 0x%llx\n", i, d.size[i], (unsigned long long)d.modifier[i]);
	int bad = 0;
	if (child_mode) {
		if (send_fds(sp[0], &d, sizeof d, fds, d.num_objects))
			die("send");
		int status = 0;
		waitpid(kid, &status, 0);
		bad = WIFEXITED(status) ? WEXITSTATUS(status) : 9;
		printf("child exit %d\n", bad);
	} else {
		bad = import_and_measure(&d, fds, node, dump, "same");
	}
	return bad;
}
