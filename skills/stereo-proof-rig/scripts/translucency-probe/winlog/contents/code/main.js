// SPDX-License-Identifier: MIT
// Prints every window once with its kind and frame; the rig reads geometry from KWin, never from the picture.
var tag = "TAGVALUE";
var ws = workspace.stackingOrder;
for (var i = 0; i < ws.length; i++) {
    var w = ws[i], g = w.frameGeometry;
    print("PROBEWIN " + tag + " " + JSON.stringify({cls: w.resourceClass, caption: w.caption, type: w.windowType,
        dock: w.dock, notification: w.notification, criticalNotification: w.criticalNotification, tooltip: w.tooltip,
        popup: w.popupWindow, dialog: w.dialog, normal: w.normalWindow, desktop: w.desktopWindow, active: w.active,
        opacity: w.opacity, x: g.x, y: g.y, w: g.width, h: g.height, out: w.output ? w.output.name : "?"}));
}
print("PROBEWIN " + tag + " END");
