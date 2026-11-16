/* SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <locale.h>
char *bindtextdomain(const char *d, const char *dir){ static char*(*f)(const char*,const char*); if(!f) f=dlsym(RTLD_NEXT,"bindtextdomain"); fprintf(stderr,"SHIM bindtextdomain(%s,%s)\n", d, dir?dir:"(null)"); return f(d,dir);}
char *textdomain(const char *d){ static char*(*f)(const char*); if(!f) f=dlsym(RTLD_NEXT,"textdomain"); fprintf(stderr,"SHIM textdomain(%s)\n", d?d:"(null)"); return f(d);}
char *setlocale(int c, const char *l){ static char*(*f)(int,const char*); if(!f) f=dlsym(RTLD_NEXT,"setlocale"); char*r=f(c,l); fprintf(stderr,"SHIM setlocale(%d,%s)=%s\n", c, l?l:"(null)", r?r:"(null)"); return r;}
char *dgettext(const char *d, const char *m){ static char*(*f)(const char*,const char*); static int n; if(!f) f=dlsym(RTLD_NEXT,"dgettext"); char*r=f(d,m); if(n++<3) fprintf(stderr,"SHIM dgettext(%s,%s)=%s\n", d?d:"(null)", m, r); return r;}
