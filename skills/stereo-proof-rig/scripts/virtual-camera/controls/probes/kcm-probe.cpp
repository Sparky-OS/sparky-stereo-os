// The installed Camera page's engine without its QML: the KCM plugin is loaded as System Settings loads it and driven through
// its own properties and invokables, the steps a person's clicks reach (open the page, choose a camera, move a control, pick a
// mode, Defaults, Apply). Each step prints one line: KEY VALUE (JSON for lists).
// Usage: QT_QPA_PLATFORM=offscreen kcm-probe PLUGIN.so STEP...   (steps: load, current=NODE, mode, controls, set=ID:VALUE,
//        setmode=FOURCC:W:H:FPS, defaults, save, notes, error; and with the page's own QML (mainUi, as System Settings shows it):
//        followers (the text of the item named "followers"), grab=FILE.png (the page drawn offscreen, QT_QUICK_BACKEND=software))
#include <KPluginFactory>
#include <KPluginMetaData>
#include <KQuickConfigModule>
#include <KQuickConfigModuleLoader>
#include <QElapsedTimer>
#include <QQmlEngine>
#include <memory>
#include <QGuiApplication>
#include <QJsonDocument>
#include <QJsonValue>
#include <QQuickItem>
#include <QQuickWindow>
#include <QVariant>
#include <cstdio>

namespace
{
QQuickItem *findNamed(QQuickItem *item, const QString &name)
{
    if (item->objectName() == name) {
        return item;
    }
    for (QQuickItem *child : item->childItems()) {
        if (QQuickItem *found = findNamed(child, name)) {
            return found;
        }
    }
    return nullptr;
}

QQuickWindow *pageWindow(KQuickConfigModule *kcm)
{
    static QQuickWindow *window = nullptr;
    if (window) {
        return window;
    }
    QQuickItem *ui = kcm->mainUi();
    if (!ui) {
        std::printf("NOUI %s\n", qPrintable(kcm->errorString()));
        return nullptr;
    }
    window = new QQuickWindow;
    window->resize(900, 1500);
    ui->setParentItem(window->contentItem());
    ui->setSize(QSizeF(900, 1500));
    bool drawn = false;
    QObject::connect(window, &QQuickWindow::frameSwapped, window, [&drawn]() {
        drawn = true;
    });
    window->show();
    // the state it needs, never a fixed time: the window exposed, the sentence's item made and a frame drawn (10 s at most)
    QElapsedTimer t;
    t.start();
    while (t.elapsed() < 10000 && !(window->isExposed() && drawn && findNamed(window->contentItem(), QStringLiteral("followers")))) {
        QCoreApplication::processEvents(QEventLoop::AllEvents, 50);
    }
    return window;
}
}

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    if (argc < 3) {
        return 2;
    }
    const KPluginMetaData md(QString::fromLocal8Bit(argv[1]));
    // as System Settings loads a page: KCMUtils' loader with a QML engine of its own (mainUi needs its context)
    const auto engine = std::make_shared<QQmlEngine>();
    auto result = KQuickConfigModuleLoader::loadModule(md, nullptr, {}, engine);
    if (!result) {
        std::printf("NOPLUGIN %s\n", qPrintable(result.errorString));
        return 3;
    }
    KQuickConfigModule *kcm = result.plugin;
    for (int i = 2; i < argc; ++i) {
        const QString step = QString::fromLocal8Bit(argv[i]);
        if (step == QLatin1String("load")) {
            kcm->load();
            std::printf("load done\n");
        } else if (step == QLatin1String("save")) {
            kcm->save();
            std::printf("save done\n");
        } else if (step == QLatin1String("defaults")) {
            kcm->defaults();
            std::printf("defaults done\n");
        } else if (step.startsWith(QLatin1String("current="))) {
            kcm->setProperty("current", step.mid(8));
            std::printf("current %s\n", qPrintable(kcm->property("current").toString()));
        } else if (step == QLatin1String("mode")) {
            const QVariantMap m = kcm->property("mode").toMap();
            std::printf("mode %s %d %d %g\n", qPrintable(m.value(QStringLiteral("fourcc")).toString()), m.value(QStringLiteral("width")).toInt(),
                        m.value(QStringLiteral("height")).toInt(), m.value(QStringLiteral("fps")).toDouble());
        } else if (step == QLatin1String("controls")) {
            std::printf("controls %s\n", QJsonDocument::fromVariant(kcm->property("controls")).toJson(QJsonDocument::Compact).constData());
        } else if (step == QLatin1String("notes")) {
            std::printf("notes %s\n", QJsonDocument::fromVariant(kcm->property("savedNotes")).toJson(QJsonDocument::Compact).constData());
        } else if (step == QLatin1String("followers")) {
            QQuickWindow *w = pageWindow(kcm);
            QQuickItem *label = w ? findNamed(w->contentItem(), QStringLiteral("followers")) : nullptr;
            std::printf("followers %s\n", label ? qPrintable(label->property("text").toString()) : "(no item named followers)");
        } else if (step.startsWith(QLatin1String("grab="))) {
            QQuickWindow *w = pageWindow(kcm);
            const QImage image = w ? w->grabWindow() : QImage();
            std::printf("grab %s %s\n", qPrintable(step.mid(5)), !image.isNull() && image.save(step.mid(5)) ? "saved" : "failed");
        } else if (step == QLatin1String("error")) {
            std::printf("error %s\n", qPrintable(kcm->property("modeError").toString()));
        } else if (step.startsWith(QLatin1String("set="))) {
            const QStringList p = step.mid(4).split(QLatin1Char(':'));
            QString answer;
            QMetaObject::invokeMethod(kcm, "setControl", Q_RETURN_ARG(QString, answer), Q_ARG(int, p.value(0).toInt()), Q_ARG(double, p.value(1).toDouble()));
            std::printf("set %s %s\n", qPrintable(step.mid(4)), answer.isEmpty() ? "ok" : qPrintable(answer));
        } else if (step.startsWith(QLatin1String("setmode="))) {
            const QStringList p = step.mid(8).split(QLatin1Char(':'));
            QMetaObject::invokeMethod(kcm, "setMode", Q_ARG(QString, p.value(0)), Q_ARG(int, p.value(1).toInt()), Q_ARG(int, p.value(2).toInt()),
                                      Q_ARG(double, p.value(3).toDouble()));
            std::printf("setmode %s\n", qPrintable(step.mid(8)));
        } else {
            std::printf("UNKNOWN %s\n", qPrintable(step));
            return 2;
        }
        std::fflush(stdout);
    }
    return 0;
}
