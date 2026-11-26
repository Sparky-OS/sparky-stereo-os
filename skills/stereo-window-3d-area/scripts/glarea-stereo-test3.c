/* SPDX-License-Identifier: MIT */
/*
 * A small GTK 3 program for the proof of a stereo GtkGLArea: an ordinary window with a label, buttons, a check
 * button and a text, and one GtkGLArea in it. The area draws with scissored clears only, so any GL or GLES
 * context can run it: the left view red with the tag LEFT, the right view blue with the tag RIGHT, a frame
 * number in both, a white frame one pixel wide around the view and a white square in its middle.
 *
 * It runs against GTK builds with and without the stereo GtkGLArea API: the properties, the eye getter and the colour
 * states are looked up at run time, so one binary is the control on Debian's gtk+3.0 and the test on ours.
 * The GTK 4 program of milestone 1 is its model; the options are the same, with --headerbar added.
 *
 *   glarea-stereo-test3 [--stereo] [--swap] [--opacity X] [--frame N] [--size WxH] [--report FILE] [--quit-after SECS]
 *
 *   --stereo       ask for stereo (the property "stereo")
 *   --swap         draw red where the other eye is drawn (a swapped-eye model, the control that must fail)
 *   --opacity X    widget opacity of the area (below 1 a picture on a surface of its own cannot be: the failure case)
 *   --frame N      the frame number drawn (fixed, so two runs draw the same picture)
 *   --grow-after S the area asks for 600x340 after S seconds (resize while shown)
 *   --two          a second stereo area, 240x135, under the first
 *   --overlay      a yellow label drawn over the lower right of the area (2D drawn over the 3D area)
 *   --headerbar    the window has a header bar (client-side decorations: on X11 an alpha channel)
 *   --hide-after S    the area is hidden after S seconds and shown again S seconds later
 *   --toggle-after S  the property "stereo" goes off after S seconds and on again S seconds later
 *   --report FILE  writes the state after the quit-after time: stereo-shown, the error, the eyes the render handler saw
 *   --view-size WxH   each view of a stereo area is rendered at this size (gtk_gl_area_set_stereo_view_size)
 *   --bench        the area is rendered again at every frame of the frame clock; the report gains the frames drawn,
 *                  the time they took and the processor time of the program (user and system) over them
 *   --x11-sibling  on X11, a plain green X window, 120x80, is mapped over the lower right corner of the area, as a
 *                  child of the toplevel's X window (a sibling of the area's own child window)
 *   --scrolled     the area sits in a scrolled window half its size, so half of it is scrolled out
 *   --format NAME  the format of the area's picture: u8 (the default), u10, u16, f16 or f32 (GtkGLArea:format)
 *   --color-state NAME   srgb, srgb-linear, rec2100-pq, rec2100-linear or rec2100-hlg (GtkGLArea:color-state)
 *   --patch R,G,B  (several) instead of the LEFT and RIGHT pictures the area draws a green frame, an eye tag (red in
 *                  the left view, blue in the right, white in a 2D area), the patches side by side over its lower half,
 *                  each with these encoded values, and over them a ramp of 256 steps over 1/256 of the range from 0.5;
 *                  the report gains, for each view drawn, the number of different values the ramp holds in the area's own framebuffer
 */
#include <gtk/gtk.h>
#ifdef GDK_WINDOWING_X11
#include <gdk/gdkx.h>
#include <X11/Xlib.h>
#endif
#include <epoxy/gl.h>
#include <dlfcn.h>
#include <sys/resource.h>
#include <glib-unix.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int (*EyeFunc) (GtkGLArea *);
typedef gpointer (*StateFunc) (void);

static gboolean opt_stereo, opt_swap;
static double opt_opacity = 1.0;
static int opt_grow, opt_toggle, opt_hide, opt_overlay, opt_two, opt_headerbar;
static int opt_frame = 7, opt_w = 480, opt_h = 270, opt_quit = 0;
static const char *opt_report;
static int opt_view_w, opt_view_h, opt_bench, opt_sibling, opt_scrolled;
static const char *opt_format, *opt_color_state;
static float patches[16][3];
static int n_patches, ramp_levels[3] = { -1, -1, -1 };
static char ramp_note[80];
static gint64 bench_start, bench_end;
static double bench_cpu_start, bench_cpu_end;
static int bench_frames;
static EyeFunc get_eye;
static int eyes_seen[3];
static int renders;
static char renderer[200];
static GtkApplication *app;

