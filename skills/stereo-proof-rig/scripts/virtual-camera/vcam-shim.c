// A virtual V4L2 camera for the rig, in user space: preload it and /dev/videoN opens a fake descriptor whose V4L2 ioctls
// this file answers, with the kernel's own structures (linux/videodev2.h). No module, no device node, no real camera.
// The camera is described by $VCAM_ROOT/videoN.cfg; removing the file is unplugging the camera, and a plugged camera starts at
// its defaults (the values live in $VCAM_ROOT/videoN.state, which a test removes to replug). Every mode and control set by any
// process is appended to $VCAM_ROOT/videoN.log with the process name, so a test reads what a program asked the camera for.
// Build: cc -shared -fPIC -O1 -o vcam-shim.so vcam-shim.c -ldl
//
// videoN.cfg, one line each:
//   card TEXT | bus TEXT | busy (set-format answers EBUSY: another program streams)
//   format FOURCC DESCRIPTION            the formats in the driver's order; MJPG is flagged compressed
//   size WxH [R1,R2,...]                 a size of the last format, its frame rates (the format's "rate" lines when none)
//   rate R                               a frame rate of the last format
//   ctrl NAME TYPE MIN MAX STEP DEFAULT [OPTION...] [MENUITEM...]
//     TYPE: int bool menu button int64 u8 (u8 is an array: HAS_PAYLOAD)
//     OPTION: id=0xHEX (else a standard name gets the kernel's id, others a private one), value=N (the reading at plug-in),
//       refuse (every set answers ERANGE), clamp (an integer out of range is clamped and rounded as uvcvideo does, not refused),
//       inactive readonly writeonly volatile update slider grabbed exec layout dynarray whichminmax disabled (the V4L2 flag),
//       master=NAME:MANUAL (inactive while NAME is not MANUAL; a set then answers EACCES, as uvc_ctrl_is_accessible),
//       auto=N (the reading while inactive under its master: the value the automatic mode chose; it moves by itself)
// $VCAM_ROOT/videoN.gone makes the camera answer ENODEV to every ioctl but QUERYCAP (going away or still starting)
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#define MAXFD 64
#define MAXCTRL 48
#define MAXFMT 8
#define MAXSIZE 12

struct ctrl {
    char name[64];
    __u32 id;
    int type;
    int min, max, step, def, flags;
    char menu[8][48];
    int nmenu;
    int refuse; // the driver answers ERANGE to every set
    int clamp; // out of range: clamped like uvcvideo's uvc_ctrl_clamp
    char master[64];
    int manual; // the master's value that makes this control active
    int hasauto, autoval;
    int value;
};
struct fmt {
    __u32 fourcc;
    char desc[32];
    int nsizes;
    int w[MAXSIZE], h[MAXSIZE];
    int srates[MAXSIZE][6], nsrates[MAXSIZE];
    int nrates;
    int rates[6];
};
struct dev {
    int fd;
    int num;
    char card[64], bus[64];
    int busy; // another program holds the stream: set-format answers EBUSY
    struct fmt fmts[MAXFMT];
    int nfmts;
    struct ctrl ctrls[MAXCTRL];
    int nctrls;
    __u32 curfmt, curw, curh;
    int fps;
    unsigned reads;
};
static struct dev devs[MAXFD];
static int ndevs;

static int (*real_open)(const char *, int, ...);
static int (*real_ioctl)(int, unsigned long, ...);
static int (*real_close)(int);

static __u32 cc(const char *s) { return s[0] | s[1] << 8 | s[2] << 16 | (__u32)s[3] << 24; }

static void statepath(int num, char *out, size_t n) { snprintf(out, n, "%s/video%d.state", getenv("VCAM_ROOT"), num); }

static void logline(struct dev *d, const char *fmt, ...)
{
    char p[512], comm[64] = "?";
    snprintf(p, sizeof p, "%s/video%d.log", getenv("VCAM_ROOT"), d->num);
    FILE *c = fopen("/proc/self/comm", "r");
    if (c) {
        if (fgets(comm, sizeof comm, c))
            comm[strcspn(comm, "\n")] = 0;
        fclose(c);
    }
    FILE *f = fopen(p, "a");
    if (!f)
        return;
    fprintf(f, "%s %d ", comm, (int)getpid());
    va_list ap;
    va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);
    fputc('\n', f);
    fclose(f);
}

