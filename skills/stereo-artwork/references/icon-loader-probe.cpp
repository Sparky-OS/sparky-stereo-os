// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: 2026 Daniel Campos Ramos
#include <QApplication>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QImage>
#include <QPainter>
#include <QTemporaryDir>
#include <KIconLoader>
#include <KIconTheme>
#include <iostream>
#include <stdexcept>

static void require(bool ok, const char *message)
{
    if (!ok) {
        throw std::runtime_error(message);
    }
}

int main(int argc, char **argv)
{
    try {
        QTemporaryDir data;
        require(data.isValid(), "Cannot create temporary data folder");
        qputenv("XDG_DATA_HOME", data.path().toUtf8());
        QApplication app(argc, argv);
        const QString icons = data.path() + "/icons/";
        auto write = [&](const QString &name, const QByteArray &bytes) {
            require(QDir().mkpath(QFileInfo(icons + name).path()), "Cannot create fixture folder");
            QFile f(icons + name);
            require(f.open(QIODevice::WriteOnly), "Cannot open fixture");
            require(f.write(bytes) == bytes.size(), "Cannot write fixture");
        };
        auto picture = [&](const QString &name, bool pair) {
            QImage image(pair ? 64 : 32, 32, QImage::Format_ARGB32);
            image.fill(pair ? Qt::red : Qt::green);
            if (pair) {
                QPainter p(&image);
                p.fillRect(32, 0, 32, 32, Qt::blue);
            }
            require(QDir().mkpath(QFileInfo(icons + name).path()), "Cannot create image folder");
            require(image.save(icons + name), "Cannot save fixture");
        };
        write("probeplain/index.theme", "[Icon Theme]\nName=Probe plain\nDirectories=32x32/places\n\n[32x32/places]\nSize=32\nType=Fixed\nContext=Places\n");
        picture("probeplain/32x32/places/folder.png", false);
        write("probestereo/index.theme", "[Icon Theme]\nName=Probe stereo\nInherits=probeplain\nDirectories=plain/16x16/actions\nX-StereoDirectories=stereo/32x32/places\n\n[plain/16x16/actions]\nSize=16\nType=Fixed\nContext=Actions\n\n[stereo/32x32/places]\nX-StereoSize=32\nType=Fixed\nContext=Places\nX-StereoLayout=sbs-left-first\n");
        require(QDir().mkpath(icons + "probestereo/plain/16x16/actions"), "Cannot create placeholder folder");
        picture("probestereo/stereo/32x32/places/folder.png", true);
        KIconTheme::forceThemeForTests("probestereo");
        KIconLoader::global()->reconfigure({});
        auto *loader = KIconLoader::global();
        QPixmap left, right;
        require(loader->loadStereoIcon("folder", QSize(32, 32), 1, &left, &right), "Stereo API found no pair");
        require(left.size() == QSize(32, 32) && right.size() == QSize(32, 32), "Eye size changed");
        require(left.toImage().pixelColor(16, 16) == QColor(Qt::red), "Left view is wrong");
        require(right.toImage().pixelColor(16, 16) == QColor(Qt::blue), "Right view is wrong");
        std::cout << "PASS: explicit stereo request returns red left and blue right, each 32x32\n";
        const auto plain = loader->loadIcon("folder", KIconLoader::Desktop, 32);
        require(plain.toImage().pixelColor(16, 16) == QColor(Qt::green), "Ordinary request did not inherit plain icon");
        std::cout << "PASS: ordinary request returns inherited green, not the pair's red left view\n";
        require(!loader->loadStereoIcon("probe-missing-icon", QSize(32, 32), 1, &left, &right), "Missing pair accepted");
        std::cout << "PASS: missing pair refused\n";
        if (argc > 1 && QByteArray(argv[1]) == "--expect-ordinary-left") {
            require(plain.toImage().pixelColor(16, 16) == QColor(Qt::red), "Negative control: ordinary request is not the pair's left view");
        }
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
