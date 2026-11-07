/* A desktop that announces another stereo support version (STEREO_SHIM_SUPPORT, default 4), for the negative paths: preload it. */
#include <stdlib.h>
unsigned stereo_supported_x11(void *display)
{
    (void)display;
    const char *v = getenv("STEREO_SHIM_SUPPORT");
    return v ? (unsigned)atoi(v) : 4;
}

/* STEREO_SHIM_WAYLAND=1: the declaration of a Wayland surface is refused */
int stereo_declare_wayland(void *surface, int layout, int content_class, unsigned subclass)
{
    (void)surface; (void)layout; (void)content_class; (void)subclass;
    return -22;
}