static void save_state(struct dev *d)
{
    char p[512];
    statepath(d->num, p, sizeof p);
    FILE *f = fopen(p, "w");
    if (!f)
        return;
    for (int i = 0; i < d->nctrls; i++)
        fprintf(f, "ctrl %s %d\n", d->ctrls[i].name, d->ctrls[i].value);
    fprintf(f, "fmt %u %u %u %d\n", d->curfmt, d->curw, d->curh, d->fps);
    fclose(f);
}

static const struct {
    const char *name;
    __u32 id;
} standard[] = {
    {"brightness", V4L2_CID_BRIGHTNESS}, {"contrast", V4L2_CID_CONTRAST}, {"saturation", V4L2_CID_SATURATION}, {"hue", V4L2_CID_HUE},
    {"auto_exposure", V4L2_CID_EXPOSURE_AUTO}, {"white_balance_automatic", V4L2_CID_AUTO_WHITE_BALANCE}, {"gamma", V4L2_CID_GAMMA},
    {"sharpness", V4L2_CID_SHARPNESS}, {"exposure_time_absolute", V4L2_CID_EXPOSURE_ABSOLUTE}, {"power_line_frequency", V4L2_CID_POWER_LINE_FREQUENCY},
    {"white_balance_temperature", V4L2_CID_WHITE_BALANCE_TEMPERATURE}, {"exposure_dynamic_framerate", V4L2_CID_EXPOSURE_AUTO_PRIORITY},
    {"gain", V4L2_CID_GAIN}, {"backlight_compensation", V4L2_CID_BACKLIGHT_COMPENSATION}, {"rotate", V4L2_CID_ROTATE},
    {"focus_absolute", V4L2_CID_FOCUS_ABSOLUTE}, {"focus_automatic_continuous", V4L2_CID_FOCUS_AUTO}, {"focus_relative", V4L2_CID_FOCUS_RELATIVE},
    {"pan_relative", V4L2_CID_PAN_RELATIVE}, {"tilt_relative", V4L2_CID_TILT_RELATIVE}, {"zoom_relative", V4L2_CID_ZOOM_RELATIVE},
    {"iris_relative", V4L2_CID_IRIS_RELATIVE}, {"zoom_continuous", V4L2_CID_ZOOM_CONTINUOUS}, {"pan_speed", V4L2_CID_PAN_SPEED},
    {"tilt_speed", V4L2_CID_TILT_SPEED}, {"pan_reset", V4L2_CID_PAN_RESET}, {"do_white_balance", V4L2_CID_DO_WHITE_BALANCE},
};

static void parse_rates(const char *s, int *out, int *n)
{
    *n = 0;
    char buf[64];
    snprintf(buf, sizeof buf, "%s", s);
    for (char *t = strtok(buf, ","); t && *n < 6; t = strtok(NULL, ","))
        out[(*n)++] = atoi(t);
}