/* 5x7 glyphs, one row per byte, bit 4 on the left */
static const struct { char c; guint8 rows[7]; } font[] = {
  { 'L', { 16, 16, 16, 16, 16, 16, 31 } }, { 'E', { 31, 16, 16, 30, 16, 16, 31 } },
  { 'F', { 31, 16, 16, 30, 16, 16, 16 } }, { 'T', { 31, 4, 4, 4, 4, 4, 4 } },
  { 'R', { 30, 17, 17, 30, 20, 18, 17 } }, { 'I', { 14, 4, 4, 4, 4, 4, 14 } },
  { 'G', { 14, 17, 16, 23, 17, 17, 14 } }, { 'H', { 17, 17, 17, 31, 17, 17, 17 } },
  { 'M', { 17, 27, 21, 21, 17, 17, 17 } }, { 'O', { 14, 17, 17, 17, 17, 17, 14 } },
  { 'N', { 17, 25, 21, 19, 17, 17, 17 } },
  { '0', { 14, 17, 19, 21, 25, 17, 14 } }, { '1', { 4, 12, 4, 4, 4, 4, 14 } },
  { '2', { 14, 17, 1, 2, 4, 8, 31 } }, { '3', { 30, 1, 1, 14, 1, 1, 30 } },
  { '4', { 2, 6, 10, 18, 31, 2, 2 } }, { '5', { 31, 16, 30, 1, 1, 17, 14 } },
  { '6', { 6, 8, 16, 30, 17, 17, 14 } }, { '7', { 31, 1, 2, 4, 8, 8, 8 } },
  { '8', { 14, 17, 17, 14, 17, 17, 14 } }, { '9', { 14, 17, 17, 15, 1, 2, 12 } },
};

static void
rect (int x, int y, int w, int h, float r, float g, float b)
{
  glScissor (x, y, w, h);
  glClearColor (r, g, b, 1);
  glClear (GL_COLOR_BUFFER_BIT);
}

static void
text (const char *s, int x, int y_top, int px, int height)
{
  for (; *s; s++, x += 6 * px)
    for (gsize k = 0; k < G_N_ELEMENTS (font); k++)
      if (font[k].c == *s)
        for (int row = 0; row < 7; row++)
          for (int col = 0; col < 5; col++)
            if (font[k].rows[row] & (16 >> col))
              rect (x + col * px, height - (y_top + (row + 1) * px), px, px, 1, 1, 1);
}

