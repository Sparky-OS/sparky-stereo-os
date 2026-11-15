// SPDX-License-Identifier: GPL-2.0-or-later
// Test-only observer of the installed KCM's real Qt Quick controls.
#include <QCoreApplication>
#include <QApplication>
#include <QQuickWidget>
#include <QFile>
#include <QGuiApplication>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointer>
#include <QQuickItem>
#include <QQuickWindow>
#include <QRegularExpression>
#include <QTimer>

static QStringList modelStrings(QObject *object)
{
    QStringList result;
    if (object->metaObject()->indexOfMethod("textAt(int)") < 0) {
        return result;
    }
    const int count = object->property("count").toInt();
    if (count < 1 || count > 512) {
        return result;
    }
    for (int index = 0; index < count; ++index) {
        QString text;
        if (!QMetaObject::invokeMethod(object, "textAt", Q_RETURN_ARG(QString, text), Q_ARG(int, index))) {
            qFatal("KCM fixture cannot read ComboBox textAt");
        }
        result.append(text);
    }
    return result;
}

class Observer : public QObject
{
public:
    QString path = qEnvironmentVariable("KSCREEN_MODE_CAPTURE_OUT");
    QPointer<QQuickWindow> window;
    QPointer<QWidget> widget;
    QPointer<QObject> resolution;
    QPointer<QObject> refresh;
    QStringList resolutions;
    QJsonArray rows;
    int attempts = 0;
    int index = 0;
    int interlacedIndex = -1;

    void save(const QString &suffix)
    {
        if (!window || !(widget ? widget->grab().toImage() : window->grabWindow()).save(path + suffix + QStringLiteral(".png"))) {
            qFatal("KCM fixture cannot capture the rendered window");
        }
    }

    void scan()
    {
        QList<QQuickWindow *> windows;
        for (QWidget *candidate : QApplication::allWidgets()) {
            if (auto quickWidget = qobject_cast<QQuickWidget *>(candidate); quickWidget && quickWidget->isVisible()) {
                windows.append(quickWidget->quickWindow());
                widget = quickWidget->window();
            }
        }
        for (QWindow *candidate : QGuiApplication::allWindows()) {
            if (auto quick = qobject_cast<QQuickWindow *>(candidate); quick && quick->isVisible()) {
                windows.append(quick);
            }
        }
        for (QQuickWindow *quick : windows) {
            QList<QQuickItem *> items{quick->contentItem()};
            for (qsizetype i = 0; i < items.size(); ++i) {
                items.append(items[i]->childItems());
            }
            for (QQuickItem *item : items) {
                const QString text = item->property("currentText").toString();
                if (attempts == 3 && !text.isEmpty()) {
                    qInfo() << item->metaObject()->className() << text << modelStrings(item);
                }
                if (modelStrings(item).isEmpty()) {
                    continue;
                }
                if (text.contains(QRegularExpression(QStringLiteral("[0-9]\\s*[×x]\\s*[0-9]")))) {
                    resolution = item;
                    window = quick;
                } else if (text.contains(QStringLiteral("Hz"))) {
                    refresh = item;
                }
            }
        }
        if (!resolution || !refresh || !window) {
            if (++attempts > 100) {
                qFatal("KCM fixture cannot find resolution and refresh controls");
            }
            QTimer::singleShot(200, this, [this]() { scan(); });
            return;
        }
        if (widget) { widget->resize(1150, 1000); }
        resolutions = modelStrings(resolution);
        for (int i = 0; i < resolutions.size(); ++i) {
            if (resolutions[i].contains(QStringLiteral("1080i"))) {
                interlacedIndex = i;
            }
        }
        QObject *popup = resolution->property("popup").value<QObject *>();
        if (!popup || !QMetaObject::invokeMethod(popup, "open")) {
            qFatal("KCM fixture cannot open resolution list");
        }
        QTimer::singleShot(600, this, [this, popup]() {
            save(QStringLiteral("-resolutions"));
            QMetaObject::invokeMethod(popup, "close");
            next();
        });
    }

    void next()
    {
        if (index == resolutions.size()) {
            QFile file(path + QStringLiteral(".json"));
            if (!file.open(QIODevice::WriteOnly)) {
                qFatal("KCM fixture cannot write observed rows");
            }
            file.write(QJsonDocument(QJsonObject{{"resolutions", QJsonArray::fromStringList(resolutions)}, {"rows", rows}}).toJson());
            if (interlacedIndex >= 0) {
                resolution->setProperty("currentIndex", interlacedIndex);
                QMetaObject::invokeMethod(resolution, "activated", Q_ARG(int, interlacedIndex));
            }
            QTimer::singleShot(300, this, [this]() {
                QObject *popup = refresh->property("popup").value<QObject *>();
                if (popup) {
                    QMetaObject::invokeMethod(popup, "open");
                }
                QTimer::singleShot(600, this, [this]() { save(QStringLiteral("-refresh")); QCoreApplication::exit(0); });
            });
            return;
        }
        resolution->setProperty("currentIndex", index);
        if (!QMetaObject::invokeMethod(resolution, "activated", Q_ARG(int, index))) {
            qFatal("KCM fixture cannot select a resolution");
        }
        QTimer::singleShot(100, this, [this]() {
            rows.append(QJsonObject{{"resolution", resolutions[index]}, {"refreshRates", QJsonArray::fromStringList(modelStrings(refresh))}});
            ++index;
            next();
        });
    }
};

static void startObserver()
{
    if (!qEnvironmentVariableIsSet("KSCREEN_MODE_CAPTURE_OUT")) {
        return;
    }
    auto observer = new Observer;
    observer->setParent(QCoreApplication::instance());
    QTimer::singleShot(1000, observer, [observer]() { observer->scan(); });
}
Q_COREAPP_STARTUP_FUNCTION(startObserver)
