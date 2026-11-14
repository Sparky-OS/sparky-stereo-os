// SPDX-License-Identifier: MIT
// qdiscs: a Qt Quick window of six coloured discs on neutral grey, drawn once per eye (the window's
// _q_stereo_depth, each disc's _q_stereo_parallax in device pixels, positive when nearer), to compare the pair a
// scene graph backend hands the compositor: QSG_RHI_BACKEND=vulkan against opengl.
//
//   QDISCS_DEPTH=0.5,-0.5,1.5,-1.5,0.25,1   the six parallaxes (red, green, blue, yellow, cyan, magenta)
//   QDISCS_FLAT=1                           the window never shows depth (the 2D control)
//   QDISCS_FRAMELESS=1                      no frame at all
//   QDISCS_WIDTH, QDISCS_HEIGHT             the window's size in logical pixels (940 x 620)
//   QDISCS_LIFECYCLE=1                      resized at 2.5 s, hidden at 4 s, shown at 5 s
//   QDISCS_TOGGLE=1                         depth off at 2.5 s and on again at 4 s (two views, one, two)
//   QDISCS_OFF=1                            depth off at 2.5 s, for good (two views, then one)
//   QDISCS_STRESS=1                         depth off and on every 100 ms from 0.5 s to 6.5 s (60 changes, ending
//                                           on), the window hidden at 2 s, shown at 2.5 s and resized at 4 s
// At 7 s it prints one STATE line and then stays still.
#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QSGRendererInterface>
#include <QTimer>
#include <atomic>
#include <cstdio>
#include <memory>

static const char s_scene[] = R"(
import QtQuick
Window {
    width: 940; height: 620
    color: "#808080"
    Rectangle { objectName: "d0"; x:  80; y:  90; width: 160; height: 160; radius: 80; color: "#ff0000" }
    Rectangle { objectName: "d1"; x: 390; y:  90; width: 160; height: 160; radius: 80; color: "#00ff00" }
    Rectangle { objectName: "d2"; x: 700; y:  90; width: 160; height: 160; radius: 80; color: "#0000ff" }
    Rectangle { objectName: "d3"; x:  80; y: 370; width: 160; height: 160; radius: 80; color: "#ffff00" }
    Rectangle { objectName: "d4"; x: 390; y: 370; width: 160; height: 160; radius: 80; color: "#00ffff" }
    Rectangle { objectName: "d5"; x: 700; y: 370; width: 160; height: 160; radius: 80; color: "#ff00ff" }
}
)";

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    QQmlEngine engine;
    QQmlComponent component(&engine);
    component.setData(s_scene, QUrl());
    std::unique_ptr<QQuickWindow> window(qobject_cast<QQuickWindow *>(component.create()));
    if (!window) {
        fprintf(stderr, "qdiscs: %s\n", qPrintable(component.errorString()));
        return 2;
    }
    QQuickWindow *w = window.get();
    w->setTitle(QStringLiteral("qdiscs"));
    if (qEnvironmentVariableIntValue("QDISCS_FRAMELESS") == 1)
        w->setFlag(Qt::FramelessWindowHint);
    bool ok = false;
    const int width = qEnvironmentVariableIntValue("QDISCS_WIDTH", &ok);
    if (ok && width > 0)
        w->setWidth(width);
    const int height = qEnvironmentVariableIntValue("QDISCS_HEIGHT", &ok);
    if (ok && height > 0)
        w->setHeight(height);
    const QStringList depths = qEnvironmentVariable("QDISCS_DEPTH", QStringLiteral("0.5,-0.5,1.5,-1.5,0.25,1")).split(QLatin1Char(','));
    for (int i = 0; i < 6 && i < depths.size(); ++i) {
        if (QQuickItem *disc = w->findChild<QQuickItem *>(QStringLiteral("d%1").arg(i)))
            disc->setProperty("_q_stereo_parallax", depths.at(i).toDouble());
    }
    static std::atomic<int> frames{0};
    QObject::connect(w, &QQuickWindow::frameSwapped, w, [] { ++frames; }, Qt::DirectConnection);
    const bool depth = qEnvironmentVariableIntValue("QDISCS_FLAT") != 1;
    w->show();
    if (depth)
        w->setProperty("_q_stereo_depth", true);
    if (qEnvironmentVariableIntValue("QDISCS_LIFECYCLE") == 1) {
        QTimer::singleShot(2500, w, [w] { w->resize(w->width() + 60, w->height() + 40); });
        QTimer::singleShot(4000, w, [w] { w->hide(); });
        QTimer::singleShot(5000, w, [w] { w->show(); });
    }
    if (depth && qEnvironmentVariableIntValue("QDISCS_TOGGLE") == 1) {
        QTimer::singleShot(2500, w, [w] { w->setProperty("_q_stereo_depth", false); });
        QTimer::singleShot(4000, w, [w] { w->setProperty("_q_stereo_depth", true); });
    }
    if (depth && qEnvironmentVariableIntValue("QDISCS_OFF") == 1)
        QTimer::singleShot(2500, w, [w] { w->setProperty("_q_stereo_depth", false); });
    if (depth && qEnvironmentVariableIntValue("QDISCS_STRESS") == 1) {
        auto *changes = new int(0);
        auto *timer = new QTimer(w);
        QObject::connect(timer, &QTimer::timeout, w, [w, changes, timer] {
            ++*changes;
            w->setProperty("_q_stereo_depth", *changes % 2 == 0);
            if (*changes == 60)
                timer->stop();
        });
        QTimer::singleShot(500, w, [timer] { timer->start(100); });
        QTimer::singleShot(2000, w, [w] { w->hide(); });
        QTimer::singleShot(2500, w, [w] { w->show(); });
        QTimer::singleShot(4000, w, [w] { w->resize(w->width() + 60, w->height() + 40); });
    }
    QTimer::singleShot(7000, w, [w] {
        printf("STATE api %d stereo-format %d views-asked %d pair %d size %dx%d dpr %.3f frames %d exposed %d\n",
               int(w->rendererInterface()->graphicsApi()), w->format().stereo(), w->property("_q_stereo_views").toInt(),
               w->property("_q_stereo_pair").toBool(), w->width(), w->height(), w->devicePixelRatio(), frames.load(),
               w->isExposed());
        fflush(stdout);
    });
    return app.exec();
}
