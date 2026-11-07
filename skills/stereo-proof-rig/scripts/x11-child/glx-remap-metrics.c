// SPDX-License-Identifier: GPL-2.0-or-later (from the open-sims lane of Sparky Stereo OS)
// Isolate drawable stereo capability from simulator render pipelines.
#include <GL/gl.h>
#include <GL/glx.h>
#include <X11/Xlib.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    Display *display = XOpenDisplay(NULL);
    if (!display) return 2;
    int stereo_request = argc > 1 && atoi(argv[1]);
    int attrs[] = { GLX_RENDER_TYPE, GLX_RGBA_BIT, GLX_DRAWABLE_TYPE, GLX_WINDOW_BIT,
                    GLX_DOUBLEBUFFER, True, GLX_STEREO, stereo_request, None };
    int count = 0;GLXFBConfig* configs=glXChooseFBConfig(display,DefaultScreen(display),attrs,&count);
    if (!configs || !count) return 3;
    GLXFBConfig config=configs[0];XVisualInfo* visual=glXGetVisualFromFBConfig(display,config);XFree(configs);
    if(!visual) return 3;
    XSetWindowAttributes properties = {0};
    properties.colormap = XCreateColormap(display, RootWindow(display, visual->screen), visual->visual, AllocNone);
    Window window = XCreateWindow(display, RootWindow(display, visual->screen), 0, 0, 640, 480,
                                  0, visual->depth, InputOutput, visual->visual, CWColormap, &properties);
    XStoreName(display, window, "GLX remap metrics");
    XMapWindow(display, window);
    GLXContext context = glXCreateNewContext(display, config, GLX_RGBA_TYPE, NULL, True);
    if (!context || !glXMakeCurrent(display, window, context)) return 4;
    GLboolean stereo = GL_FALSE;
    glGetBooleanv(GL_STEREO, &stereo);
    glDrawBuffer(GL_BACK_LEFT);
    GLenum left_error = glGetError();
    if(stereo_request) glDrawBuffer(GL_BACK_RIGHT);
    GLenum right_error = glGetError();
    printf("requested_visual=%d GL_STEREO=%d left_error=0x%x right_error=0x%x\n",
           argc > 1 ? atoi(argv[1]) : 0, stereo, left_error, right_error);
    fflush(stdout);
    for (int frame=0; frame<1000; ++frame) {
        if (frame==10) { XUnmapWindow(display,window); XMapWindow(display,window); XSync(display,False); }
        while (XPending(display)) { XEvent event; XNextEvent(display,&event); }

        glDrawBuffer(GL_BACK_LEFT);
        glClearColor(1, 0, 0, 1);
        glClear(GL_COLOR_BUFFER_BIT);
        if(stereo_request) {
            glDrawBuffer(GL_BACK_RIGHT);
            glClearColor(0, 0, 1, 1);
            glClear(GL_COLOR_BUFFER_BIT);
        }
        glXSwapBuffers(display, window);
        if(frame%5==0) {
            unsigned width=0;glXQueryDrawable(display,window,GLX_WIDTH,&width);
            XWindowAttributes attributes;XGetWindowAttributes(display,window,&attributes);
            fprintf(stderr,"lane-raw-glx frame=%d glx_width=%u physical_width=%d\n",frame,width,attributes.width);
        }
        usleep(100000);
    }
}
