// A virtual V4L2 camera for the rig, in user space: preload it and /dev/videoN opens a fake descriptor whose V4L2 ioctls
// this file answers, with the kernel's own structures (linux/videodev2.h). No module, no device node, no real camera.
// The camera is described by $VCAM_ROOT/videoN.cfg (see vcam-A.cfg); removing the file is unplugging the camera, and a plugged
// camera starts at its defaults (the values live in $VCAM_ROOT/videoN.state, which the shim erases when it is opened new).
// Build: cc -shared -fPIC -O1 -o vcam-shim.so vcam-shim.c -ldl
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
#define MAXCTRL 24
#define MAXFMT 6

struct ctrl {
    char name[64];
    __u32 id;
    int type;
    int min, max, step, def, flags;
    char menu[8][48];
    int nmenu;
    int refuse; // the driver answers ERANGE to every set
    int value;
};
struct fmt {
    __u32 fourcc;
    char desc[32];
    int nsizes;
    int w[8], h[8];
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
};
static struct dev devs[MAXFD];
static int ndevs;

static int (*real_open)(const char *, int, ...);
static int (*real_ioctl)(int, unsigned long, ...);
static int (*real_close)(int);

static __u32 cc(const char *s) { return s[0] | s[1] << 8 | s[2] << 16 | (__u32)s[3] << 24; }

static void statepath(int num, char *out, size_t n) { snprintf(out, n, "%s/video%d.state", getenv("VCAM_ROOT"), num); }

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

static int load_cfg(struct dev *d, const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f)
        return -1;
    char line[512];
    struct fmt *cf = NULL;
    while (fgets(line, sizeof line, f)) {
        line[strcspn(line, "\n")] = 0;
        char *a = strtok(line, " ");
        if (!a || a[0] == '#')
            continue;
        if (!strcmp(a, "card")) snprintf(d->card, sizeof d->card, "%.63s", line + 5);
        else if (!strcmp(a, "bus")) snprintf(d->bus, sizeof d->bus, "%.63s", line + 4);
        else if (!strcmp(a, "busy")) d->busy = 1;
        else if (!strcmp(a, "format") && d->nfmts < MAXFMT) {
            cf = &d->fmts[d->nfmts++];
            memset(cf, 0, sizeof *cf);
            cf->fourcc = cc(strtok(NULL, " "));
            snprintf(cf->desc, sizeof cf->desc, "%s", strtok(NULL, " "));
        } else if (!strcmp(a, "size") && cf && cf->nsizes < 8) {
            sscanf(strtok(NULL, " "), "%dx%d", &cf->w[cf->nsizes], &cf->h[cf->nsizes]);
            cf->nsizes++;
        } else if (!strcmp(a, "rate") && cf && cf->nrates < 6) cf->rates[cf->nrates++] = atoi(strtok(NULL, " "));
        else if (!strcmp(a, "ctrl") && d->nctrls < MAXCTRL) {
            // ctrl NAME TYPE MIN MAX STEP DEFAULT [refuse|inactive|readonly|MENUITEM,...]
            struct ctrl *c = &d->ctrls[d->nctrls];
            memset(c, 0, sizeof *c);
            snprintf(c->name, sizeof c->name, "%s", strtok(NULL, " "));
            char *t = strtok(NULL, " ");
            c->type = !strcmp(t, "int") ? V4L2_CTRL_TYPE_INTEGER : !strcmp(t, "bool") ? V4L2_CTRL_TYPE_BOOLEAN
                : !strcmp(t, "menu") ? V4L2_CTRL_TYPE_MENU : V4L2_CTRL_TYPE_BUTTON;
            c->min = atoi(strtok(NULL, " "));
            c->max = atoi(strtok(NULL, " "));
            c->step = atoi(strtok(NULL, " "));
            c->def = c->value = atoi(strtok(NULL, " "));
            if (c->type == V4L2_CTRL_TYPE_BUTTON) c->flags |= V4L2_CTRL_FLAG_WRITE_ONLY;
            c->id = V4L2_CID_BASE + 0x400 + d->nctrls;
            // a control named like a standard one gets the kernel's own id, so a page can show the standard name
            static const struct { const char *name; __u32 id; } standard[] = {
                {"brightness", V4L2_CID_BRIGHTNESS}, {"contrast", V4L2_CID_CONTRAST}, {"auto_exposure", V4L2_CID_EXPOSURE_AUTO},
                {"white_balance_automatic", V4L2_CID_AUTO_WHITE_BALANCE}, {"sharpness", V4L2_CID_SHARPNESS},
                {"exposure_time_absolute", V4L2_CID_EXPOSURE_ABSOLUTE}, {"power_line_frequency", V4L2_CID_POWER_LINE_FREQUENCY},
            };
            for (unsigned k = 0; k < sizeof standard / sizeof *standard; k++)
                if (!strcmp(c->name, standard[k].name)) c->id = standard[k].id;
            for (char *o; (o = strtok(NULL, " "));) {
                if (!strcmp(o, "refuse")) c->refuse = 1;
                else if (!strcmp(o, "inactive")) c->flags |= V4L2_CTRL_FLAG_INACTIVE;
                else if (!strcmp(o, "readonly")) c->flags |= V4L2_CTRL_FLAG_READ_ONLY;
                else if (c->nmenu < 8) snprintf(c->menu[c->nmenu++], 48, "%s", o);
            }
            d->nctrls++;
        }
    }
    fclose(f);
    d->curfmt = d->fmts[0].fourcc;
    d->curw = d->fmts[0].w[0];
    d->curh = d->fmts[0].h[0];
    d->fps = d->fmts[0].rates[0];
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
    char sp[512];
    statepath(num, sp, sizeof sp);
    FILE *f = fopen(sp, "r");
    if (f) { // the values the camera holds since it was plugged
        char l[256], n[64];
        int v;
        while (fgets(l, sizeof l, f)) {
            if (sscanf(l, "ctrl %63s %d", n, &v) == 2)
                for (int i = 0; i < d->nctrls; i++)
                    if (!strcmp(d->ctrls[i].name, n)) d->ctrls[i].value = v;
            unsigned a, b, c2; int r;
            if (sscanf(l, "fmt %u %u %u %d", &a, &b, &c2, &r) == 4) { d->curfmt = a; d->curw = b; d->curh = c2; d->fps = r; }
        }
        fclose(f);
    }
    (void)flags; (void)mode;
    return fd;
}

