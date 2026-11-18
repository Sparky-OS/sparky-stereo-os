workspace.windowAdded.connect(function (w) {
    print("POPUPLOG t=" + Date.now() + " class=" + w.resourceClass + " menu=" + w.popupMenu + " dropdown=" + w.dropdownMenu + " popup=" + w.popupWindow + " tooltip=" + w.tooltip + " x=" + Math.round(w.frameGeometry.x) + " y=" + Math.round(w.frameGeometry.y) + " w=" + Math.round(w.frameGeometry.width) + " h=" + Math.round(w.frameGeometry.height));
});
