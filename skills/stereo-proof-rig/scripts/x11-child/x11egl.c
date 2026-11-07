/* SPDX-License-Identifier: MIT */
/* x11egl: like x11child, but the 3D area is an EGL two-view window surface (EGL_EXT_multiview_window) on a child X window.
 * usage: x11egl MODE (plain | overflow | sibling | egl-plain ...); prints the same line as x11child. */
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#ifndef EGL_MULTIVIEW_VIEW_COUNT_EXT
#define EGL_MULTIVIEW_VIEW_COUNT_EXT 0x3134
#endif

static int err(Display *d, XErrorEvent *e) { (void)d; (void)e; return 0; }

int main(int argc, char **argv)
{
    const char *mode = argc > 1 ? argv[1] : "plain";
    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) return 2;
    XSetErrorHandler(err);
    int scr = DefaultScreen(dpy);
    Window root = RootWindow(dpy, scr);
    const int PW = 400, PH = 300;
    int cx = 100, cy = 80, cw = 200, ch = 150;
    if (!strcmp(mode, "overflow")) { cx = 250; cy = 200; cw = 300; ch = 200; }
    PFNEGLGETPLATFORMDISPLAYEXTPROC getpd = (PFNEGLGETPLATFORMDISPLAYEXTPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");
    EGLDisplay ed = getpd(EGL_PLATFORM_X11_EXT, dpy, NULL);
    EGLint maj, min;
    if (!eglInitialize(ed, &maj, &min)) { fprintf(stderr, "eglInitialize failed\n"); return 3; }
    const char *ext = eglQueryString(ed, EGL_EXTENSIONS);
    fprintf(stderr, "egl %d.%d multiview_window=%d\n", maj, min, ext && strstr(ext, "EGL_EXT_multiview_window") != NULL);
    eglBindAPI(EGL_OPENGL_API);
    EGLint ca[] = { EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT, EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_NONE };
    EGLConfig cfg; EGLint nc = 0;
    if (!eglChooseConfig(ed, ca, &cfg, 1, &nc) || nc < 1) { fprintf(stderr, "no config\n"); return 4; }
    EGLint vid; eglGetConfigAttrib(ed, cfg, EGL_NATIVE_VISUAL_ID, &vid);
    XVisualInfo tmpl; tmpl.visualid = vid; int nv = 0;
    XVisualInfo *vi = XGetVisualInfo(dpy, VisualIDMask, &tmpl, &nv);
    Colormap cmap = XCreateColormap(dpy, root, vi->visual, AllocNone);
    XSetWindowAttributes sa; memset(&sa, 0, sizeof sa);
    sa.colormap = cmap; sa.border_pixel = 0; sa.background_pixel = 0x808080; sa.event_mask = StructureNotifyMask | ExposureMask;
    Window parent = XCreateWindow(dpy, root, 200, 150, PW, PH, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWBorderPixel | CWBackPixel | CWEventMask, &sa);
    XStoreName(dpy, parent, "x11egl-parent");
    Window child = XCreateWindow(dpy, parent, cx, cy, cw, ch, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWBorderPixel | CWBackPixel | CWEventMask, &sa);
    int sx = cx + cw / 2, sy = cy - 20, sw = 120, sh = ch / 2;
    Window sib = 0;
    if (!strcmp(mode, "sibling")) {
        sa.background_pixel = 0x00c000;
        sib = XCreateWindow(dpy, parent, sx, sy, sw, sh, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWBorderPixel | CWBackPixel | CWEventMask, &sa);
    }
    XMapWindow(dpy, child); if (sib) XMapWindow(dpy, sib); XMapWindow(dpy, parent); XSync(dpy, False);
    EGLint sattr[] = { EGL_MULTIVIEW_VIEW_COUNT_EXT, 2, EGL_NONE };
    PFNEGLCREATEPLATFORMWINDOWSURFACEEXTPROC cpws = (PFNEGLCREATEPLATFORMWINDOWSURFACEEXTPROC)eglGetProcAddress("eglCreatePlatformWindowSurfaceEXT");
    EGLSurface es = cpws(ed, cfg, &child, sattr);
    if (es == EGL_NO_SURFACE) { fprintf(stderr, "no two-view surface: 0x%x\n", eglGetError()); return 5; }
    EGLContext ec = eglCreateContext(ed, cfg, EGL_NO_CONTEXT, NULL);
    if (!eglMakeCurrent(ed, es, es, ec)) { fprintf(stderr, "make current 0x%x\n", eglGetError()); return 6; }
    printf("parent=0x%lx child=0x%lx sibling=0x%lx place=%d,%d,%d,%d sib=%d,%d,%d,%d stereo=1\n", parent, child, sib, cx, cy, cw, ch, sx, sy, sw, sh);
    fflush(stdout);
    for (;;) {
        while (XPending(dpy)) { XEvent ev; XNextEvent(dpy, &ev); }
        glViewport(0, 0, cw, ch);
        glDrawBuffer(GL_BACK_LEFT);  glClearColor(0.78f, 0.f, 0.f, 1.f); glClear(GL_COLOR_BUFFER_BIT);
        glDrawBuffer(GL_BACK_RIGHT); glClearColor(0.f, 0.f, 0.78f, 1.f); glClear(GL_COLOR_BUFFER_BIT);
        eglSwapBuffers(ed, es);
        usleep(50000);
    }
}