static gboolean
render (GtkGLArea *area, GdkGLContext *context, gpointer data)
{
  int scale = gtk_widget_get_scale_factor (GTK_WIDGET (area));
  int w = gtk_widget_get_allocated_width (GTK_WIDGET (area)) * scale;
  int h = gtk_widget_get_allocated_height (GTK_WIDGET (area)) * scale;
  int eye = get_eye ? get_eye (area) : 0;
  float r = 0, g = 0.5f, b = 0;
  const char *tag = "MONO";
  char number[16];

  /* an area that asks for stereo draws into the framebuffer GTK set the viewport for: the view's own size */
  if (eye != 0)
    {
      int viewport[4];

      glGetIntegerv (GL_VIEWPORT, viewport);
      w = viewport[2];
      h = viewport[3];
    }

  if (opt_bench && eye != 2)
    {
      struct rusage usage;

      getrusage (RUSAGE_SELF, &usage);
      bench_end = g_get_monotonic_time ();
      bench_cpu_end = usage.ru_utime.tv_sec + usage.ru_stime.tv_sec + (usage.ru_utime.tv_usec + usage.ru_stime.tv_usec) / 1e6;
      /* the first frames set the windows up: the count starts at the thirtieth */
      if (++bench_frames == 30)
        {
          bench_start = bench_end;
          bench_cpu_start = bench_cpu_end;
        }
    }

  eyes_seen[eye]++;
  renders++;
  if (!renderer[0])
    g_snprintf (renderer, sizeof renderer, "%s / %s", (const char *) glGetString (GL_VENDOR), (const char *) glGetString (GL_RENDERER));

  if (eye == 1 || eye == 2)
    {
      gboolean left = (eye == 1) != opt_swap;
      r = left ? 1 : 0;
      b = left ? 0 : 1;
      g = 0;
      tag = eye == 1 ? "LEFT" : "RIGHT";
    }

  if (n_patches > 0)
    {
      int frame = 4, tag = h / 6, i;
      int step = (w - 2 * frame) / 256 > 0 ? (w - 2 * frame) / 256 : 1;

      glEnable (GL_SCISSOR_TEST);
      rect (0, 0, w, h, 0, 1, 0);
      rect (frame, frame, w - 2 * frame, h - 2 * frame, 0, 0, 0);
      for (i = 0; i < n_patches; i++)
        {
          int x0 = frame + tag + i * (w - 2 * frame - tag) / n_patches;
          int x1 = frame + tag + (i + 1) * (w - 2 * frame - tag) / n_patches;

          rect (x0, frame, x1 - x0, h / 2 - frame, patches[i][0], patches[i][1], patches[i][2]);
        }
      rect (frame, frame, tag, tag, eye == 2 ? 0 : 1, eye == 0 ? 1 : 0, eye == 1 ? 0 : 1);
      for (i = 0; i < 256 && frame + (i + 1) * step <= w - frame; i++)
        {
          float v = 0.5f + i / 65536.0f;

          rect (frame + i * step, h / 2, step, h / 2 - frame, v, v, v);
        }
      glDisable (GL_SCISSOR_TEST);

      /* what the ramp holds in the framebuffer the program drew into, read back in a type that keeps its depth: the
       * type of the area's format first, then the others (OpenGL ES reads a framebuffer only in its own type) */
      if (ramp_levels[eye] < 0)
        {
          static const struct { GLenum type; const char *name; int bytes; } types[] = {
            { GL_FLOAT, "float", 16 }, { GL_UNSIGNED_SHORT, "16-bit", 8 },
            { GL_UNSIGNED_INT_2_10_10_10_REV, "10-bit", 4 }, { GL_UNSIGNED_BYTE, "8-bit", 4 },
          };
          int order[4] = { 0, 1, 2, 3 };
          guchar *row = g_malloc0 (16 * (gsize) w);
          int fb = 0, t;

          if (opt_format && !strcmp (opt_format, "u16")) { order[0] = 1; order[1] = 0; }
          else if (opt_format && !strcmp (opt_format, "u10")) { order[0] = 2; order[1] = 0; order[2] = 1; }
          else if (!opt_format || !strcmp (opt_format, "u8")) { order[0] = 3; order[1] = 0; order[2] = 1; order[3] = 2; }
          glGetIntegerv (GL_FRAMEBUFFER_BINDING, &fb);
          glBindFramebuffer (GL_READ_FRAMEBUFFER, fb);
          glReadBuffer (GL_COLOR_ATTACHMENT0);
          glPixelStorei (GL_PACK_ALIGNMENT, 1);
          ramp_levels[eye] = 0;
          g_strlcpy (ramp_note, "(the framebuffer could not be read)", sizeof ramp_note);
          for (t = 0; t < 4; t++)
            {
              int levels = 0, bytes = types[order[t]].bytes;
              guchar last[4] = { 0 };

              while (glGetError () != GL_NO_ERROR)
                ;
              /* the ramp is the upper half of the picture: OpenGL's rows count from the bottom */
              glReadPixels (0, 3 * h / 4, w, 1, GL_RGBA, types[order[t]].type, row);
              if (glGetError () != GL_NO_ERROR)
                continue;
              for (i = frame; i < frame + 256 * step && i < w - frame; i++)
                {
                  guchar red[4] = { 0 };

                  /* the red sample of the pixel: the first quarter of a float or 16-bit pixel, the low ten bits of a
                   * 10-bit one, the first byte of an 8-bit one */
                  if (types[order[t]].type == GL_UNSIGNED_INT_2_10_10_10_REV)
                    {
                      guint32 v;

                      memcpy (&v, row + 4 * i, 4);
                      v &= 0x3ff;
                      memcpy (red, &v, 4);
                    }
                  else
                    memcpy (red, row + (gsize) bytes * i, bytes / 4);
                  if (levels == 0 || memcmp (red, last, 4))
                    {
                      memcpy (last, red, 4);
                      levels++;
                    }
                }
              ramp_levels[eye] = levels;
              g_snprintf (ramp_note, sizeof ramp_note, "(read as %s, %s)", types[order[t]].name,
                          epoxy_is_desktop_gl () ? "OpenGL" : "OpenGL ES");
              break;
            }
          g_free (row);
        }
      return TRUE;
    }

  glEnable (GL_SCISSOR_TEST);
  rect (0, 0, w, h, r, g, b);
  rect (0, 0, w, 1, 1, 1, 1);
  rect (0, h - 1, w, 1, 1, 1, 1);
  rect (0, 0, 1, h, 1, 1, 1);
  rect (w - 1, 0, 1, h, 1, 1, 1);
  rect (w / 2 - h / 8, h / 2 - h / 8, h / 4, h / 4, 1, 1, 1);
  text (tag, 12, 12, h / 28 ? h / 28 : 1, h);
  g_snprintf (number, sizeof number, "%d", opt_frame);
  text (number, 12, 12 + 9 * (h / 28 ? h / 28 : 1), h / 28 ? h / 28 : 1, h);
  glDisable (GL_SCISSOR_TEST);
  return TRUE;
}