int open(const char *path, int flags, ...)
{
    va_list ap;
    va_start(ap, flags);
    int mode = (flags & O_CREAT) ? va_arg(ap, int) : 0;
    va_end(ap);
    int handled;
    int fd = vopen(path, flags, mode, &handled);
    if (handled)
        return fd;
    return real_open(path, flags, mode);
}
int open64(const char *path, int flags, ...) __attribute__((alias("open")));

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

int ioctl(int fd, unsigned long req, ...)
{
    init();
    va_list ap;
    va_start(ap, req);
    void *arg = va_arg(ap, void *);
    va_end(ap);
    struct dev *d = find(fd);
    if (!d)
        return real_ioctl(fd, req, arg);
    switch (req) {
    case VIDIOC_QUERYCAP: {
        struct v4l2_capability *c = arg;
        memset(c, 0, sizeof *c);
        snprintf((char *)c->driver, sizeof c->driver, "uvcvideo");
        snprintf((char *)c->card, sizeof c->card, "%.31s", d->card);
        snprintf((char *)c->bus_info, sizeof c->bus_info, "%.31s", d->bus);
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
        for (int i = 0; i < d->nfmts; i++)
            if (d->fmts[i].fourcc == s->pixel_format) {
                if ((int)s->index >= d->fmts[i].nrates) { errno = EINVAL; return -1; }
                s->type = V4L2_FRMIVAL_TYPE_DISCRETE;
                s->discrete.numerator = 1;
                s->discrete.denominator = d->fmts[i].rates[s->index];
                return 0;
            }
        errno = EINVAL;
        return -1;
    }
    case VIDIOC_G_FMT: {
        struct v4l2_format *f = arg;
        f->fmt.pix.width = d->curw; f->fmt.pix.height = d->curh; f->fmt.pix.pixelformat = d->curfmt;
        f->fmt.pix.field = V4L2_FIELD_NONE;
        return 0;
    }
    case VIDIOC_S_FMT: {
        struct v4l2_format *f = arg;
        if (d->busy) { errno = EBUSY; return -1; }
        for (int i = 0; i < d->nfmts; i++)
            if (d->fmts[i].fourcc == f->fmt.pix.pixelformat)
                for (int s = 0; s < d->fmts[i].nsizes; s++)
                    if ((int)f->fmt.pix.width == d->fmts[i].w[s] && (int)f->fmt.pix.height == d->fmts[i].h[s]) {
                        d->curfmt = d->fmts[i].fourcc; d->curw = d->fmts[i].w[s]; d->curh = d->fmts[i].h[s];
                        save_state(d);
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
        int want = p->parm.capture.timeperframe.numerator ? p->parm.capture.timeperframe.denominator / p->parm.capture.timeperframe.numerator : 0;
        for (int i = 0; i < d->nfmts; i++)
            if (d->fmts[i].fourcc == d->curfmt)
                for (int r = 0; r < d->fmts[i].nrates; r++)
                    if (d->fmts[i].rates[r] == want) { d->fps = want; save_state(d); p->parm.capture.timeperframe.denominator = want; return 0; }
        errno = EINVAL;
        return -1;
    }
    case VIDIOC_QUERY_EXT_CTRL: {
        struct v4l2_query_ext_ctrl *q = arg;
        __u32 want = q->id & ~(V4L2_CTRL_FLAG_NEXT_CTRL | V4L2_CTRL_FLAG_NEXT_COMPOUND);
        struct ctrl *c = NULL;
        if (q->id & V4L2_CTRL_FLAG_NEXT_CTRL) {
            for (int i = 0; i < d->nctrls; i++)
                if (d->ctrls[i].id > want && (!c || d->ctrls[i].id < c->id)) c = &d->ctrls[i];
        } else
            c = byid(d, want);
        if (!c) { errno = EINVAL; return -1; }
        memset(q, 0, sizeof *q);
        q->id = c->id; q->type = c->type; q->minimum = c->min; q->maximum = c->max; q->step = c->step;
        q->default_value = c->def; q->flags = c->flags; q->elem_size = 4; q->elems = 1;
        snprintf(q->name, sizeof q->name, "%.31s", c->name);
        return 0;
    }
    case VIDIOC_QUERYMENU: {
        struct v4l2_querymenu *m = arg;
        struct ctrl *c = byid(d, m->id);
        if (!c || (int)m->index >= c->nmenu) { errno = EINVAL; return -1; }
        snprintf((char *)m->name, sizeof m->name, "%s", c->menu[m->index]);
        return 0;
    }
    case VIDIOC_G_EXT_CTRLS: {
        struct v4l2_ext_controls *e = arg;
        for (__u32 i = 0; i < e->count; i++) {
            struct ctrl *c = byid(d, e->controls[i].id);
            if (!c) { e->error_idx = i; errno = EINVAL; return -1; }
            e->controls[i].value = c->value;
        }
        return 0;
    }
    case VIDIOC_S_EXT_CTRLS: {
        struct v4l2_ext_controls *e = arg;
        for (__u32 i = 0; i < e->count; i++) {
            struct ctrl *c = byid(d, e->controls[i].id);
            if (!c) { e->error_idx = i; errno = EINVAL; return -1; }
            if (c->flags & V4L2_CTRL_FLAG_READ_ONLY) { e->error_idx = i; errno = EACCES; return -1; }
            if (c->flags & V4L2_CTRL_FLAG_INACTIVE) { e->error_idx = i; errno = EACCES; return -1; }
            if (c->refuse || (c->type != V4L2_CTRL_TYPE_BUTTON && (e->controls[i].value < c->min || e->controls[i].value > c->max))) { e->error_idx = i; errno = ERANGE; return -1; }
            if (c->type != V4L2_CTRL_TYPE_BUTTON) c->value = e->controls[i].value;
        }
        save_state(d);
        return 0;
    }
    default:
        errno = ENOTTY;
        return -1;
    }
}
