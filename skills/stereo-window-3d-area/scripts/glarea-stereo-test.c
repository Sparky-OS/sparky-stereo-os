/* SPDX-License-Identifier: MIT */
/*
 * A small GTK 4 program for the proof of a stereo GtkGLArea: an ordinary window with a label, buttons, a check
 * button and a text, and one GtkGLArea in it. The area draws with scissored clears only, so any GL or GLES
 * context can run it: the left view red with the tag LEFT, the right view blue with the tag RIGHT, a frame
 * number in both, a white frame one pixel wide around the view and a white square in its middle.
 *
 * It runs against GTK builds with and without the stereo GtkGLArea API: the property and the getter are looked up
 * at run time, so one binary is the control on Debian's gtk4 and the test on ours.
 *
 *   glarea-stereo-test [--stereo] [--swap] [--opacity X] [--frame N] [--size WxH] [--report FILE] [--quit-after SECS]
 *
 *   --stereo       ask for stereo (the property "stereo")
 *   --swap         draw red where the other eye is drawn (a swapped-eye model, the control that must fail)
 *   --opacity X    widget opacity of the area (below 1 GTK cannot offload it: the failure case)
 *   --frame N      the frame number drawn (fixed, so two runs draw the same picture)
 *   --offload      puts the area in a GtkGraphicsOffload (GTK 4.14 and later), the control for the offload path itself
 *   --grow-after S the area asks for 600x340 after S seconds (resize while shown)
 *   --overlay      a yellow label drawn over the lower right of the area (2D drawn over the 3D area)
 *   --hide-after S    the area is hidden after S seconds and shown again S seconds later
 *   --toggle-after S  the property "stereo" goes off after S seconds and on again S seconds later
 *   --report FILE  writes the state after the quit-after time: stereo-shown, the error, the eyes the render handler saw
 */
#include <gtk/gtk.h>
#include <epoxy/gl.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int (*EyeFunc) (GtkGLArea *);

static gboolean opt_stereo, opt_swap;
static double opt_opacity = 1.0;
static int opt_grow, opt_toggle, opt_offload, opt_hide, opt_overlay;
static int opt_frame = 7, opt_w = 480, opt_h = 270, opt_quit = 0;
static const char *opt_report;
static EyeFunc get_eye;
static int eyes_seen[3];
static int renders;
static char renderer[200];

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
  int w = gtk_widget_get_width (GTK_WIDGET (area)) * scale;
  int h = gtk_widget_get_height (GTK_WIDGET (area)) * scale;
  int eye = get_eye ? get_eye (area) : 0;
  float r = 0, g = 0.5f, b = 0;
  const char *tag = "MONO";
  char number[16];

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
  if (f != stdout)
    fclose (f);
  g_clear_error (&error);
  g_application_quit (g_application_get_default ());
  return G_SOURCE_REMOVE;
}

