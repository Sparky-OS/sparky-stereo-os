# Counting a tray entry's menus in a Plasma login (ORDER 108 milestones 12 and 13)

`popups.js` is a KWin script that prints every window added (`popupWindow`, geometry); `lib.sh` sends ten right clicks through one `fakeinput` connection per scenario and counts the menus from KWin's log, for stock entries as well as ours.
Use S1 (ten right clicks in a row), S2 (a left click between) and S3 (choosing a menu entry between) with `appmenus` and `trays`: the applet's menus are the popup windows that are not the tray's own 218x100 menu.
Do not count windows of an exact menu size: that count read 0 for two entries in a fresh shell. A left click or a chosen entry clears the stale press that causes the defect, so only S1 discriminates a broken tray.
Paths in `lib.sh` (`M`, the rig container's `/t2`) are the lane's; adapt them.