static int load_cfg(struct dev *d, const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f)
        return -1;
    char line[512];
    struct fmt *cf = NULL;
    while (fgets(line, sizeof line, f)) {
        line[strcspn(line, "\n")] = 0;
        char *save = NULL;
        char *a = strtok_r(line, " ", &save);
        if (!a || a[0] == '#')
            continue;
        if (!strcmp(a, "card")) snprintf(d->card, sizeof d->card, "%.63s", line + 5);
        else if (!strcmp(a, "bus")) snprintf(d->bus, sizeof d->bus, "%.63s", line + 4);
        else if (!strcmp(a, "busy")) d->busy = 1;
        else if (!strcmp(a, "format") && d->nfmts < MAXFMT) {
            cf = &d->fmts[d->nfmts++];
            memset(cf, 0, sizeof *cf);
            cf->fourcc = cc(strtok_r(NULL, " ", &save));
            snprintf(cf->desc, sizeof cf->desc, "%s", strtok_r(NULL, " ", &save));
        } else if (!strcmp(a, "size") && cf && cf->nsizes < MAXSIZE) {
            sscanf(strtok_r(NULL, " ", &save), "%dx%d", &cf->w[cf->nsizes], &cf->h[cf->nsizes]);
            const char *r = strtok_r(NULL, " ", &save);
            if (r) parse_rates(r, cf->srates[cf->nsizes], &cf->nsrates[cf->nsizes]);
            cf->nsizes++;
        } else if (!strcmp(a, "rate") && cf && cf->nrates < 6) cf->rates[cf->nrates++] = atoi(strtok_r(NULL, " ", &save));
        else if (!strcmp(a, "ctrl") && d->nctrls < MAXCTRL) {
            struct ctrl *c = &d->ctrls[d->nctrls];
            memset(c, 0, sizeof *c);
            snprintf(c->name, sizeof c->name, "%s", strtok_r(NULL, " ", &save));
            char *t = strtok_r(NULL, " ", &save);
            c->type = !strcmp(t, "int") ? V4L2_CTRL_TYPE_INTEGER : !strcmp(t, "bool") ? V4L2_CTRL_TYPE_BOOLEAN
                : !strcmp(t, "menu") ? V4L2_CTRL_TYPE_MENU : !strcmp(t, "int64") ? V4L2_CTRL_TYPE_INTEGER64
                : !strcmp(t, "u8") ? V4L2_CTRL_TYPE_U8 : V4L2_CTRL_TYPE_BUTTON;
            c->min = atoi(strtok_r(NULL, " ", &save));
            c->max = atoi(strtok_r(NULL, " ", &save));
            c->step = atoi(strtok_r(NULL, " ", &save));
            c->def = c->value = atoi(strtok_r(NULL, " ", &save));
            if (c->type == V4L2_CTRL_TYPE_BUTTON) c->flags |= V4L2_CTRL_FLAG_WRITE_ONLY | V4L2_CTRL_FLAG_EXECUTE_ON_WRITE;
            if (c->type == V4L2_CTRL_TYPE_U8) c->flags |= V4L2_CTRL_FLAG_HAS_PAYLOAD;
            c->id = V4L2_CID_USER_BASE + 0x1000 + d->nctrls; // a private id
            for (unsigned k = 0; k < sizeof standard / sizeof *standard; k++)
                if (!strcmp(c->name, standard[k].name)) c->id = standard[k].id;
            for (char *o; (o = strtok_r(NULL, " ", &save));) {
                if (!strncmp(o, "id=", 3)) c->id = strtoul(o + 3, NULL, 0);
                else if (!strncmp(o, "value=", 6)) c->value = atoi(o + 6);
                else if (!strncmp(o, "auto=", 5)) { c->hasauto = 1; c->autoval = atoi(o + 5); }
                else if (!strncmp(o, "master=", 7)) {
                    char *colon = strchr(o + 7, ':');
                    if (colon) { *colon = 0; c->manual = atoi(colon + 1); }
                    snprintf(c->master, sizeof c->master, "%s", o + 7);
                }
                else if (!strcmp(o, "refuse")) c->refuse = 1;
                else if (!strcmp(o, "clamp")) c->clamp = 1;
                else if (!strcmp(o, "inactive")) c->flags |= V4L2_CTRL_FLAG_INACTIVE;
                else if (!strcmp(o, "readonly")) c->flags |= V4L2_CTRL_FLAG_READ_ONLY;
                else if (!strcmp(o, "writeonly")) c->flags |= V4L2_CTRL_FLAG_WRITE_ONLY;
                else if (!strcmp(o, "volatile")) c->flags |= V4L2_CTRL_FLAG_VOLATILE;
                else if (!strcmp(o, "update")) c->flags |= V4L2_CTRL_FLAG_UPDATE;
                else if (!strcmp(o, "slider")) c->flags |= V4L2_CTRL_FLAG_SLIDER;
                else if (!strcmp(o, "grabbed")) c->flags |= V4L2_CTRL_FLAG_GRABBED;
                else if (!strcmp(o, "exec")) c->flags |= V4L2_CTRL_FLAG_EXECUTE_ON_WRITE;
                else if (!strcmp(o, "layout")) c->flags |= V4L2_CTRL_FLAG_MODIFY_LAYOUT;
                else if (!strcmp(o, "dynarray")) c->flags |= V4L2_CTRL_FLAG_DYNAMIC_ARRAY | V4L2_CTRL_FLAG_HAS_PAYLOAD;
                else if (!strcmp(o, "whichminmax")) c->flags |= V4L2_CTRL_FLAG_HAS_WHICH_MIN_MAX;
                else if (!strcmp(o, "disabled")) c->flags |= V4L2_CTRL_FLAG_DISABLED;
                else if (c->nmenu < 8) snprintf(c->menu[c->nmenu++], 48, "%s", o);
            }
            d->nctrls++;
        }
    }
    fclose(f);
    d->curfmt = d->fmts[0].fourcc;
    d->curw = d->fmts[0].w[0];
    d->curh = d->fmts[0].h[0];
    d->fps = d->fmts[0].nsrates[0] ? d->fmts[0].srates[0][0] : d->fmts[0].rates[0];
    return 0;
}

