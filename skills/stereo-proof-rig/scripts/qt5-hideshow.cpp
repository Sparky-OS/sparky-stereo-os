// SPDX-License-Identifier: MIT
// qt5-hideshow.cpp, the proof rig (ORDER 578): build in the rig image with qtbase5-dev and g++,
//   g++ -O2 -fPIC -shared -o hideshow.so qt5-hideshow.cpp $(pkg-config --cflags --libs Qt5Gui Qt5Core)
// and preload it into a Qt 5 program (LD_PRELOAD=hideshow.so). See native-linux/references/wayland-protocol-errors.md.
// HIDESHOW_AFTER milliseconds after Qt starts, and then every HIDESHOW_EVERY milliseconds (0: once), it hides the
// video's native QWindow (a child QWindow with an OpenGL surface) from Qt's own thread and shows it again
// HIDESHOW_GAP milliseconds later: what Qt 5 does to that window when its container or the page that holds it is
// hidden. Qt 5's Wayland platform destroys a hidden window's wl_surface.
#include <QCoreApplication>
#include <QGuiApplication>
#include <QPointer>
#include <QTimer>
#include <QWindow>
#include <cstdio>
#include <cstdlib>

static int env(const char *name, int fallback)
{
    const char *v = getenv(name);
    return v ? atoi(v) : fallback;
}

static void cycle()
{
    QWindow *target = nullptr;
    const auto windows = QGuiApplication::allWindows();
    for (QWindow *w : windows)
        if (w->parent() && w->surfaceType() == QSurface::OpenGLSurface && w->isVisible())
            target = w;
    if (target) {
        fprintf(stderr, "hideshow: hiding the video window %p\n", (void *)target);
        target->hide();
        QPointer<QWindow> keep(target);
        QTimer::singleShot(env("HIDESHOW_GAP", 150), qApp, [keep] {
            if (keep) {
                fprintf(stderr, "hideshow: showing the video window again\n");
                keep->show();
            }
        });
    } else {
        fprintf(stderr, "hideshow: no visible video window\n");
    }
    if (int every = env("HIDESHOW_EVERY", 0))
        QTimer::singleShot(every, qApp, cycle);
}

static void start()
{
    if (!qobject_cast<QGuiApplication *>(QCoreApplication::instance()))
        return;
    QTimer::singleShot(env("HIDESHOW_AFTER", 8000), qApp, cycle);
}
Q_COREAPP_STARTUP_FUNCTION(start)
