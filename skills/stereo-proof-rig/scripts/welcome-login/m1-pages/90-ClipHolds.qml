// ORDER 63 M1 rig page: a StereoPicture inside a Welcome page, which clips, in Kirigami's ColumnView, which clips; both
// clips hold the whole picture. stereo-layer 1.23.3 shows one view here; 1.23.4 shows the pair.
import QtQuick
import org.kde.plasma.welcome as Welcome
import org.sparky.stereo
Welcome.Page {
    heading: "A clip that holds the picture"
    description: ""
    StereoPicture {
        id: picture
        anchors.centerIn: parent
        width: 400
        height: 312
        source: "file:///diag/any-screen.pns"
    }
    Timer {
        interval: 4000
        running: true
        onTriggered: console.log("DIAG holds stereoActive=" + picture.stereoActive + " failure=[" + picture.stereoFailure + "]")
    }
}