static void init(void)
{
    if (!real_open) {
        real_open = dlsym(RTLD_NEXT, "open");
        real_ioctl = dlsym(RTLD_NEXT, "ioctl");
        real_close = dlsym(RTLD_NEXT, "close");
    }
}

static struct dev *find(int fd)
{
    for (int i = 0; i < ndevs; i++)
        if (devs[i].fd == fd)
            return &devs[i];
    return NULL;
}

static void load_state(struct dev *d)
{
    char sp[512];
    statepath(d->num, sp, sizeof sp);
    FILE *f = fopen(sp, "r");
    if (!f)
        return;
    char l[256], n[64];
    int v;
    while (fgets(l, sizeof l, f)) {
        if (sscanf(l, "ctrl %63s %d", n, &v) == 2)
            for (int i = 0; i < d->nctrls; i++)
                if (!strcmp(d->ctrls[i].name, n)) d->ctrls[i].value = v;
        unsigned a, b, c2;
        int r;
        if (sscanf(l, "fmt %u %u %u %d", &a, &b, &c2, &r) == 4) { d->curfmt = a; d->curw = b; d->curh = c2; d->fps = r; }
    }
    fclose(f);
}

static int vopen(const char *path, int flags, int mode, int *handled)
{
    init();
    int num;
    const char *root = getenv("VCAM_ROOT");
    if (!root || sscanf(path, "/dev/video%d", &num) != 1) {
        *handled = 0;
        return -1;
    }
    *handled = 1;
    if (getenv("VCAM_TRACE")) fprintf(stderr, "vcam: open %s\n", path);
    char cfg[512];
    snprintf(cfg, sizeof cfg, "%s/video%d.cfg", root, num);
    if (access(cfg, R_OK) != 0) {
        errno = ENOENT;
        return -1;
    }
    int fd = real_open("/dev/null", O_RDWR);
    struct dev *d = NULL;
    for (int i = 0; i < ndevs; i++)
        if (devs[i].fd < 0) {
            d = &devs[i];
            break;
        }
    if (!d && ndevs < MAXFD)
        d = &devs[ndevs++];
    if (!d) {
        real_close(fd);
        errno = EMFILE;
        return -1;
    }
    memset(d, 0, sizeof *d);
    d->fd = fd;
    d->num = num;
    load_cfg(d, cfg);
    load_state(d);
    (void)flags; (void)mode;
    return fd;
}

int open(const char *path, int flags, ...)
{
    va_list ap;
    va_start(ap, flags);
    int mode = ((flags & O_CREAT) || (flags & O_TMPFILE) == O_TMPFILE) ? va_arg(ap, int) : 0;
    va_end(ap);
    int handled;
    int fd = vopen(path, flags, mode, &handled);
    if (handled)
        return fd;
    return real_open(path, flags, mode);
}
int open64(const char *path, int flags, ...) __attribute__((alias("open")));
// A program built with _FORTIFY_SOURCE (Debian's hardening: Qt's V4L2 plugin) calls open(path, O_RDONLY) as __open_2
int __open_2(const char *path, int flags) { return open(path, flags); }
int __open64_2(const char *path, int flags) { return open(path, flags); }

int close(int fd)
{
    init();
    struct dev *d = find(fd);
    if (d)
        d->fd = -1;
    return real_close(fd);
}

static struct ctrl *byid(struct dev *d, __u32 id)
{
    for (int i = 0; i < d->nctrls; i++)
        if (d->ctrls[i].id == id) return &d->ctrls[i];
    return NULL;
}

static struct ctrl *byname(struct dev *d, const char *name)
{
    for (int i = 0; i < d->nctrls; i++)
        if (!strcmp(d->ctrls[i].name, name)) return &d->ctrls[i];
    return NULL;
}

// whether a control is inactive now: its static flag, or its master not in the manual value (uvcvideo's master/slave mappings)
static int inactive_now(struct dev *d, struct ctrl *c)
{
    if (c->flags & V4L2_CTRL_FLAG_INACTIVE)
        return 1;
    struct ctrl *m = c->master[0] ? byname(d, c->master) : NULL;
    return m && m->value != c->manual;
}

