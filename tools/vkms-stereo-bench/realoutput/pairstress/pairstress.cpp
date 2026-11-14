// SPDX-License-Identifier: MIT
// pairstress: Qt Quick windows drawn once per eye (the window's _q_stereo_depth, each item's _q_stereo_parallax),
// taken through the events that end in an expose, with a watchdog on the gui thread.
//
//   pairstress CASE     still | hideshow | minimize | resize | two | closeexpose | cycles
//
// Each window is white with a reference square at the screen (parallax 0) and a square 8 px nearer; a script reads
// the two squares in each half of the output's frame: a pair shows them 8 px apart between the eyes, one picture 0.
// The program prints READY when its case has run and then stays still. The watchdog prints WATCHDOG and the gui
// thread's backtrace when the gui thread has not run for 5 s.
#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTimer>
#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdio>
#include <execinfo.h>
#include <memory>
#include <pthread.h>
#include <thread>
#include <unistd.h>
#include <vector>

static std::atomic<qint64> s_beat{0};
static std::atomic<int> s_frames{0};
static pthread_t s_gui;

static qint64 now()
{
    return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
}

static void backtraceHandler(int)
{
    void *frames[64];
    const int n = backtrace(frames, 64);
    backtrace_symbols_fd(frames, n, 2);
}

static const char s_scene[] = R"(
import QtQuick
Window {
    property color reference: "#0000ff"
    property color near: "#ff0000"
    width: 400; height: 240
    color: "white"
    Rectangle { objectName: "reference"; x: 40; y: 60; width: 60; height: 60; color: parent ? parent.reference : "black" }
    Rectangle { objectName: "near"; x: 200; y: 60; width: 60; height: 60; color: parent ? parent.near : "black" }
}
)";

static std::unique_ptr<QQuickWindow> makeWindow(QQmlEngine &engine, const char *reference, const char *near, int x)
{
    QQmlComponent component(&engine);
    component.setData(s_scene, QUrl());
    std::unique_ptr<QQuickWindow> window(qobject_cast<QQuickWindow *>(component.create()));
    if (!window) {
        fprintf(stderr, "pairstress: %s\n", qPrintable(component.errorString()));
        exit(2);
    }
    window->setProperty("reference", QColor(reference));
    window->setProperty("near", QColor(near));
    window->findChild<QQuickItem *>("reference")->setProperty("color", QColor(reference));
    window->findChild<QQuickItem *>("near")->setProperty("color", QColor(near));
    window->findChild<QQuickItem *>("reference")->setProperty("_q_stereo_parallax", 0.0);
    window->findChild<QQuickItem *>("near")->setProperty("_q_stereo_parallax", 8.0);
    window->setPosition(x, 100);
    QObject::connect(window.get(), &QQuickWindow::frameSwapped, window.get(), [] { ++s_frames; }, Qt::DirectConnection);
    window->show();
    window->setProperty("_q_stereo_depth", true);
    return window;
}

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    const QString mode = argc > 1 ? QString::fromLatin1(argv[1]) : QStringLiteral("still");
    s_gui = pthread_self();
    signal(SIGUSR2, backtraceHandler);
    s_beat = now();
    QTimer beat;
    QObject::connect(&beat, &QTimer::timeout, [] { s_beat = now(); });
    beat.start(100);
    std::thread([] {
        bool told = false;
        for (;;) {
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            const qint64 held = now() - s_beat;
            if (held > 5000 && !told) {
                told = true;
                fprintf(stderr, "WATCHDOG the gui thread has not run for %lld ms; its backtrace:\n", static_cast<long long>(held));
                pthread_kill(s_gui, SIGUSR2);
            } else if (held < 1000) {
                told = false;
            }
        }
    }).detach();

    QQmlEngine engine;
    std::vector<std::unique_ptr<QQuickWindow>> windows;
    windows.push_back(makeWindow(engine, "#0000ff", "#ff0000", 100));
    if (mode == QLatin1String("two"))
        windows.push_back(makeWindow(engine, "#00ff00", "#ff00ff", 700));
    QQuickWindow *w = windows.front().get();
    const auto ready = [w](const char *what) {
        printf("READY %s frames %d pair %d exposed %d\n", what, s_frames.load(), w->property("_q_stereo_pair").toBool(), w->isExposed());
        fflush(stdout);
    };
    // every case starts once the window is drawn as a pair and has been still for a while
    const int start = 6000;
    if (mode == QLatin1String("hideshow")) {
        QTimer::singleShot(start, [w] { w->hide(); });
        QTimer::singleShot(start + 1500, [w] { w->show(); });
        QTimer::singleShot(start + 6000, [=] { ready("hideshow"); });
    } else if (mode == QLatin1String("minimize")) {
        QTimer::singleShot(start, [=] { w->showMinimized(); ready("minimized"); });
    } else if (mode == QLatin1String("resize")) {
        QTimer::singleShot(start, [w] { w->resize(520, 300); });
        QTimer::singleShot(start + 5000, [=] { ready("resize"); });
    } else if (mode == QLatin1String("closeexpose")) {
        // twenty windows, each closed while its first expose is being handled or right after
        auto *count = new int(0);
        auto *timer = new QTimer(&app);
        auto *extra = new std::vector<std::unique_ptr<QQuickWindow>>;
        QObject::connect(timer, &QTimer::timeout, [=, &engine] {
            if (*count == 20) {
                timer->stop();
                ready("closeexpose");
                return;
            }
            auto window = makeWindow(engine, "#00ff00", "#ff00ff", 600);
            QQuickWindow *raw = window.get();
            if (*count % 2)
                QObject::connect(raw, &QWindow::visibleChanged, raw, [raw] { raw->close(); }, Qt::QueuedConnection);
            else
                QTimer::singleShot(30 + 10 * *count, raw, [raw] { raw->close(); });
            extra->push_back(std::move(window));
            if (extra->size() > 3)
                extra->erase(extra->begin());
            ++*count;
        });
        QTimer::singleShot(start, [timer] { timer->start(400); });
    } else if (mode == QLatin1String("cycles")) {
        auto *count = new int(0);
        auto *timer = new QTimer(&app);
        QObject::connect(timer, &QTimer::timeout, [=] {
            if (*count == 400) {
                timer->stop();
                QTimer::singleShot(6000, [=] { ready("cycles"); });
                return;
            }
            (*count % 2) ? w->show() : w->hide();
            ++*count;
        });
        QTimer::singleShot(start, [timer] { timer->start(60); });
    } else {
        QTimer::singleShot(start, [=] { ready("still"); });
    }
    return app.exec();
}
