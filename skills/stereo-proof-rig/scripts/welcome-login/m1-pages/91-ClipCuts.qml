// ORDER 63 M1 rig page: a StereoPicture in an item that clips it, 106 pixels taken from each side. Both 1.23.3 and
// 1.23.4 draw it flat (the left view, clipped); 1.23.4 says why once in the log.
import QtQuick
import org.kde.plasma.welcome as Welcome
import org.sparky.stereo
Welcome.Page {
    heading: "A clip that cuts the picture"
    description: ""
    Item {
        objectName: "cut"
        anchors.centerIn: parent
        width: 188
        height: 312
        clip: true
        StereoPicture {
            id: picture
            x: -106
            width: 400
            height: 312
            source: "file:///diag/any-screen.pns"
        }
    }
    Timer {
        interval: 4000
        running: true
        onTriggered: console.log("DIAG cuts stereoActive=" + picture.stereoActive + " failure=[" + picture.stereoFailure + "]")
    }
}
