import QtQuick
import org.kde.plasma.private.volume

Item {
    id: root
    property var steps: []
    property int at: 0

    SoundFormats {
        id: f
        onApplied: (ok, what) => {
            console.log("RESULT " + JSON.stringify({ok: ok, what: what, message: f.message, graph: f.graph, user: f.userState, system: f.systemState}))
            root.next()
        }
    }

    function next() {
        if (at >= steps.length) {
            Qt.quit()
            return
        }
        const s = steps[at++]
        if (s.op === "apply") {
            f.apply(s.system === true, s.state, s.what)
        } else if (s.op === "dump") {
            f.refresh()
            console.log("DUMP " + JSON.stringify({name: s.name, engine: f.engine, graph: f.graph, user: f.userState, system: f.systemState, devices: f.devices, live: f.live}))
            next()
        } else if (s.op === "wait") {
            t.interval = s.ms
            t.start()
        }
    }

    Timer {
        id: t
        onTriggered: root.next()
    }

    Component.onCompleted: {
        const x = new XMLHttpRequest()
        x.open("GET", "file:///tmp/steps.json", false)
        x.send()
        steps = JSON.parse(x.responseText)
        next()
    }
}
