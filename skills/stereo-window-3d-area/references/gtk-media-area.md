# A GTK 4 program's pictures and video in 3D (libstereo-gtk, ORDER 742)

For a program that shows decoded pictures or video frames in a GTK 4 window (HandBrake's preview, a viewer, a player) and has no GL area of its own.
GtkGLArea programs follow [gtk-glarea.md](gtk-glarea.md) instead.

## Recipe

1. Link `stereo-gtk` (package `libstereo-gtk-dev`, stereo-layer 1.23.0 and later; `pkg-config stereo-gtk`).
2. Make the window that holds the picture a `StereoGtkWindow` (or `StereoGtkApplicationWindow`).
   In a GtkBuilder file write `class="StereoGtkWindow"` and call `g_type_ensure(stereo_gtk_window_get_type())` before the builder loads it.
3. Put a `stereo_gtk_area_new()` over the program's own picture widget in a `GtkOverlay`, with `gtk_widget_set_can_target(area, FALSE)`, so the picture's click and motion controllers keep working.
4. For each frame: decide the packing in the policy's order (the file's entry in the shared store, then the stream's mark, then `stereo_policy_video_side_by_side_by_shape()`; the swap last), then `stereo_gtk_unpack(texture, layout, order, anaglyph, &left, &right, &error)`, `stereo_gtk_area_set_view_aspect(area, stereo_gtk_view_aspect(w, h, frame_aspect, layout))` and `stereo_gtk_area_set_pair(area, left, right)`.
   A played `GtkMediaStream` gives its frames on `invalidate-contents`: `gdk_paintable_get_current_image()` is a `GdkTexture`, and `gdk_paintable_get_intrinsic_aspect_ratio()` is the frame's display aspect.
5. Name every 2D widget drawn over the picture (the player's controls, a message) with `stereo_gtk_area_keep_above()`: the window cuts its hole around them, so they stay in the window, the same in both eyes.
6. The menu: `stereo_gtk_file_menu_new(file_changed, enable_changed, data)` and `stereo_gtk_file_menu_set_file(menu, path, stereo_source)`.
   It holds "Enable 3D", "Display Settings…" (Display Configuration), the 3D Input Format list of the C policy, "Not 3D" and "Swap left and right eyes", stored in the shared per-file store; the media file is never written.
   It shows only for a source that is 3D by its mark or shape, or has a stored entry.

## How it works

The area makes a `wl_subsurface` below the window's surface, declares it full side by side through libstereo-declare (`set_content(3)`), and gives it one shared-memory buffer holding the two views at their own size, with a `wp_viewport` destination at the picture's rectangle: Stereo KWin scales once, at the output.
The window masks the picture's rectangle out of its own drawing only while both views have been presented, so the subsurface shows through the hole; until then, or when 3D is off, the area draws the left view itself.
On X11 the same area is a child window declared with `stereo_declare_x11_child_place()`.

`stereo_gtk_unpack()` follows the Qt layer's rule (`storedView()`, `Picture::fromAnaglyph()`): side by side and quincunx give two half-width views, top and bottom and rows two half-height views, columns and checkerboard the view's own samples, the three anaglyph pairs two full-size colour reconstructions.
A picture and its depth map in one frame (side by side, top and bottom, four rows with graphics, four quarters with the background) are drawn by libstereo-dibr inside `stereo_gtk_unpack()`, cut and drawn as the Qt layer's `unpackWithDepth()` and `Picture::fromDepth()` do: the depth map's gray (qGray) as nearness, 8 bits, the library's one default (`stereo_dibr_options_default()`), the picture as the left eye. Nothing reads or changes the person's depth limits (since 1.23.1).
Frames in turn, both views in one block, multiview and a separate depth map need a second picture: `stereo_gtk_layout_needs_two_pictures(layout)` says so, `stereo_gtk_unpack(one picture)` fails with a translated sentence for the program to show, and `stereo_gtk_unpack_pair(first, second, layout, order, &left, &right, &error)` gives the eyes: two decoded pictures in turn (the first is the left eye unless the right comes first; sizes must match) or a picture and its depth map of any size. The Qt layer has the same rule for two pictures in turn, `Picture::fromViewsInTurn()`.
Where the second picture comes from is the program's, and pairs are counted from the source's first frame (H.264 and H.265 frame packing type 5, Matroska StereoMode 13 and 14), never from the program's own position: a played clip needs the source frame number of its first frame (Stereo HandBrake encodes the clip from a time range on a frame boundary and adds the clip's own frame number from `gtk_media_stream_get_timestamp()` and the frame rate); a still needs the other picture of its pair, the one after it for an even frame and the one before it for an odd one (Stereo HandBrake's scan keeps it as preview number + `HB_PREVIEW_NEIGHBOUR` and marks which).

## Traps

- Symptom: the program's controls vanish while 3D is shown.
  Cause: the window's mask removes everything drawn in the picture's rectangle, controls included.
  Fix: `stereo_gtk_area_keep_above()` for each widget over the picture.
  Found by: reading `window_snapshot()`: the inverted-alpha mask covers the whole window snapshot.
- Symptom: a full side-by-side source sits in the middle half of a wide empty box.
  Cause: the program sized its picture box for the packed frame (32:9).
  Fix: give the box the view's aspect while the pair is shown (HandBrake: `gtk_aspect_frame_set_ratio()`).
- Symptom: the area's events never reach the program.
  Cause: an overlay child takes the pointer.
  Fix: `gtk_widget_set_can_target(area, FALSE)`.
- Symptom: after the program turns its 3D area off and on again ("Enable 3D"), the area stays flat and the program's log says "Device or resource busy".
  Cause: up to libstereo-gtk 1.23.1 each new area set libstereo-declare up again; the library keeps one state per thread for the application on its display and answers EBUSY.
  Fix: libstereo-gtk 1.23.2 sets it up once per display.
  Found by: the area's `stereo-error` message in the program's log, then `stereo_declare_wayland_init()`'s `if (state.display) return -EBUSY`.
- Symptom: the program's 3D menu, whose button sits in an overlay that hides itself (a player's HUD), closes about 150 ms after it opens, and its item is never chosen.
  Cause: the overlay's own hide timer unmapped the button while the popover was open (GTK's enter and leave for the overlay can be out of step after a popover was used).
  Fix: keep the overlay shown while the menu's popover is visible (`notify::visible` on `gtk_menu_button_get_popover()`).
  Found by: a `notify::visible` handler on the popover and the overlay's hide logged in a dev build.

