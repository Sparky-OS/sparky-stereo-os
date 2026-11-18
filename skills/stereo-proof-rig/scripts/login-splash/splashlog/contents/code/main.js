// SPDX-License-Identifier: MIT
// Logs every window of a login with its geometry, so the rig reads geometry from KWin, never from the picture.
function ts() { return (Date.now() / 1000).toFixed(3); }
function d(w) {
    if (!w) return "null";
    var g = w.frameGeometry;
    return w.resourceClass + " type=" + w.windowType + " desktop=" + w.desktopWindow + " dock=" + w.dock + " keepAbove=" + w.keepAbove
        + " out=" + (w.output ? w.output.name : "?") + " geo=" + g.x + "," + g.y + "," + g.width + "x" + g.height + " pid=" + w.pid + " wid=" + w.internalId;
}
function log(m) { print("SPLASHLOG " + ts() + " active=" + (workspace.activeWindow ? workspace.activeWindow.resourceClass : "none") + " " + m); }
log("loaded screens=" + workspace.screens.map(function (o) { return o.name + "@" + o.geometry.x + "," + o.geometry.y + "," + o.geometry.width + "x" + o.geometry.height; }).join(" "));
workspace.windowAdded.connect(function (w) { log("ADDED " + d(w)); });
workspace.windowRemoved.connect(function (w) { log("REMOVED " + d(w)); });
workspace.windowActivated.connect(function (w) { log("ACTIVATED " + d(w)); });
