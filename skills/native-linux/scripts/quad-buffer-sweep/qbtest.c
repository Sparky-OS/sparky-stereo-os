/* Quad-buffer GLX calibration client: left eye red square at x=-0.2, right eye blue square at x=+0.2 (NDC),
   so the right image lies 0.4*W/2 pixels to the right of the left one (positive shift = behind the screen).
   usage: qbtest [mono] */
#include <X11/Xlib.h>
#include <GL/glx.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
static void box(float cx,float r,float g,float b){glColor3f(r,g,b);glBegin(GL_QUADS);glVertex2f(cx-.15f,-.3f);glVertex2f(cx+.15f,-.3f);glVertex2f(cx+.15f,.3f);glVertex2f(cx-.15f,.3f);glEnd();}
int main(int argc,char**argv){
 int mono=argc>1&&!strcmp(argv[1],"mono");
 Display*d=XOpenDisplay(0);if(!d)return 2;
 int a[]={GLX_RENDER_TYPE,GLX_RGBA_BIT,GLX_DRAWABLE_TYPE,GLX_WINDOW_BIT,GLX_DOUBLEBUFFER,1,GLX_STEREO,mono?0:1,GLX_RED_SIZE,8,GLX_GREEN_SIZE,8,GLX_BLUE_SIZE,8,GLX_DEPTH_SIZE,16,None};
 int n;GLXFBConfig*c=glXChooseFBConfig(d,0,a,&n);
 if(!c||!n){fprintf(stderr,"qbtest: no %s FBConfig\n",mono?"mono":"stereo");return 3;}
 XVisualInfo*vi=glXGetVisualFromFBConfig(d,c[0]);
 XSetWindowAttributes sa;sa.colormap=XCreateColormap(d,RootWindow(d,vi->screen),vi->visual,AllocNone);sa.event_mask=ExposureMask;
 Window w=XCreateWindow(d,RootWindow(d,vi->screen),0,0,640,480,0,vi->depth,InputOutput,vi->visual,CWColormap|CWEventMask,&sa);
 XStoreName(d,w,"qbtest");XMapWindow(d,w);
 GLXContext cx=glXCreateNewContext(d,c[0],GLX_RGBA_TYPE,0,1);glXMakeContextCurrent(d,w,w,cx);
 int st=0;glGetIntegerv(GL_STEREO,&st);fprintf(stderr,"qbtest: GL_STEREO=%d renderer=%s\n",st,glGetString(GL_RENDERER));
 for(;;){
  XWindowAttributes wa;XGetWindowAttributes(d,w,&wa);glViewport(0,0,wa.width,wa.height);
  glDrawBuffer(mono?GL_BACK:GL_BACK_LEFT);glClearColor(.1f,.1f,.1f,1);glClear(GL_COLOR_BUFFER_BIT);box(mono?0:-.2f,1,0,0);
  if(!mono){glDrawBuffer(GL_BACK_RIGHT);glClear(GL_COLOR_BUFFER_BIT);box(.2f,0,0,1);}
  glXSwapBuffers(d,w);usleep(30000);
 }
}
