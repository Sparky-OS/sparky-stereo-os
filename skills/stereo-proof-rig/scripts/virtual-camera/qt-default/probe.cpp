// What a Qt program gets as "the default camera", by the three routes of ORDER 582:
//   C++      QMediaDevices::defaultVideoInput()
//   QCamera  a QCamera made without a device
//   QML      MediaDevices.defaultVideoInput and a Camera without a cameraDevice
// and a QCamera given a device by the program (the program's own choice, which must stay).
// Usage: camera-default-probe [--watch SECONDS]
// Prints one line per fact: "KEY value". With --watch it prints "CHANGED ..." for each videoInputsChanged.
#include <QtCore/QCoreApplication>
#include <QtCore/QTimer>
#include <QtMultimedia/QCamera>
#include <QtMultimedia/QCameraDevice>
#include <QtMultimedia/QMediaDevices>
#include <QtQml/QQmlComponent>
#include <QtQml/QQmlEngine>
#include <cstdio>

static void list(const char *key)
{
    const auto inputs = QMediaDevices::videoInputs();
    QStringList parts;
    for (const QCameraDevice &d : inputs)
        parts << QStringLiteral("%1%2").arg(QString::fromUtf8(d.id()), d.isDefault() ? "*" : "");
    printf("%s %s\n", key, qPrintable(parts.join(' ')));
}

static void defaults(const char *key)
{
    QCamera plain;
    printf("%s api=%s qcamera=%s\n", key, QMediaDevices::defaultVideoInput().id().constData(),
           plain.cameraDevice().id().constData());
    fflush(stdout);
}

int main(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    int watch = 0;
    if (argc > 2 && QByteArray(argv[1]) == "--watch")
        watch = QByteArray(argv[2]).toInt();

    QMediaDevices devices;
    list("LIST");
    defaults("DEFAULT");

    const auto inputs = QMediaDevices::videoInputs();
    if (!inputs.isEmpty()) {
        QCamera own(inputs.last());
        printf("OWN chosen=%s kept=%s\n", inputs.last().id().constData(), own.cameraDevice().id().constData());
    }

    QQmlEngine engine;
    QQmlComponent component(&engine);
    component.setData(R"(
        import QtQml
        import QtMultimedia
        QtObject {
            property var devices: MediaDevices { id: md }
            property var camera: Camera { }
            property string defaultId: md.defaultVideoInput.id
            property string cameraId: camera.cameraDevice.id
        })", QUrl());
    QObject *qml = component.create();
    if (qml)
        printf("QML api=%s camera=%s\n", qPrintable(qml->property("defaultId").toString()),
               qPrintable(qml->property("cameraId").toString()));
    else
        printf("QML error %s\n", qPrintable(component.errorString()));
    fflush(stdout);

    if (watch > 0) {
        QObject::connect(&devices, &QMediaDevices::videoInputsChanged, &app, [&] {
            list("CHANGED_LIST");
            defaults("CHANGED_DEFAULT");
            if (qml)
                printf("CHANGED_QML api=%s\n", qPrintable(qml->property("defaultId").toString()));
            fflush(stdout);
        });
        printf("WATCHING\n");
        fflush(stdout);
        QTimer::singleShot(watch * 1000, &app, &QCoreApplication::quit);
        return app.exec();
    }
    return 0;
}
