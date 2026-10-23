# Depth inside every window

**For everyone who uses the desktop, and for theme and toolkit developers:** how the elements inside a window (its buttons, fields, tabs, rows and the menus it draws itself) get a small depth of their own, how that depth reaches every Qt Quick and Qt Widgets window styled by Union, the values it ships with and what each one is for, and which ways of drawing a window still show it flat.

**Status:** built in the edition's packages qt6-base 6.11.2+dfsg-5+stereo3d8, qt6-declarative 6.11.2+dfsg-3+stereo3d1, kwin 4:6.7.4-2+stereo3d32, plasma-wayland-protocols 1.21.0-1+stereo3d8, stereo-declare 1.5.0-1 and plasma-union 6.8.80~git20261022.2163195c-0+stereo3d1.
Measured on those packages, installed together, on the headless proof rig on 23 October 2026.
Not yet seen on a 3D TV.

## What you see

The desktop already has three places: the active window at the screen, its menus and tooltips popped, the windows behind it and the wallpaper sunk ([Depth on the desktop](depth-on-the-desktop.md)).
Inside the active window, each element now sits at a depth of its own, a pixel or less from the window.
An element the theme draws with an outer shadow, like a raised button, stands a little in front of the window.
An element the theme draws with an inset shadow, like a sunken field, lies a little behind it.
A pressed, checked, flat or disabled button, which the theme draws without its shadow, lies on the window.
In a tab bar the current tab lies on the window and the other tabs step back from it, the way Stereo KWin steps windows back behind the active one.
A menu or a popup that a window draws inside itself pops to the popped limit, as a menu that is a surface of its own does.
Each element moves as a whole: its background, border, text and icon.
An element deeper than what it lies on is seen through its own rectangle, as through a window frame, so it never shows past its edges.
A window in the pile behind the active one is a flat sheet, as before.
A 2D screen shows every window exactly as it was.

## The values, and what each one is for

The depth of an element is a share of a limit, and the limits are the user's: System Settings, "3D Depth", stored in `kwinrc`, group `[StereoDepth]`.
They are in pixels of a view 1920 pixels wide, the unit Stereo KWin uses on every screen.

| Setting | Default | What it moves | Why this size |
|---|---|---|---|
| `SunkLimit` | 10 px | Desktop elements behind the screen: the windows in the pile step back, the wallpaper deepest. | Behind the screen is like looking through a window, so depth there stays contained and this limit can be the larger one (Daniel, 5 October 2026). |
| `PoppedLimit` | 4 px | Desktop elements in front of the screen: menus, popups, tooltips and dialogs, also the ones a window draws inside itself. | In front of the screen, the screen's edge cuts through what comes out too far, so the popped side is the smaller one (Daniel, 5 October 2026). |
| `ElementLimit` | 1 px | A window's own elements (buttons, fields, tabs, rows, check boxes), either way, from the surface they lie on. | The two limits above are for desktop elements; a window's own elements move by half a pixel to a pixel either way (Daniel, 23 October 2026), so an inset text field sinks 1 px at most and is never buried at the wallpaper's depth. |