static void
activate (GApplication *app, gpointer data)
{
  GtkWidget *window = gtk_application_window_new (GTK_APPLICATION (app));
  GtkWidget *box = gtk_box_new (GTK_ORIENTATION_VERTICAL, 8);
  GtkWidget *bar = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 8);
  GtkWidget *area = gtk_gl_area_new ();
  GtkWidget *area_row = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 0);
  GtkWidget *label = gtk_label_new ("GtkGLArea in an ordinary window");

  gtk_window_set_title (GTK_WINDOW (window), "GtkGLArea stereo test");
  gtk_window_set_default_size (GTK_WINDOW (window), 640, 460);
  gtk_widget_set_margin_top (box, 12);
  gtk_widget_set_margin_bottom (box, 12);
  gtk_widget_set_margin_start (box, 12);
  gtk_widget_set_margin_end (box, 12);
  gtk_box_append (GTK_BOX (box), label);
  gtk_box_append (GTK_BOX (bar), gtk_button_new_with_label ("One"));
  gtk_box_append (GTK_BOX (bar), gtk_button_new_with_label ("Two"));
  gtk_box_append (GTK_BOX (bar), gtk_check_button_new_with_label ("Check"));
  gtk_box_append (GTK_BOX (box), bar);
  gtk_widget_set_size_request (area, opt_w, opt_h);
  gtk_widget_set_halign (area, GTK_ALIGN_CENTER);
  gtk_widget_set_hexpand (area_row, TRUE);
  gtk_widget_set_opacity (area, opt_opacity);
  g_signal_connect (area, "render", G_CALLBACK (render), NULL);
  if (opt_stereo && g_object_class_find_property (G_OBJECT_GET_CLASS (area), "stereo"))
    g_object_set (area, "stereo", TRUE, NULL);
  if (opt_overlay)
    {
      GtkWidget *overlay = gtk_overlay_new ();
      GtkWidget *tag = gtk_label_new ("OVERLAY");
      GtkCssProvider *css = gtk_css_provider_new ();

      gtk_css_provider_load_from_string (css, "label.tag { background: #ffff00; color: #000000; padding: 6px 12px; }");
      gtk_style_context_add_provider_for_display (gdk_display_get_default (), GTK_STYLE_PROVIDER (css),
                                                  GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
      gtk_widget_add_css_class (tag, "tag");
      gtk_widget_set_halign (tag, GTK_ALIGN_END);
      gtk_widget_set_valign (tag, GTK_ALIGN_END);
      gtk_widget_set_margin_end (tag, 20);
      gtk_widget_set_margin_bottom (tag, 20);
      gtk_overlay_set_child (GTK_OVERLAY (overlay), area);
      gtk_overlay_add_overlay (GTK_OVERLAY (overlay), tag);
      gtk_widget_set_halign (overlay, GTK_ALIGN_CENTER);
      gtk_box_append (GTK_BOX (area_row), overlay);
    }
  else if (opt_offload)
    gtk_box_append (GTK_BOX (area_row), gtk_graphics_offload_new (area));
  else
    gtk_box_append (GTK_BOX (area_row), area);
  gtk_box_append (GTK_BOX (box), area_row);
  gtk_box_append (GTK_BOX (box), gtk_label_new ("Text under the area, the same in both eyes"));
  gtk_window_set_child (GTK_WINDOW (window), box);
  gtk_window_present (GTK_WINDOW (window));
  if (opt_grow > 0)
    g_timeout_add_seconds (opt_grow, grow, area);
  if (opt_toggle > 0)
    g_timeout_add_seconds (opt_toggle, set_stereo_off, area);
  if (opt_hide > 0)
    g_timeout_add_seconds (opt_hide, hide_now, area);
  if (opt_quit > 0)
    g_timeout_add_seconds (opt_quit, finish, area);
}

int
main (int argc, char **argv)
{
  GtkApplication *app;
  int status;

  for (int i = 1; i < argc; i++)
    {
      if (!strcmp (argv[i], "--stereo")) opt_stereo = TRUE;
      else if (!strcmp (argv[i], "--swap")) opt_swap = TRUE;
      else if (!strcmp (argv[i], "--opacity") && i + 1 < argc) opt_opacity = atof (argv[++i]);
      else if (!strcmp (argv[i], "--frame") && i + 1 < argc) opt_frame = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--size") && i + 1 < argc) sscanf (argv[++i], "%dx%d", &opt_w, &opt_h);
      else if (!strcmp (argv[i], "--overlay")) opt_overlay = TRUE;
      else if (!strcmp (argv[i], "--offload")) opt_offload = TRUE;
      else if (!strcmp (argv[i], "--grow-after") && i + 1 < argc) opt_grow = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--hide-after") && i + 1 < argc) opt_hide = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--toggle-after") && i + 1 < argc) opt_toggle = atoi (argv[++i]);
      else if (!strcmp (argv[i], "--report") && i + 1 < argc) opt_report = argv[++i];
      else if (!strcmp (argv[i], "--quit-after") && i + 1 < argc) opt_quit = atoi (argv[++i]);
      else { fprintf (stderr, "unknown option %s\n", argv[i]); return 2; }
    }
  get_eye = (EyeFunc) dlsym (RTLD_DEFAULT, "gtk_gl_area_get_current_eye");
  app = gtk_application_new ("org.sparkyos.GlAreaStereoTest", G_APPLICATION_NON_UNIQUE);
  g_signal_connect (app, "activate", G_CALLBACK (activate), NULL);
  status = g_application_run (G_APPLICATION (app), 1, argv);
  g_object_unref (app);
  return status;
}
