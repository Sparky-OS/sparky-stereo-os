/* Test-only injection at the Present request. Never part of a shipped library.
 * SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <xcb/present.h>
#include <xcb/xcbext.h>
#include <sys/uio.h>
#include <string.h>
#include <stdbool.h>

static void *symbol(const char *name)
{
   void *p=dlsym(RTLD_NEXT,name);
   if(!p) { void *lib=dlopen("libxcb-present.so.0",RTLD_NOW|RTLD_LOCAL); if(lib) p=dlsym(lib,name); }
   if(!p) { fprintf(stderr,"present injection: %s unavailable\n",name); _exit(8); }
   return p;
}

static xcb_pixmap_t injected(xcb_connection_t *c, xcb_pixmap_t source, int16_t *xoff)
{
   xcb_get_geometry_reply_t *g=xcb_get_geometry_reply(c,xcb_get_geometry(c,source),NULL);
   if(!g) return source;
   if(g->width<1200) { free(g); return source; }
   static unsigned n;
   if(n++<4) fprintf(stderr,"inject Present pixmap=0x%x %ux%u xoff=%s src_eye=%s\n",source,g->width,g->height,getenv("X_OFF")?getenv("X_OFF"):"0",getenv("SRC_W")?getenv("SRC_W"):"unchanged");
   if(getenv("X_OFF")) *xoff=atoi(getenv("X_OFF"));
   if(!getenv("SRC_W")) { free(g); return source; }
   unsigned eye=g->width/2, width=atoi(getenv("SRC_W"));
   xcb_pixmap_t dest=xcb_generate_id(c); xcb_gcontext_t gc=xcb_generate_id(c);
   xcb_create_pixmap(c,g->depth,dest,g->root,2*width,g->height);
   xcb_create_gc(c,gc,dest,0,NULL);
   xcb_copy_area(c,source,dest,gc,0,0,0,0,width,g->height);
   xcb_copy_area(c,source,dest,gc,eye,0,width,0,width,g->height);
   xcb_free_gc(c,gc); free(g);
   return dest;
}


static _Thread_local bool inside;
static xcb_pixmap_t request_image(xcb_connection_t *c, struct iovec *v,
 const xcb_protocol_request_t *r, xcb_pixmap_t **field)
{
   if (!r->ext || strcmp(r->ext->name,"Present")) return XCB_NONE;
   int16_t x;
   xcb_pixmap_t before, after;
   if(r->opcode==XCB_PRESENT_PIXMAP) {
      xcb_present_pixmap_request_t *p=v[0].iov_base;
      before=p->pixmap; x=p->x_off; after=injected(c,before,&x);
      p->pixmap=after; p->x_off=x; *field=&p->pixmap;
   } else if(r->opcode==XCB_PRESENT_PIXMAP_SYNCED) {
      xcb_present_pixmap_synced_request_t *p=v[0].iov_base;
      before=p->pixmap; x=p->x_off; after=injected(c,before,&x);
      p->pixmap=after; p->x_off=x; *field=&p->pixmap;
   } else return XCB_NONE;
   return after!=before ? after : XCB_NONE;
}
unsigned int xcb_send_request(xcb_connection_t *c,int flags,struct iovec *v,const xcb_protocol_request_t *r)
{
   static __typeof__(&xcb_send_request) real;
   if(!real) real=symbol("xcb_send_request");
   if(inside) return real(c,flags,v,r);
   inside=true; xcb_pixmap_t *field=NULL;
   xcb_pixmap_t changed=request_image(c,v,r,&field);
   unsigned int serial=real(c,flags,v,r);
   if(changed) xcb_free_pixmap(c,changed);
   inside=false; return serial;
}
uint64_t xcb_send_request64(xcb_connection_t *c,int flags,struct iovec *v,const xcb_protocol_request_t *r)
{
   static __typeof__(&xcb_send_request64) real;
   if(!real) real=symbol("xcb_send_request64");
   if(inside) return real(c,flags,v,r);
   inside=true; xcb_pixmap_t *field=NULL;
   xcb_pixmap_t changed=request_image(c,v,r,&field);
   uint64_t serial=real(c,flags,v,r);
   if(changed) xcb_free_pixmap(c,changed);
   inside=false; return serial;
}
