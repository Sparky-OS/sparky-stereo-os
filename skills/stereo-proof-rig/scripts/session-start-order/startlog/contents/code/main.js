// Records the session start. Loaded by kwinrc [Plugins] startlogEnabled=true, so it runs from KWin's first moment.
function ts() { return Date.now() / 1000; }
function active() { return workspace.activeScreen ? workspace.activeScreen.name : "none"; }
function d(w) {
    if (!w) return "null";
    return w.resourceClass + " '" + w.caption + "' type=" + w.windowType + " normal=" + w.normalWindow + " desktop=" + w.desktopWindow + " dock=" + w.dock + " out=" + (w.output ? w.output.name : "?") + " pid=" + w.pid;
}
function log(m) { print("STARTLOG " + ts().toFixed(3) + " active=" + active() + " " + m); }
log("script loaded; screens=" + workspace.screens.map(function (o) { return o.name; }).join(","));
workspace.windowActivated.connect(function (w) { log("ACTIVATED " + d(w)); });
workspace.windowAdded.connect(function (w) { log("ADDED " + d(w)); w.outputChanged.connect(function () { log("OUTPUT-CHANGED " + d(w)); }); });
workspace.windowRemoved.connect(function (w) { log("REMOVED " + d(w)); });
workspace.screensChanged.connect(function () { log("SCREENS-CHANGED"); });
