// What a Qt program that chooses no format gets from a camera: a QCamera on the device named by its id (/dev/videoN) is started
// with no QCameraFormat, so Qt Multimedia picks one itself (QPlatformCamera::findBestCameraFormat) and sets it on the device.
// The rig's virtual camera logs that S_FMT with this program's name. Exits when the camera is active, fails, or after 15 s.
// Usage: QT_QPA_PLATFORM=offscreen qt-probe /dev/videoN
#include <QCamera>
#include <QCameraDevice>
#include <QGuiApplication>
#include <QMediaCaptureSession>
#include <QMediaDevices>
#include <QTimer>
#include <QVideoSink>
#include <cstdio>

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    if (argc < 2) {
        return 2;
    }
    const QByteArray want(argv[1]);
    QCameraDevice device;
    for (const QCameraDevice &d : QMediaDevices::videoInputs()) {
        std::printf("listed %s%s\n", d.id().constData(), d.isDefault() ? " (default)" : "");
        if (d.id() == want) {
            device = d;
        }
    }
    if (device.isNull()) {
        std::printf("NOCAMERA %s\n", want.constData());
        return 3;
    }
    std::printf("formats %lld\n", qlonglong(device.videoFormats().size()));
    QCamera camera(device);
    QMediaCaptureSession session;
    QVideoSink sink;
    session.setCamera(&camera);
    session.setVideoSink(&sink);
    QObject::connect(&camera, &QCamera::errorOccurred, &app, [&app](QCamera::Error, const QString &text) {
        std::printf("error %s\n", qPrintable(text));
        app.quit();
    });
    QObject::connect(&camera, &QCamera::activeChanged, &app, [&app](bool active) {
        std::printf("active %d\n", active);
        if (active) {
            QTimer::singleShot(500, &app, &QCoreApplication::quit);
        }
    });
    QTimer::singleShot(15000, &app, &QCoreApplication::quit);
    camera.start();
    app.exec();
    std::printf("asked format %s\n", camera.cameraFormat().isNull() ? "none" : "set");
    return 0;
}
