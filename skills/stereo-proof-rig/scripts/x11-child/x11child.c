/* SPDX-License-Identifier: MIT */
/* x11child: a 2D X11 window with a stereo GLX child, for the clipping rows of ORDER 160.
 * usage: x11child MODE   (plain | overflow | sibling | mono-sibling | twosib)
 * Parent: 400x300, grey. GL child: left eye red, right eye blue. The sibling is a plain X window, green, mapped after the child (above it).
 * Prints "parent=<id> child=<id> sibling=<id>" and the child's place; runs until killed. */
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <GL/glx.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static int err(Display *d, XErrorEvent *e) { (void)d; (void)e; return 0; }

int main(int argc, char **argv)
{
    const char *mode = argc > 1 ? argv[1] : "plain";
    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) { fprintf(stderr, "no display\n"); return 2; }
    XSetErrorHandler(err);
    int scr = DefaultScreen(dpy);
    Window root = RootWindow(dpy, scr);
    const int PW = 400, PH = 300;
    int cx = 100, cy = 80, cw = 200, ch = 150;
    if (!strcmp(mode, "overflow")) { cx = 250; cy = 200; cw = 300; ch = 200; }
    int stereo = strcmp(mode, "mono-sibling") != 0 && strcmp(mode, "gls") != 0;
    int drawstereo = strcmp(mode, "mono-sibling") != 0;
    int attrs[] = { GLX_X_RENDERABLE, True, GLX_DRAWABLE_TYPE, GLX_WINDOW_BIT, GLX_RENDER_TYPE, GLX_RGBA_BIT,
        GLX_DOUBLEBUFFER, True, GLX_STEREO, stereo ? True : False, GLX_RED_SIZE, 8, GLX_GREEN_SIZE, 8, GLX_BLUE_SIZE, 8, None };
    int n = 0;
    GLXFBConfig *fb = glXChooseFBConfig(dpy, scr, attrs, &n);
    if (!fb || n < 1) { fprintf(stderr, "no %s fbconfig\n", stereo ? "stereo" : "mono"); return 3; }
    XVisualInfo *vi = glXGetVisualFromFBConfig(dpy, fb[0]);
    Colormap cmap = XCreateColormap(dpy, root, vi->visual, AllocNone);
    XSetWindowAttributes sa; memset(&sa, 0, sizeof sa);
    sa.colormap = cmap; sa.border_pixel = 0; sa.background_pixel = 0x808080; sa.event_mask = StructureNotifyMask | ExposureMask;
    Window parent = XCreateWindow(dpy, root, 200, 150, PW, PH, 0, vi->depth, InputOutput, vi->visual,
                                  CWColormap | CWBorderPixel | CWBackPixel | CWEventMask, &sa);
    XStoreName(dpy, parent, "x11child-parent");
    Window child = XCreateWindow(dpy, parent, cx, cy, cw, ch, 0, vi->depth, InputOutput, vi->visual,
                                 CWColormap | CWBorderPixel | CWBackPixel | CWEventMask, &sa);
    Window sib = 0, sib2 = 0;
    int sx = cx + cw / 2, sy = cy - 20, sw = 120, sh = ch / 2;
    if (!strcmp(mode, "sibling") || !strcmp(mode, "mono-sibling") || !strcmp(mode, "twosib")) {
        sa.background_pixel = 0x00c000;
        sib = XCreateWindow(dpy, parent, sx, sy, sw, sh, 0, vi->depth, InputOutput, vi->visual,
                            CWColormap | CWBorderPixel | CWBackPixel | CWEventMask, &sa);
    }
    GLXContext ctx = glXCreateNewContext(dpy, fb[0], GLX_RGBA_TYPE, NULL, True);
    XMapWindow(dpy, child);
    if (sib) XMapWindow(dpy, sib);
    XMapWindow(dpy, parent);
    XSync(dpy, False);
    GLXWindow gw = glXCreateWindow(dpy, fb[0], child, NULL);
    glXMakeContextCurrent(dpy, gw, gw, ctx);
    printf("parent=0x%lx child=0x%lx sibling=0x%lx place=%d,%d,%d,%d sib=%d,%d,%d,%d stereo=%d\n", parent, child, sib, cx, cy, cw, ch, sx, sy, sw, sh, stereo);
    fflush(stdout);
    for (int frame = 0;; frame++) {
        while (XPending(dpy)) { XEvent ev; XNextEvent(dpy, &ev); }
        glViewport(0, 0, cw, ch);
        if (drawstereo) {
            glDrawBuffer(GL_BACK_LEFT);  glClearColor(0.78f, 0.f, 0.f, 1.f); glClear(GL_COLOR_BUFFER_BIT);
            glDrawBuffer(GL_BACK_RIGHT); glClearColor(0.f, 0.f, 0.78f, 1.f); glClear(GL_COLOR_BUFFER_BIT);
        } else {
            glClearColor(0.78f, 0.78f, 0.f, 1.f); glClear(GL_COLOR_BUFFER_BIT);
        }
        glXSwapBuffers(dpy, gw);
        usleep(50000);
    }
}
