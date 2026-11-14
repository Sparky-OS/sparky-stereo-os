/* glx-fps.c: a GLX quad buffer window (STEREO=0: a plain one) that swaps FRAMES times as fast as the swap lets it, then
 * prints the swaps per second, with the swap interval the driver gives by default and again with INTERVAL (default 0).
 * Build: cc -O1 -o glx-fps glx-fps.c -lGL -lX11      SPDX-License-Identifier: MIT */
#define GLX_GLXEXT_PROTOTYPES
#include <GL/gl.h>
#include <GL/glx.h>
#include <GL/glxext.h>
#include <X11/Xlib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec / 1e9; }
int main(void)
{
    int n = 0, frames = getenv("FRAMES") ? atoi(getenv("FRAMES")) : 600, stereo = !getenv("STEREO") || atoi(getenv("STEREO"));
    Display *d = XOpenDisplay(NULL);
    if (!d) return 2;
    int att[] = { GLX_RENDER_TYPE, GLX_RGBA_BIT, GLX_DRAWABLE_TYPE, GLX_WINDOW_BIT, GLX_DOUBLEBUFFER, True, GLX_STEREO, stereo ? True : False,
                  GLX_RED_SIZE, 8, GLX_GREEN_SIZE, 8, GLX_BLUE_SIZE, 8, None };
    GLXFBConfig *c = glXChooseFBConfig(d, DefaultScreen(d), att, &n);
    if (!c || !n) { printf("glx-fps: NO-CONFIG\n"); return 4; }
    XVisualInfo *vi = glXGetVisualFromFBConfig(d, c[0]);
    XSetWindowAttributes swa; memset(&swa, 0, sizeof swa);
    swa.colormap = XCreateColormap(d, RootWindow(d, vi->screen), vi->visual, AllocNone); swa.event_mask = ExposureMask;
    Window win = XCreateWindow(d, RootWindow(d, vi->screen), 100, 100, 800, 600, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);
    XMapWindow(d, win);
    for (;;) { XEvent e; XNextEvent(d, &e); if (e.type == Expose) break; }
    GLXContext ctx = glXCreateNewContext(d, c[0], GLX_RGBA_TYPE, NULL, True);
    glXMakeCurrent(d, win, ctx);
    for (int pass = 0; pass < 2; pass++) {
        if (pass) glXSwapIntervalEXT(d, win, getenv("INTERVAL") ? atoi(getenv("INTERVAL")) : 0);
        for (int i = 0; i < 30; i++) { glClear(GL_COLOR_BUFFER_BIT); glXSwapBuffers(d, win); }
        double t0 = now();
        for (int i = 0; i < frames; i++) {
            for (int eye = 0; eye < (stereo ? 2 : 1); eye++) {
                glDrawBuffer(stereo ? (eye ? GL_BACK_RIGHT : GL_BACK_LEFT) : GL_BACK);
                glClearColor(eye ? 0 : (i % 60) / 60.0f, 0, eye ? 1 : 0, 1); glClear(GL_COLOR_BUFFER_BIT);
            }
            glXSwapBuffers(d, win);
        }
        glFinish();
        printf("glx-fps: %s, %s: %.1f swaps a second (%s)\n", stereo ? "stereo" : "mono", pass ? "interval 0" : "default interval", frames / (now() - t0), glGetString(GL_RENDERER));
        fflush(stdout);
    }
    return 0;
}