static int rates_of(struct dev *d, __u32 fourcc, __u32 w, __u32 h, const int **out)
{
    for (int i = 0; i < d->nfmts; i++)
        if (d->fmts[i].fourcc == fourcc)
            for (int s = 0; s < d->fmts[i].nsizes; s++)
                if ((int)w == d->fmts[i].w[s] && (int)h == d->fmts[i].h[s]) {
                    if (d->fmts[i].nsrates[s]) { *out = d->fmts[i].srates[s]; return d->fmts[i].nsrates[s]; }
                    *out = d->fmts[i].rates;
                    return d->fmts[i].nrates;
                }
    return 0;
}

int ioctl(int fd, unsigned long req, ...)
{
    init();
    // Qt declares the request as int (xioctl(int, int, void *)): the sign-extended 0x80685600 must still be VIDIOC_QUERYCAP
    if (req > 0xffffffffUL && (req >> 32) == 0xffffffffUL)
        req &= 0xffffffffUL;
    va_list ap;
    va_start(ap, req);
    void *arg = va_arg(ap, void *);
    va_end(ap);
    struct dev *d = find(fd);
    if (getenv("VCAM_TRACE") && d) fprintf(stderr, "vcam: ioctl %lx\n", req);
    if (!d)
        return real_ioctl(fd, req, arg);
    // $VCAM_ROOT/videoN.gone: the camera is going away or still starting (a USB reset): it opens and answers QUERYCAP, and every
    // other ioctl answers ENODEV, as uvcvideo does for a device marked disconnected
    char gone[512];
    snprintf(gone, sizeof gone, "%s/video%d.gone", getenv("VCAM_ROOT"), d->num);
    if (req != VIDIOC_QUERYCAP && access(gone, F_OK) == 0) {
        errno = ENODEV;
        return -1;
    }
    switch (req) {
    case VIDIOC_QUERYCAP: {
        struct v4l2_capability *c = arg;
        memset(c, 0, sizeof *c);
        snprintf((char *)c->driver, sizeof c->driver, "uvcvideo");
        snprintf((char *)c->card, sizeof c->card, "%.31s", d->card);
        snprintf((char *)c->bus_info, sizeof c->bus_info, "%.31s", d->bus);
        c->version = 0x070304;
        c->capabilities = V4L2_CAP_VIDEO_CAPTURE | V4L2_CAP_STREAMING | V4L2_CAP_DEVICE_CAPS;
        c->device_caps = V4L2_CAP_VIDEO_CAPTURE | V4L2_CAP_STREAMING;
        return 0;
    }
    case VIDIOC_ENUM_FMT: {
        struct v4l2_fmtdesc *f = arg;
        if (f->type != V4L2_BUF_TYPE_VIDEO_CAPTURE || (int)f->index >= d->nfmts) { errno = EINVAL; return -1; }
        f->pixelformat = d->fmts[f->index].fourcc;
        f->flags = d->fmts[f->index].fourcc == cc("MJPG") ? V4L2_FMT_FLAG_COMPRESSED : 0;
        snprintf((char *)f->description, sizeof f->description, "%s", d->fmts[f->index].desc);
        return 0;
    }
    case VIDIOC_ENUM_FRAMESIZES: {
        struct v4l2_frmsizeenum *s = arg;
        for (int i = 0; i < d->nfmts; i++)
            if (d->fmts[i].fourcc == s->pixel_format) {
                if ((int)s->index >= d->fmts[i].nsizes) { errno = EINVAL; return -1; }
                s->type = V4L2_FRMSIZE_TYPE_DISCRETE;
                s->discrete.width = d->fmts[i].w[s->index];
                s->discrete.height = d->fmts[i].h[s->index];
                return 0;
            }
        errno = EINVAL;
        return -1;
    }
    case VIDIOC_ENUM_FRAMEINTERVALS: {
        struct v4l2_frmivalenum *s = arg;
        const int *rates = NULL;
        int n = rates_of(d, s->pixel_format, s->width, s->height, &rates);
        if ((int)s->index >= n) { errno = EINVAL; return -1; }
        s->type = V4L2_FRMIVAL_TYPE_DISCRETE;
        s->discrete.numerator = 1;
        s->discrete.denominator = rates[s->index];
        return 0;
    }
    case VIDIOC_G_FMT: {
        struct v4l2_format *f = arg;
        f->fmt.pix.width = d->curw; f->fmt.pix.height = d->curh; f->fmt.pix.pixelformat = d->curfmt;
        f->fmt.pix.field = V4L2_FIELD_NONE;
        f->fmt.pix.bytesperline = d->curw * 2;
        f->fmt.pix.sizeimage = d->curw * d->curh * 2;
        return 0;
    }
    case VIDIOC_TRY_FMT:
    case VIDIOC_S_FMT: {
        struct v4l2_format *f = arg;
        if (req == VIDIOC_S_FMT && d->busy) { errno = EBUSY; return -1; }
        int fi = -1;
        for (int i = 0; i < d->nfmts; i++)
            if (d->fmts[i].fourcc == f->fmt.pix.pixelformat) fi = i;
        if (req == VIDIOC_TRY_FMT) {
            // a driver adjusts what it is asked for: an unknown format to its first, a size to the nearest it has
            if (fi < 0) fi = 0;
            int best = 0;
            long bd = -1;
            for (int s = 0; s < d->fmts[fi].nsizes; s++) {
                long dw = (long)d->fmts[fi].w[s] - f->fmt.pix.width, dh = (long)d->fmts[fi].h[s] - f->fmt.pix.height;
                long dist = dw * dw + dh * dh;
                if (bd < 0 || dist < bd) { bd = dist; best = s; }
            }
            f->fmt.pix.pixelformat = d->fmts[fi].fourcc;
            f->fmt.pix.width = d->fmts[fi].w[best];
            f->fmt.pix.height = d->fmts[fi].h[best];
            f->fmt.pix.field = V4L2_FIELD_NONE;
            f->fmt.pix.bytesperline = f->fmt.pix.width * 2;
            f->fmt.pix.sizeimage = f->fmt.pix.width * f->fmt.pix.height * 2;
            return 0;
        }
        if (fi >= 0)
            for (int s = 0; s < d->fmts[fi].nsizes; s++)
                if ((int)f->fmt.pix.width == d->fmts[fi].w[s] && (int)f->fmt.pix.height == d->fmts[fi].h[s]) {
                    d->curfmt = d->fmts[fi].fourcc; d->curw = d->fmts[fi].w[s]; d->curh = d->fmts[fi].h[s];
                    f->fmt.pix.field = V4L2_FIELD_NONE;
                    f->fmt.pix.bytesperline = d->curw * 2;
                    f->fmt.pix.sizeimage = d->curw * d->curh * 2;
                    save_state(d);
                    logline(d, "S_FMT %.4s %ux%u", (char *)&d->curfmt, d->curw, d->curh);
                    return 0;
                }
        errno = EINVAL; // a real driver would adjust to the nearest size; the rig's camera is strict so a test can tell
        return -1;
    }
    case VIDIOC_G_PARM: {
        struct v4l2_streamparm *p = arg;
        p->parm.capture.timeperframe.numerator = 1;
        p->parm.capture.timeperframe.denominator = d->fps;
        p->parm.capture.capability = V4L2_CAP_TIMEPERFRAME;
        return 0;
    }
    case VIDIOC_S_PARM: {
        struct v4l2_streamparm *p = arg;
        if (d->busy) { errno = EBUSY; return -1; }
        const __u32 num = p->parm.capture.timeperframe.numerator, den = p->parm.capture.timeperframe.denominator;
        const int *rates = NULL;
        int n = rates_of(d, d->curfmt, d->curw, d->curh, &rates);
        for (int r = 0; r < n; r++)
            if (num && (den + num / 2) / num == (__u32)rates[r]) {
                d->fps = rates[r];
                save_state(d);
                logline(d, "S_PARM %d", d->fps);
                p->parm.capture.timeperframe.numerator = 1;
                p->parm.capture.timeperframe.denominator = rates[r];
                p->parm.capture.capability = V4L2_CAP_TIMEPERFRAME;
                return 0;
            }
        errno = EINVAL;
        return -1;
    }
    case VIDIOC_QUERYCTRL:
        errno = EINVAL; // the old interface: answered as an empty list (PipeWire's props), the extended one below is the camera's
        return -1;
    case VIDIOC_QUERY_EXT_CTRL: {
        struct v4l2_query_ext_ctrl *q = arg;
        __u32 want = q->id & ~(V4L2_CTRL_FLAG_NEXT_CTRL | V4L2_CTRL_FLAG_NEXT_COMPOUND);
        int compound = q->id & V4L2_CTRL_FLAG_NEXT_COMPOUND;
        struct ctrl *c = NULL;
        if (q->id & (V4L2_CTRL_FLAG_NEXT_CTRL | V4L2_CTRL_FLAG_NEXT_COMPOUND)) {
            for (int i = 0; i < d->nctrls; i++) {
                int isc = d->ctrls[i].type >= V4L2_CTRL_COMPOUND_TYPES;
                if ((!isc || compound) && d->ctrls[i].id > want && (!c || d->ctrls[i].id < c->id)) c = &d->ctrls[i];
            }
        } else
            c = byid(d, want);
        if (!c) { errno = EINVAL; return -1; }
        memset(q, 0, sizeof *q);
        q->id = c->id; q->type = c->type; q->minimum = c->min; q->maximum = c->max; q->step = c->step;
        q->default_value = c->def; q->flags = c->flags | (inactive_now(d, c) ? V4L2_CTRL_FLAG_INACTIVE : 0);
        q->elem_size = c->type == V4L2_CTRL_TYPE_U8 ? 1 : 4; q->elems = c->type == V4L2_CTRL_TYPE_U8 ? 4 : 1;
        if (c->type == V4L2_CTRL_TYPE_U8) { q->nr_of_dims = 1; q->dims[0] = 4; }
        snprintf(q->name, sizeof q->name, "%.31s", c->name);
        return 0;
    }
    case VIDIOC_QUERYMENU: {
        struct v4l2_querymenu *m = arg;
        struct ctrl *c = byid(d, m->id);
        if (!c || (int)m->index >= c->nmenu || !strcmp(c->menu[m->index], "-")) { errno = EINVAL; return -1; }
        snprintf((char *)m->name, sizeof m->name, "%s", c->menu[m->index]);
        return 0;
    }
    case VIDIOC_G_EXT_CTRLS: {
        struct v4l2_ext_controls *e = arg;
        for (__u32 i = 0; i < e->count; i++) {
            struct ctrl *c = byid(d, e->controls[i].id);
            if (!c) { e->error_idx = i; errno = EINVAL; return -1; }
            if (c->flags & V4L2_CTRL_FLAG_WRITE_ONLY) { e->error_idx = i; errno = EACCES; return -1; }
            // while its master is automatic the reading is what the automatic mode chose, and it moves
            e->controls[i].value = (c->hasauto && inactive_now(d, c)) ? c->autoval + (int)(d->reads++ % 7) * 10 : c->value;
        }
        return 0;
    }
    case VIDIOC_S_EXT_CTRLS: {
        struct v4l2_ext_controls *e = arg;
        for (__u32 i = 0; i < e->count; i++) {
            struct ctrl *c = byid(d, e->controls[i].id);
            if (!c) { e->error_idx = i; errno = EINVAL; return -1; }
            if (c->flags & V4L2_CTRL_FLAG_READ_ONLY) { e->error_idx = i; errno = EACCES; return -1; }
            if (c->flags & V4L2_CTRL_FLAG_GRABBED) { e->error_idx = i; errno = EBUSY; return -1; }
            if (inactive_now(d, c)) { e->error_idx = i; errno = EACCES; logline(d, "S_CTRL %s refused inactive", c->name); return -1; }
            int v = e->controls[i].value;
            if (c->type == V4L2_CTRL_TYPE_INTEGER && c->clamp) {
                int step = c->step > 0 ? c->step : 1;
                v = c->min + (v - c->min + step / 2) / step * step;
                v = v < c->min ? c->min : v > c->max ? c->max : v;
            }
            if (c->refuse || (c->type != V4L2_CTRL_TYPE_BUTTON && (v < c->min || v > c->max))) {
                e->error_idx = i; errno = ERANGE; logline(d, "S_CTRL %s %d refused range", c->name, e->controls[i].value); return -1;
            }
            if (c->type != V4L2_CTRL_TYPE_BUTTON) c->value = v;
            logline(d, "S_CTRL %s %d", c->name, v);
        }
        save_state(d);
        return 0;
    }
    default:
        errno = ENOTTY;
        return -1;
    }
}
