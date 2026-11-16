// What a Qt program gets as "the default camera" on the PipeWire camera backend (ORDER 625),
// and whether a camera the program holds stays the same through hotplugs and list refreshes.
// Usage: probe625 [--own ID] [--start] [--watch SECONDS]
//   LIST     the listed camera ids, * marks isDefault
//   DEFAULT  api=QMediaDevices::defaultVideoInput() qcamera=the device a QCamera made without one gets
//   CAMERA   kind=plain (QCamera()) or own (QCamera(device), the program's own choice), chosen and kept
//   --start  starts that camera into a QVideoSink and prints FRAMES every two seconds
//   --watch  prints CHANGED_* for each videoInputsChanged until SECONDS have passed
#include <QtCore/QTimer>
#include <QtGui/QGuiApplication>
#include <QtMultimedia/QCamera>
#include <QtMultimedia/QCameraDevice>
#include <QtMultimedia/QMediaCaptureSession>
#include <QtMultimedia/QMediaDevices>
#include <QtMultimedia/QVideoSink>
#include <cstdio>
#include <memory>
#include <unistd.h>

static void list(const char *key)
{
    QStringList parts;
    for (const QCameraDevice &d : QMediaDevices::videoInputs())
        parts << QStringLiteral("%1%2").arg(QString::fromUtf8(d.id()), d.isDefault() ? "*" : "");
    printf("%s %s\n", key, qPrintable(parts.join(' ')));
}

static void defaults(const char *key)
{
    QCamera plain;
    printf("%s api=%s qcamera=%s\n", key, QMediaDevices::defaultVideoInput().id().constData(),
           plain.cameraDevice().id().constData());
}

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    QByteArray ownId;
    bool start = false;
    int watch = 0;
    for (int i = 1; i < argc; ++i) {
        const QByteArray a = argv[i];
        if (a == "--own" && i + 1 < argc)
            ownId = argv[++i];
        else if (a == "--start")
            start = true;
        else if (a == "--watch" && i + 1 < argc)
            watch = QByteArray(argv[++i]).toInt();
    }
    printf("PID %d\n", int(getpid()));

    QMediaDevices devices;
    list("LIST");
    defaults("DEFAULT");

    std::unique_ptr<QCamera> camera;
    if (ownId.isEmpty()) {
        camera = std::make_unique<QCamera>();
        printf("CAMERA kind=plain kept=%s\n", camera->cameraDevice().id().constData());
    } else {
        QCameraDevice chosen;
        for (const QCameraDevice &d : QMediaDevices::videoInputs())
            if (d.id() == ownId)
                chosen = d;
        camera = std::make_unique<QCamera>(chosen);
        printf("CAMERA kind=own chosen=%s found=%d kept=%s\n", ownId.constData(), !chosen.isNull(),
               camera->cameraDevice().id().constData());
    }
    fflush(stdout);

    QObject::connect(camera.get(), &QCamera::errorOccurred, &app,
                     [](QCamera::Error, const QString &s) {
        printf("CAMERA_ERROR %s\n", qPrintable(s));
        fflush(stdout);
    });

    QMediaCaptureSession session;
    QVideoSink sink;
    int frames = 0;
    if (start) {
        session.setCamera(camera.get());
        session.setVideoSink(&sink);
        QObject::connect(&sink, &QVideoSink::videoFrameChanged, &app, [&] { ++frames; });
        camera->start();
        auto *tick = new QTimer(&app);
        QObject::connect(tick, &QTimer::timeout, &app, [&] {
            printf("FRAMES %d active=%d kept=%s\n", frames, camera->isActive(),
                   camera->cameraDevice().id().constData());
            fflush(stdout);
        });
        tick->start(2000);
    }

    if (watch > 0 || start) {
        QObject::connect(&devices, &QMediaDevices::videoInputsChanged, &app, [&] {
            list("CHANGED_LIST");
            defaults("CHANGED_DEFAULT");
            printf("CHANGED_CAMERA kept=%s\n", camera->cameraDevice().id().constData());
            fflush(stdout);
        });
        printf("WATCHING\n");
        fflush(stdout);
        QTimer::singleShot((watch > 0 ? watch : 6) * 1000, &app, &QCoreApplication::quit);
        app.exec();
        printf("END frames=%d kept=%s\n", frames, camera->cameraDevice().id().constData());
    }
    return 0;
}
