// Decode time of the picture Plasma's Image wallpaper picks from a wallpaper package's contents/images for a screen size.
// The selection is a copy of WallpaperPackage::findPreferredImageInPackage (plasma-workspace 6.7.4,
// wallpapers/image/plugin/finder/packagefinder.cpp: distance(), resSize()); the decode is QImageReader as QML's Image uses it:
// read() of the whole picture, and read() with setScaledSize(target) (the PNG handler cannot scale, so QImageReader scales after the read).
// Usage: decode-bench PACKAGE_DIR WIDTHxHEIGHT ROUNDS   prints: picked file, bytes, median ms read, median ms read+scale
#include <QDir>
#include <QElapsedTimer>
#include <QFileInfo>
#include <QGuiApplication>
#include <QImageReader>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <limits>
#include <vector>

static double distance(const QSize &size, const QSize &desired)
{
    const double desiredAspectRatio = (desired.height() > 0) ? desired.width() / static_cast<double>(desired.height()) : 0;
    const double candidateAspectRatio = (size.height() > 0) ? size.width() / static_cast<double>(size.height()) : std::numeric_limits<double>::max();
    double delta = size.width() - desired.width();
    delta = delta >= 0.0 ? delta : -delta * 2;
    return std::abs(candidateAspectRatio - desiredAspectRatio) * 25000 + delta;
}

static QSize resSize(QStringView str)
{
    const int index = str.indexOf(QLatin1Char('x'));
    if (index != -1) {
        return {str.left(index).toInt(), str.mid(index + 1).toInt()};
    }
    return {};
}

static double median(std::vector<double> v)
{
    std::sort(v.begin(), v.end());
    return v[v.size() / 2];
}

int main(int argc, char **argv)
{
    qputenv("QT_QPA_PLATFORM", "offscreen");
    QGuiApplication app(argc, argv);
    if (argc < 4) {
        return 2;
    }
    const QString dir = QString::fromLocal8Bit(argv[1]) + QStringLiteral("/contents/images");
    const QStringList parts = QString::fromLocal8Bit(argv[2]).split(QLatin1Char('x'));
    const QSize target(parts.value(0).toInt(), parts.value(1).toInt());
    const int rounds = atoi(argv[3]);
    QString preferred;
    double best = std::numeric_limits<double>::max();
    for (const QString &entry : QDir(dir).entryList(QDir::Files)) {
        const QSize candidate = resSize(QFileInfo(entry).baseName());
        if (candidate.isEmpty()) {
            continue;
        }
        const double dist = distance(candidate, target);
        if (preferred.isEmpty() || dist < best) {
            preferred = entry;
            best = dist;
        }
    }
    const QString path = dir + QLatin1Char('/') + preferred;
    std::vector<double> plain, scaled;
    for (int i = -1; i < rounds; ++i) {
        QElapsedTimer t;
        t.start();
        QImageReader r(path);
        const QImage img = r.read();
        const double a = t.nsecsElapsed() / 1e6;
        if (img.isNull()) {
            fprintf(stderr, "%s: %s\n", qPrintable(path), qPrintable(r.errorString()));
            return 1;
        }
        t.restart();
        QImageReader r2(path);
        r2.setScaledSize(target);
        const QImage img2 = r2.read();
        const double b = t.nsecsElapsed() / 1e6;
        if (i >= 0) {
            plain.push_back(a);
            scaled.push_back(b);
        }
    }
    printf("%s %lld %.1f %.1f\n", qPrintable(preferred), static_cast<long long>(QFileInfo(path).size()), median(plain), median(scaled));
    return 0;
}
