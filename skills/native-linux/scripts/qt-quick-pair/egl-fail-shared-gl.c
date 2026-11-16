// A test shim (LD_PRELOAD) that makes the Nth eglCreateContext of the program fail whose bound client API
// is desktop OpenGL and which shares another context (QF583_FAIL_SHARED_GL=N), and says so on standard error. In a Qt
// Quick program on desktop OpenGL inside Qt's own frame, N=2 refuses the frame's ordinary decorations context ("Decorations
// will not be drawn") and N=3 the one made for a window with two views ("Failed to create the decorations EGLContext
// of a window with two views"), the path where that frame cannot be drawn into both views (measured, ORDER 583).
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <EGL/egl.h>

EGLContext eglCreateContext(EGLDisplay dpy, EGLConfig config, EGLContext share, const EGLint *attribs)
{
    static EGLContext (*real)(EGLDisplay, EGLConfig, EGLContext, const EGLint *);
    static int count;
    if (!real)
        real = (EGLContext (*)(EGLDisplay, EGLConfig, EGLContext, const EGLint *))dlsym(RTLD_NEXT, "eglCreateContext");
    const char *n = getenv("QF583_FAIL_SHARED_GL");
    if (n && share != EGL_NO_CONTEXT && eglQueryAPI() == EGL_OPENGL_API && ++count == atoi(n)) {
        fprintf(stderr, "egl-fail-shared-gl: shared desktop OpenGL context %d refused\n", count);
        return EGL_NO_CONTEXT;
    }
    return real(dpy, config, share, attribs);
}
