import QtQuick
import org.kde.plasma.private.volume

Item {
    id: root
    property var steps: []
    property int at: 0

    SpeakerSetup {
        id: s
        onApplied: (ok, node) => {
            console.log("RESULT " + JSON.stringify({ok: ok, node: node, message: s.message, user: s.userState, system: s.systemState, defaultSink: s.defaultSink}))
            root.next()
        }
    }

    function next() {
        if (at >= steps.length) {
            Qt.quit()
            return
        }
        const st = steps[at++]
        if (st.op === "apply") {
            s.apply(st.system === true, st.state, st.node, st.makeDefault !== false)
        } else if (st.op === "dump") {
            s.refresh()
            console.log("DUMP " + JSON.stringify({name: st.name, devices: s.devices, user: s.userState, system: s.systemState, defaultSink: s.defaultSink, testing: s.testing, testRunning: s.testRunning, message: s.message}))
            next()
        } else if (st.op === "wait") {
            t.interval = st.ms
            t.start()
        } else if (st.op === "test") {
            if (st.position === "all") {
                s.testAll(st.node)
            } else {
                s.testChannel(st.node, st.position)
            }
            next()
        } else if (st.op === "stop") {
            s.stopTest()
            next()
        } else if (st.op === "seconds") {
            s.testSeconds = st.value
            next()
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