static gboolean
grow (gpointer data)
{
  gtk_widget_set_size_request (GTK_WIDGET (data), 600, 340);
  return G_SOURCE_REMOVE;
}

static gboolean
show_again (gpointer data)
{
  gtk_widget_set_visible (GTK_WIDGET (data), TRUE);
  return G_SOURCE_REMOVE;
}

static gboolean
hide_now (gpointer data)
{
  gtk_widget_set_visible (GTK_WIDGET (data), FALSE);
  g_timeout_add_seconds (opt_hide, show_again, data);
  return G_SOURCE_REMOVE;
}

static gboolean
set_stereo_on (gpointer data)
{
  g_object_set (data, "stereo", TRUE, NULL);
  return G_SOURCE_REMOVE;
}

static gboolean
set_stereo_off (gpointer data)
{
  g_object_set (data, "stereo", FALSE, NULL);
  g_timeout_add_seconds (opt_toggle, set_stereo_on, data);
  return G_SOURCE_REMOVE;
}

static gboolean
finish (gpointer data)
{
  GtkWidget *area = data;
  gboolean stereo = FALSE, shown = FALSE;
  GError *error = NULL;
  FILE *f = opt_report ? fopen (opt_report, "w") : stdout;

  if (g_object_class_find_property (G_OBJECT_GET_CLASS (area), "stereo"))
    {
      g_object_get (area, "stereo", &stereo, "stereo-shown", &shown, "stereo-error", &error, NULL);
      fprintf (f, "api: yes\n");
    }
  else
    fprintf (f, "api: no\n");
  fprintf (f, "renderer: %s\nstereo: %d\nstereo-shown: %d\nstereo-error: %s\nrenders: %d\neyes-seen: none=%d left=%d right=%d\n",
           renderer, stereo, shown, error ? error->message : "none", renders, eyes_seen[0], eyes_seen[1], eyes_seen[2]);
  if (g_object_class_find_property (G_OBJECT_GET_CLASS (area), "format"))
    {
      GParamSpec *spec = g_object_class_find_property (G_OBJECT_GET_CLASS (area), "format");
      GEnumClass *formats = g_type_class_ref (spec->value_type);
      int format = 0;
      GError *area_error = gtk_gl_area_get_error (GTK_GL_AREA (area));

      g_object_get (area, "format", &format, NULL);
      fprintf (f, "format: %s\ncolor-state-asked: %s\nerror: %s\n", g_enum_get_value (formats, format)->value_nick,
               opt_color_state ? opt_color_state : "srgb", area_error ? area_error->message : "none");
      g_type_class_unref (formats);
    }
  if (n_patches > 0)
    fprintf (f, "ramp-levels: none=%d left=%d right=%d %s\n", ramp_levels[0], ramp_levels[1], ramp_levels[2], ramp_note);
  if (opt_bench && bench_frames > 30)
    fprintf (f, "bench-frames: %d\nbench-wall-ms: %.1f\nbench-cpu-ms: %.1f\n", bench_frames - 30,
             (bench_end - bench_start) / 1000.0, (bench_cpu_end - bench_cpu_start) * 1000.0);
  if (f != stdout)
    fclose (f);
  g_clear_error (&error);
  g_application_quit (G_APPLICATION (app));
  return G_SOURCE_REMOVE;
}

static gboolean
bench_tick (GtkWidget *widget, GdkFrameClock *clock, gpointer data)
{
  gtk_gl_area_queue_render (GTK_GL_AREA (widget));
  return G_SOURCE_CONTINUE;
}

