/* SPDX-License-Identifier: MIT */
/* The raw unmap/remap reproducer of the open-sims lane (glx-remap-metrics.c) for an EGL two-view window surface on X11:
 * one 640x480 top-level window, drawn, unmapped and mapped again once. Prints the surface's width and the X window's width. */
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef EGL_MULTIVIEW_VIEW_COUNT_EXT
#define EGL_MULTIVIEW_VIEW_COUNT_EXT 0x3134
#endif

int main(int argc, char **argv)
{
    int stereo = argc > 1 ? atoi(argv[1]) : 1;
    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) return 2;
    PFNEGLGETPLATFORMDISPLAYEXTPROC getpd = (PFNEGLGETPLATFORMDISPLAYEXTPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");
    EGLDisplay ed = getpd(EGL_PLATFORM_X11_EXT, dpy, NULL);
    EGLint maj, min;
    if (!eglInitialize(ed, &maj, &min)) return 3;
    eglBindAPI(EGL_OPENGL_API);
    EGLint ca[] = { EGL_SURFACE_TYPE, EGL_WINDOW_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT, EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_NONE };
    EGLConfig cfg; EGLint nc = 0;
    if (!eglChooseConfig(ed, ca, &cfg, 1, &nc) || nc < 1) return 4;
    EGLint vid; eglGetConfigAttrib(ed, cfg, EGL_NATIVE_VISUAL_ID, &vid);
    XVisualInfo tmpl; tmpl.visualid = vid; int nv = 0;
    XVisualInfo *vi = XGetVisualInfo(dpy, VisualIDMask, &tmpl, &nv);
    XSetWindowAttributes sa; memset(&sa, 0, sizeof sa);
    sa.colormap = XCreateColormap(dpy, RootWindow(dpy, vi->screen), vi->visual, AllocNone);
    Window win = XCreateWindow(dpy, RootWindow(dpy, vi->screen), 0, 0, 640, 480, 0, vi->depth, InputOutput, vi->visual, CWColormap, &sa);
    XStoreName(dpy, win, "EGL remap metrics");
    XMapWindow(dpy, win);
    PFNEGLCREATEPLATFORMWINDOWSURFACEEXTPROC cpws = (PFNEGLCREATEPLATFORMWINDOWSURFACEEXTPROC)eglGetProcAddress("eglCreatePlatformWindowSurfaceEXT");
    EGLint sattr[] = { EGL_MULTIVIEW_VIEW_COUNT_EXT, 2, EGL_NONE };
    EGLSurface es = cpws(ed, cfg, &win, stereo ? sattr : NULL);
    EGLContext ec = eglCreateContext(ed, cfg, EGL_NO_CONTEXT, NULL);
    if (es == EGL_NO_SURFACE || !eglMakeCurrent(ed, es, es, ec)) return 5;
    printf("requested_views=%d\n", stereo ? 2 : 1);
    fflush(stdout);
    for (int frame = 0; frame < 1000; ++frame) {
        if (frame == 10) { XUnmapWindow(dpy, win); XMapWindow(dpy, win); XSync(dpy, False); }
        while (XPending(dpy)) { XEvent ev; XNextEvent(dpy, &ev); }
        glDrawBuffer(GL_BACK_LEFT);  glClearColor(1, 0, 0, 1); glClear(GL_COLOR_BUFFER_BIT);
        if (stereo) { glDrawBuffer(GL_BACK_RIGHT); glClearColor(0, 0, 1, 1); glClear(GL_COLOR_BUFFER_BIT); }
        eglSwapBuffers(ed, es);
        if (frame % 5 == 0) {
            EGLint w = 0; eglQuerySurface(ed, es, EGL_WIDTH, &w);
            XWindowAttributes a; XGetWindowAttributes(dpy, win, &a);
            fprintf(stderr, "lane-raw-glx frame=%d glx_width=%d physical_width=%d\n", frame, w, a.width);
        }
        usleep(100000);
    }
}
