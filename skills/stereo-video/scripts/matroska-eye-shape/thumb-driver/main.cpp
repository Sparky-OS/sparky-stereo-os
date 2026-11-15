// SPDX-License-Identifier: MIT
// Runs one KIO thumbnailer plug-in on one file, as Dolphin's thumbnail worker does, and saves the picture it makes.
// Usage: thumb-driver PLUGIN.so FILE OUT.png [SIZE]
#include <KIO/ThumbnailCreator>
#include <KPluginFactory>
#include <KPluginMetaData>
#include <QGuiApplication>
#include <QImage>
#include <QMimeDatabase>
#include <QUrl>
#include <cstdio>

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    if (argc < 4) {
        std::fprintf(stderr, "usage: thumb-driver PLUGIN.so FILE OUT.png [SIZE]\n");
        return 2;
    }
    const int size = argc > 4 ? QString::fromLocal8Bit(argv[4]).toInt() : 512;
    const KPluginMetaData md(QString::fromLocal8Bit(argv[1]));
    const auto result = KPluginFactory::instantiatePlugin<KIO::ThumbnailCreator>(md);
    if (!result) {
        std::fprintf(stderr, "cannot load %s: %s\n", argv[1], qPrintable(result.errorString));
        return 2;
    }
    const QString mime = QMimeDatabase().mimeTypeForFile(QString::fromLocal8Bit(argv[2])).name();
    const KIO::ThumbnailRequest request(QUrl::fromLocalFile(QString::fromLocal8Bit(argv[2])), QSize(size, size), mime, 1.0, 0);
    const KIO::ThumbnailResult thumbnail = result.plugin->create(request);
    if (!thumbnail.isValid()) {
        std::fprintf(stderr, "no thumbnail for %s (%s)\n", argv[2], qPrintable(mime));
        return 3;
    }
    const QImage image = thumbnail.image();
    if (!image.save(QString::fromLocal8Bit(argv[3]))) {
        std::fprintf(stderr, "cannot write %s\n", argv[3]);
        return 4;
    }
    std::printf("%s %dx%d mime=%s\n", argv[3], image.width(), image.height(), qPrintable(mime));
    return 0;
}