#ifdef GDK_WINDOWING_X11
static gboolean
map_sibling (gpointer data)
{
  GtkWidget *area = data;
  GtkWidget *toplevel = gtk_widget_get_toplevel (area);
  GdkWindow *window = gtk_widget_get_window (toplevel);
  int x = 0, y = 0;

  if (GDK_IS_X11_WINDOW (window) && gtk_widget_translate_coordinates (area, toplevel, 0, 0, &x, &y))
    {
      Display *dpy = gdk_x11_display_get_xdisplay (gdk_window_get_display (window));
      int scale = gdk_window_get_scale_factor (window);
      XSetWindowAttributes attributes = { 0, };
      XWindowAttributes top;
      Window sibling;

      XGetWindowAttributes (dpy, gdk_x11_window_get_xid (window), &top);
      attributes.background_pixel = 0xff00ff00;
      attributes.border_pixel = 0;
      attributes.colormap = top.colormap;
      sibling = XCreateWindow (dpy, gdk_x11_window_get_xid (window),
                               (x + gtk_widget_get_allocated_width (area)) * scale - 60,
                               (y + gtk_widget_get_allocated_height (area)) * scale - 40,
                               120, 80, 0, top.depth, InputOutput, top.visual,
                               CWBackPixel | CWBorderPixel | CWColormap, &attributes);
      XMapRaised (dpy, sibling);
      XFlush (dpy);
    }
  return G_SOURCE_REMOVE;
}
#endif

static void
set_format_and_state (GtkWidget *area)
{
  if (opt_format && g_object_class_find_property (G_OBJECT_GET_CLASS (area), "format"))
    {
      /* GdkMemoryFormat's values, which are GTK 4's */
      static const struct { const char *name; int format; } formats[] = {
        { "u8", 2 }, { "u10", 68 }, { "u16", 10 }, { "f16", 13 }, { "f32", 16 },
      };

      for (gsize i = 0; i < G_N_ELEMENTS (formats); i++)
        if (!strcmp (formats[i].name, opt_format))
          g_object_set (area, "format", formats[i].format, NULL);
    }
  if (opt_color_state && g_object_class_find_property (G_OBJECT_GET_CLASS (area), "color-state"))
    {
      gpointer state = NULL;
      StateFunc getter = NULL;

      if (!strcmp (opt_color_state, "srgb"))
        getter = (StateFunc) dlsym (RTLD_DEFAULT, "gdk_color_state_get_srgb");
      else if (!strcmp (opt_color_state, "srgb-linear"))
        getter = (StateFunc) dlsym (RTLD_DEFAULT, "gdk_color_state_get_srgb_linear");
      else if (!strcmp (opt_color_state, "rec2100-pq"))
        getter = (StateFunc) dlsym (RTLD_DEFAULT, "gdk_color_state_get_rec2100_pq");
      else if (!strcmp (opt_color_state, "rec2100-linear"))
        getter = (StateFunc) dlsym (RTLD_DEFAULT, "gdk_color_state_get_rec2100_linear");
      if (getter)
        state = getter ();
      else if (!strcmp (opt_color_state, "rec2100-hlg"))
        {
          /* ITU-T H.273: colour primaries 9 (Rec. 2020), transfer characteristics 18 (hybrid log-gamma), RGB, full range */
          gpointer (*cicp_new) (void) = dlsym (RTLD_DEFAULT, "gdk_cicp_params_new");
          void (*set) (gpointer, guint);
          gpointer (*build) (gpointer, GError **) = dlsym (RTLD_DEFAULT, "gdk_cicp_params_build_color_state");
          gpointer cicp = cicp_new ();

          set = dlsym (RTLD_DEFAULT, "gdk_cicp_params_set_color_primaries"); set (cicp, 9);
          set = dlsym (RTLD_DEFAULT, "gdk_cicp_params_set_transfer_function"); set (cicp, 18);
          set = dlsym (RTLD_DEFAULT, "gdk_cicp_params_set_matrix_coefficients"); set (cicp, 0);
          set = dlsym (RTLD_DEFAULT, "gdk_cicp_params_set_range"); set (cicp, 1);
          state = build (cicp, NULL);
          g_object_unref (cicp);
        }
      if (state != NULL)
        g_object_set (area, "color-state", state, NULL);
    }
}