**The theme gives the sign and the strength, with what it already draws.**
An outer shadow shows a box "as if it were lifted above the canvas", and an inset one "as if the box were cut out of the canvas and shifted behind it" ([CSS Backgrounds and Borders 3, §6.1](https://www.w3.org/TR/css-backgrounds-3/#box-shadow)).
Union reads exactly that: an outer shadow raises an element and an inset shadow sinks it.
The strongest shadow in the window is a whole step of `ElementLimit`, and weaker shadows take a share of it by their blur, offset and opacity: more shadow, outer or inset, means more separation (Daniel, 23 October 2026).
An element with no shadow lies on what it is drawn on.
A depth the theme declares always wins (`depth: sunk | screen | popped | <percentage> | <number>`), so a theme without shadows, or a high contrast theme, still says where its elements stand.
Union's Breeze declares only what its drawing does not say: a flat tool button rises under the pointer, as Qt raises it, and the menus, popups, tooltips and dialogs drawn inside a window are popped.

**Levels fit inside the limit, the way Stereo KWin fits menus.**
An element stands on what it lies on, so a raised button on a raised card stands one step out from the card.
When nested levels would pass the limit, the whole stack is fitted into it, as Stereo KWin fits a sub-menu over its menu and steps the windows in the pile back inside the sunk range.
It is one design at every scale.

**Why the tests also run at 12 px.**
At the shipped `ElementLimit` of 1 px, many shares are fractions of a pixel.
In the measuring style's ladder, Qt Quick moves three elements by 0.111, 0.333 and 0.667 px: the first two change no pixel of the picture, and the third changes one.
A test cannot measure what changes no pixel.
So the same code also runs with `ElementLimit` at 12 px, where every share and every cut moves whole pixels and can be measured.
12 px is a measuring scale, never a default.

## How the depth reaches every window

Five parts take part, each in the layer that owns its piece of the work.

1. **Stereo KWin tells a surface when its elements may show depth.**
   Version 3 of `kde_stereo_content_v1` (our [plasma-wayland-protocols](https://invent.kde.org/danielcamposramos/plasma-wayland-protocols/-/tree/stereo3d-6.7)) adds `kde_stereo_depth_v1`.
   Its `depth_state` event says whether the surface is awake (on a stereo output, and the active window on top of what it overlaps, a popup, a panel or the desktop, not a window in the pile).
   It also says which of the surface's edges lie on the output's edge, where nothing comes nearer than the screen.
2. **Union, the style, says where each element stands.**
   It reads the user's limits and works out each element's depth from the theme, as above.
   It sets two values the toolkit reads: the window's `_q_stereo_depth`, and each element's `_q_stereo_parallax`, its shift between the eyes in device pixels.
   It hears from Stereo KWin through [libstereo-declare](https://github.com/Sparky-OS/libstereo-declare) 1.5.
3. **Qt Quick draws the window once per eye.**
   While a window's `_q_stereo_depth` is set, Qt Quick asks the platform for a surface with two views.
   Then, in both of its render loops, it polishes, synchronises and renders the left eye, and ends that frame without presenting it ([`QRhi::SkipPresent`](https://doc.qt.io/qt-6/qrhi.html#EndFrameFlag-enum)).
   It polishes, synchronises and renders the right eye into the swapchain's right buffer ([`QRhiSwapChain::StereoTargetBuffer`](https://doc.qt.io/qt-6/qrhiswapchain.html#StereoTargetBuffer-enum)), and presents.
   Each element moves by its own share of the parallax in each eye, the left eye to the right for nearer, as Stereo KWin splits a parallax.
   Only the scene graph's matrices and clip nodes change, so layout, input and accessibility stay where they are in 2D.
4. **Qt marks the pair as the desktop's own.**
   Qt Wayland makes the EGL surface again with two views (`EGL_EXT_multiview_window`, in the edition's Mesa) between two frames, never in the middle of a pair.
   Its first commit carries `set_desktop_depth`, so Stereo KWin draws the window per eye but does not count it as stereo content: for the automatic 3D mode switch, for stereo screenshots and for the depth estimator it is still the desktop.
   A window drawn by Qt Widgets is painted once per eye by Qt's repaint manager into a buffer two views wide, with the same mark.
5. **Mesa packs the two views full side by side and declares them,** as it does for any program that draws two views, and Stereo KWin shows each view to its eye.

Without any of these parts nothing changes.
A window of another style, on another compositor, on a 2D screen, asleep in the pile, or with depth switched off, is drawn once, exactly as before.

## What is still flat, and how it gets depth

These ways of drawing a window show it flat, exactly as before, with no error.
Each is a piece of work, written here with its owning place and its test.

- **Qt Quick on the Vulkan renderer** (`QSG_RHI_BACKEND=vulkan`).
  Qt's Vulkan renderer already makes a swapchain with two layers when its window's format asks for stereo and the surface allows it ([`maxImageArrayLayers`](https://registry.khronos.org/vulkan/specs/latest/man/html/VkSurfaceCapabilitiesKHR.html)).
  The edition's Mesa allows two layers when Stereo KWin announces stereo, so what is missing is Qt's side.
  In qtbase, `QWaylandVulkanWindow` follows the window's `_q_stereo_views` with a stereo format, and `QRhiVulkan::beginFrame` rebuilds the swapchain when that format changes, as the OpenGL swapchain already does.
  Qt then marks the surface with `QWaylandStereoDepth::setDesktopDepth`, which takes effect with Mesa's next commit.
  Measured on the rig at `ElementLimit` 12 on a 3D output: both eyes show the same picture, identical to the same window on a 2D output.
- **Qt Quick's software renderer** (`QT_QUICK_BACKEND=software`).
  It paints into a backing store and has no swapchain, so it has no right buffer.
  In qtdeclarative, `qsgsoftwarerenderloop.cpp` and `qsgsoftwarethreadedrenderloop.cpp` paint the scene twice into a backing store two views wide while the window's `_q_stereo_depth` is set, with the same per eye matrices, and set the window's `_q_stereo_pair`.
  Qt Wayland's shared memory backing store already declares such a pair for Qt Widgets.
  Measured on the rig at `ElementLimit` 12 on a 3D output: both eyes show the same picture, identical to the same window on a 2D output.
- **`QQuickWidget` and `QQuickRenderControl`.**
  A Qt Quick scene drawn this way has no window of its own on screen: "the QQuickWindow must not be shown ... and there will not be an underlying native window for it" ([`QQuickRenderControl`](https://doc.qt.io/qt-6/qquickrendercontrol.html)), so the platform cannot give it two views.
  `QQuickWidget` renders its scene twice, into two textures, while its top level is painted as a pair, and Qt Widgets composes each texture into its own eye; today a window that holds such a texture is painted once.
  `QQuickRenderControl` belongs to the program that uses it, which renders each eye with the window's `_q_stereo_eye` set, or into a multiview render target.
- **Windows with client side decorations.**
  A window whose frame the client draws is painted once, because the frame would land in one half of the pair.
  On Stereo KWin, Qt's windows have server side decorations, so this is a window on a compositor without them, or a program that asks for its own frame.
  The frame is drawn into both halves at the screen's depth and the contents per eye, in `qwaylandshmbackingstore.cpp` and `qwaylandeglwindow.cpp`.
- **X11.**
  Only the Wayland EGL window reads `_q_stereo_views`, and the exchange with Stereo KWin is a Wayland protocol.
  X11 needs both halves of the exchange as window properties beside `_KDE_NET_WM_STEREO_CONTENT`: Stereo KWin writes whether the window is awake, and the program marks its pair as the desktop's depth.
  Stereo KWin's X11 window code reads them and libstereo-declare binds them; then Qt's xcb plugin gives the window a stereo GLX surface, as it already does for a stereo `QOpenGLWidget`.
  Measured on the rig at `ElementLimit` 12 on a 3D output: both eyes show the same picture, identical to the same window on a 2D output.

## What stays exactly as it was

- A 2D screen, a window in the pile, a session with the limits at zero, another compositor, or a style other than Union: the same pixels as before.
- Layout, sizes, input and accessibility positions, in every case, because depth is drawn, never laid out.
- Stereo content inside a window, which keeps its own declaration and its own eyes.

## How it was proven

Everything below ran on the six packages installed together in a fresh container, as an upgrade from the edition as published (89 packages upgraded, none removed), with Stereo KWin's headless virtual output switched into a 3D mode (side by side half), on the AMD card.
Each element's disparity is compared with a prediction worked out by hand from the theme's CSS, not from Union's code, and measured to a hundredth of a pixel against the same window on a 2D output.

| Window | Limits (`SunkLimit`/`PoppedLimit`/`ElementLimit`) | Elements at the predicted disparity |
|---|---|---|
| Union's Breeze, Qt Quick, threaded render loop | 10/4/1, the shipped values | 18 of 18 |
| The same, basic render loop | 10/4/1 | 18 of 18 |
| The same | 4/10/1, the two desktop limits swapped | 18 of 18: the in-window popup at +10, its button at +11 |
| The same | 10/4/12, the measuring scale | 18 of 18 |
| The measuring style's ladders, Qt Quick | 10/4/1 | 14 of 14; the 0.111 and 0.333 px shares change no pixel |
| The same | 10/4/12 | 14 of 14, strictly ordered: shadows 1.3, 4 and 8, levels 4, 8 and 12, insets -2, -6 and -12, tabs -12, -6, 0, -6 and -12 |
| Union's Breeze, Qt Widgets | 10/4/1 and 10/4/12 | 15 of 15, both |
| Debian's Qt Quick instead of the edition's (negative control) | 10/4/1, ladders 10/4/12 | 11 of 18; ladders 1 of 14 |
| Every depth package taken back to the published edition, Union without its depth, only Stereo KWin new (negative control) | 10/4/1, ladders 10/4/12 | 10 of 18; ladders 1 of 14; Widgets 7 of 15 |

- **The cut:** at 12 px, beside each of the three sunk fields 0 pixels differ from the 2D window in either eye, while 231 to 751 pixels inside each of them moved.
- **2D:** the same windows on a 2D output, Qt Quick and Qt Widgets: 0 differing pixels in the whole 1920x1080 capture against the edition as published, with Union built without its depth.
- **Depth off:** with the limits at zero on the 3D output, both eyes: 0 differing pixels against the 2D window.
- **On the wire:** Union's `get_depth` and `depth_state(1, 0)`; Qt's `get_depth` and `set_desktop_depth(1)`; Mesa's 1800x520 buffer, two views of a 900x520 window, with `create` and `set_content(3)` on the same commit; one `wp_viewport` on the surface, Qt's own.
- **Idle:** an idle window drawn as a pair rendered 7 frames over the case with the threaded loop and 4 with the basic loop, each half counted: no frames of its own.
- **Nothing else moved:** the one-resize cases of every stereo surface give the same PSNR as the previous KWin, to the hundredth (64.24, 63.31, 56.47, 56.02 and 69.13 dB, the control without a destination 8.11 dB), and so do the X11 views at another size (63.42 and 64.24 dB).

## Credits

Union is KDE's style engine, by Arjen Hiemstra, Akseli Lahtinen, Joshua Goins, Martin Sh, Niccolò Venerandi and Noah Davis.
Its Debian packaging, which the edition's package keeps, is by Patrick Franz and Rik Mills.
Reading an element's depth from its shadow was proposed by Samuele on [KDE Discuss](https://discuss.kde.org/t/real-depth-for-oceans-elevation-a-design-question-for-union/50744), and Daniel took it there.
The values, their roles, and the rule that a window's insides move by a pixel or less are Daniel's.
