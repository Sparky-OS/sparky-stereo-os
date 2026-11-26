// The installed Camera page's engine without its QML: the KCM plugin is loaded as System Settings loads it and driven through
// its own properties and invokables, the steps a person's clicks reach (open the page, choose a camera, move a control, pick a
// mode, Defaults, Apply). Each step prints one line: KEY VALUE (JSON for lists).
// Usage: QT_QPA_PLATFORM=offscreen kcm-probe PLUGIN.so STEP...   (steps: load, current=NODE, mode, controls, set=ID:VALUE,
//        setmode=FOURCC:W:H:FPS, defaults, save, notes, error)
#include <KPluginFactory>
#include <KPluginMetaData>
#include <KQuickConfigModule>
#include <QGuiApplication>
#include <QJsonDocument>
#include <QJsonValue>
#include <QVariant>
#include <cstdio>

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    if (argc < 3) {
        return 2;
    }
    const KPluginMetaData md(QString::fromLocal8Bit(argv[1]));
    auto result = KPluginFactory::instantiatePlugin<KQuickConfigModule>(md, nullptr);
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