static void
activate (GApplication *application, gpointer data)
{
  GtkWidget *window = gtk_application_window_new (GTK_APPLICATION (application));
  GtkWidget *box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 8);
  GtkWidget *bar = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 8);
  GtkWidget *area = gtk_gl_area_new ();
  GtkWidget *area_row = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 0);
  GtkWidget *label = gtk_label_new ("GtkGLArea in an ordinary window");

  gtk_window_set_title (GTK_WINDOW (window), "GtkGLArea stereo test");
  if (opt_headerbar)
    {
      GtkWidget *header = gtk_header_bar_new ();

      gtk_header_bar_set_title (GTK_HEADER_BAR (header), "GtkGLArea stereo test");
      gtk_header_bar_set_show_close_button (GTK_HEADER_BAR (header), TRUE);
      gtk_window_set_titlebar (GTK_WINDOW (window), header);
    }
  gtk_window_set_default_size (GTK_WINDOW (window), 640, opt_two ? 620 : 460);
  g_object_set (box, "margin", 12, NULL);
  gtk_box_pack_start (GTK_BOX (box), label, FALSE, FALSE, 0);
  gtk_box_pack_start (GTK_BOX (bar), gtk_button_new_with_label ("One"), FALSE, FALSE, 0);
  gtk_box_pack_start (GTK_BOX (bar), gtk_button_new_with_label ("Two"), FALSE, FALSE, 0);
  gtk_box_pack_start (GTK_BOX (bar), gtk_check_button_new_with_label ("Check"), FALSE, FALSE, 0);
  gtk_box_pack_start (GTK_BOX (box), bar, FALSE, FALSE, 0);
  gtk_widget_set_size_request (area, opt_w, opt_h);
  gtk_widget_set_halign (area, GTK_ALIGN_CENTER);
  gtk_widget_set_hexpand (area_row, TRUE);
  gtk_widget_set_opacity (area, opt_opacity);
  g_signal_connect (area, "render", G_CALLBACK (render), NULL);
  if (opt_stereo && g_object_class_find_property (G_OBJECT_GET_CLASS (area), "stereo"))
    g_object_set (area, "stereo", TRUE, NULL);
  if (opt_view_w > 0 && g_object_class_find_property (G_OBJECT_GET_CLASS (area), "stereo-view-width"))
    g_object_set (area, "stereo-view-width", opt_view_w, "stereo-view-height", opt_view_h, NULL);
  set_format_and_state (area);
  if (opt_bench)
    gtk_widget_add_tick_callback (area, bench_tick, NULL, NULL);
  if (opt_scrolled)
    {
      GtkWidget *scrolled = gtk_scrolled_window_new (NULL, NULL);

      gtk_widget_set_size_request (scrolled, opt_w / 2, opt_h + 20);
      gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (scrolled), GTK_POLICY_ALWAYS, GTK_POLICY_NEVER);
      gtk_widget_set_halign (scrolled, GTK_ALIGN_CENTER);
      gtk_container_add (GTK_CONTAINER (scrolled), area);
      gtk_box_pack_start (GTK_BOX (area_row), scrolled, TRUE, FALSE, 0);
    }
  else if (opt_overlay)
    {
      GtkWidget *overlay = gtk_overlay_new ();
      GtkWidget *tag = gtk_label_new ("OVERLAY");
      GtkCssProvider *css = gtk_css_provider_new ();

      gtk_css_provider_load_from_data (css, "label.tag { background: #ffff00; color: #000000; padding: 6px 12px; }", -1, NULL);
      gtk_style_context_add_provider_for_screen (gdk_screen_get_default (), GTK_STYLE_PROVIDER (css),
                                                 GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
      gtk_style_context_add_class (gtk_widget_get_style_context (tag), "tag");
      gtk_widget_set_halign (tag, GTK_ALIGN_END);
      gtk_widget_set_valign (tag, GTK_ALIGN_END);
      gtk_widget_set_margin_end (tag, 20);
      gtk_widget_set_margin_bottom (tag, 20);
      gtk_container_add (GTK_CONTAINER (overlay), area);
      gtk_overlay_add_overlay (GTK_OVERLAY (overlay), tag);
      gtk_widget_set_halign (overlay, GTK_ALIGN_CENTER);
      gtk_box_pack_start (GTK_BOX (area_row), overlay, TRUE, FALSE, 0);
    }
  else
    gtk_box_pack_start (GTK_BOX (area_row), area, TRUE, FALSE, 0);
  gtk_box_pack_start (GTK_BOX (box), area_row, FALSE, FALSE, 0);
  if (opt_two)
    {
      GtkWidget *second = gtk_gl_area_new ();

      gtk_widget_set_size_request (second, 240, 135);
      gtk_widget_set_halign (second, GTK_ALIGN_CENTER);
      g_signal_connect (second, "render", G_CALLBACK (render), NULL);
      if (opt_stereo && g_object_class_find_property (G_OBJECT_GET_CLASS (second), "stereo"))
        g_object_set (second, "stereo", TRUE, NULL);
      gtk_box_pack_start (GTK_BOX (box), second, FALSE, FALSE, 0);
    }
  gtk_box_pack_start (GTK_BOX (box), gtk_label_new ("Text under the area, the same in both eyes"), FALSE, FALSE, 0);
  gtk_container_add (GTK_CONTAINER (window), box);
  gtk_widget_show_all (window);
  gtk_window_present (GTK_WINDOW (window));
  if (opt_grow > 0)
    g_timeout_add_seconds (opt_grow, grow, area);
  if (opt_toggle > 0)
    g_timeout_add_seconds (opt_toggle, set_stereo_off, area);
  if (opt_hide > 0)
    g_timeout_add_seconds (opt_hide, hide_now, area);
  if (opt_quit > 0)
    g_timeout_add_seconds (opt_quit, finish, area);
  /* SIGTERM ends the program as the quit-after time does, with its report */
  g_unix_signal_add (SIGTERM, finish, area);
#ifdef GDK_WINDOWING_X11
  if (opt_sibling)
    g_timeout_add_seconds (2, map_sibling, area);
#endif
}

