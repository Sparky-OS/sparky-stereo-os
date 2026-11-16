// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: 2026 Daniel Campos Ramos
#include <QCoreApplication>
#include <QDBusConnection>
#include <QDBusInterface>
#include <QDBusReply>
#include <QDBusUnixFileDescriptor>
#include <QImage>
#include <QJsonDocument>
#include <QJsonObject>
#include <iostream>
#include <thread>
#include <unistd.h>

int main(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    if (argc != 2) return 2;
    int fds[2];
    if (pipe(fds)) return 2;
    QByteArray bytes;
    std::thread reader([&] {
        char chunk[65536];
        ssize_t n;
        while ((n = read(fds[0], chunk, sizeof chunk)) > 0) bytes.append(chunk, n);
        close(fds[0]);
    });
    QDBusReply<QVariantMap> result;
    {
        QDBusUnixFileDescriptor descriptor(fds[1]);
        close(fds[1]);
        QDBusInterface screenshot("org.kde.KWin", "/org/kde/KWin/ScreenShot2", "org.kde.KWin.ScreenShot2", QDBusConnection::sessionBus());
        screenshot.setTimeout(30000);
        const QVariantMap options{{"native-resolution", true}, {"include-cursor", false}};
        result = screenshot.call("CaptureActiveScreen", options, QVariant::fromValue(descriptor));
    }
    reader.join();
    if (!result.isValid()) { std::cerr << result.error().message().toStdString() << '\n'; return 1; }
    const auto info = result.value();
    const int width = info.value("width").toInt();
    const int height = info.value("height").toInt();
    const int stride = info.value("stride").toInt();
    if (width <= 0 || height <= 0 || stride < width || qint64(stride) * height != bytes.size()) return 1;
    QImage image(reinterpret_cast<const uchar *>(bytes.constData()), width, height, stride, QImage::Format(info.value("format").toInt()));
    if (image.isNull() || !image.save(QString::fromLocal8Bit(argv[1]), "PNG")) return 1;
    std::cout << QJsonDocument(QJsonObject::fromVariantMap(info)).toJson(QJsonDocument::Compact).toStdString() << '\n';
}