int
main (int argc, char **argv)
{
  int status;

  for (int i = 1; i < argc; i++)
    {
      if (!strcmp (argv[i], "--stereo")) opt_stereo = TRUE;
      else if (!strcmp (argv[i], "--swap")) opt_swap = TRUE;
      else if (!strcmp (argv[i], "--opacity") && i + 1 < argc) opt_opacity = atof (argv[++i]);
      else if (!strcmp (argv[i], "--frame") && i + 1 < argc) opt_frame = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--size") && i + 1 < argc) sscanf (argv[++i], "%dx%d", &opt_w, &opt_h);
      else if (!strcmp (argv[i], "--two")) opt_two = TRUE;
      else if (!strcmp (argv[i], "--headerbar")) opt_headerbar = TRUE;
      else if (!strcmp (argv[i], "--view-size") && i + 1 < argc) sscanf (argv[++i], "%dx%d", &opt_view_w, &opt_view_h);
      else if (!strcmp (argv[i], "--bench")) opt_bench = TRUE;
      else if (!strcmp (argv[i], "--x11-sibling")) opt_sibling = TRUE;
      else if (!strcmp (argv[i], "--scrolled")) opt_scrolled = TRUE;
      else if (!strcmp (argv[i], "--format") && i + 1 < argc) opt_format = argv[++i];
      else if (!strcmp (argv[i], "--color-state") && i + 1 < argc) opt_color_state = argv[++i];
      else if (!strcmp (argv[i], "--patch") && i + 1 < argc && n_patches < 16)
        {
          sscanf (argv[++i], "%f,%f,%f", &patches[n_patches][0], &patches[n_patches][1], &patches[n_patches][2]);
          n_patches++;
        }
      else if (!strcmp (argv[i], "--overlay")) opt_overlay = TRUE;
      else if (!strcmp (argv[i], "--grow-after") && i + 1 < argc) opt_grow = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--hide-after") && i + 1 < argc) opt_hide = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--toggle-after") && i + 1 < argc) opt_toggle = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--report") && i + 1 < argc) opt_report = argv[++i];
      else if (!strcmp (argv[i], "--quit-after") && i + 1 < argc) opt_quit = atoi (argv[++i]);
      else { fprintf (stderr, "unknown option %s\n", argv[i]); return 2; }
    }
  get_eye = (EyeFunc) dlsym (RTLD_DEFAULT, "gtk_gl_area_get_current_eye");
  app = gtk_application_new ("org.sparkyos.GlAreaStereoTest3", G_APPLICATION_NON_UNIQUE);
  g_signal_connect (app, "activate", G_CALLBACK (activate), NULL);
  status = g_application_run (G_APPLICATION (app), 1, argv);
  g_object_unref (app);
  return status;
}
