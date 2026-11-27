# scenario-locale.sh, sourced by session.sh with METERED_AT_START=metered: the integration's own strings in the session's
# language without signing in (the metered notice, the tray's tooltip and menu, the window's banner and labels).
start_app
sleep 15
python3 /lane/atspi.py tree drivesync > "$CASE/atspi-locale.txt" 2>&1
ITEM=$(gdbus call --session --dest org.kde.StatusNotifierWatcher --object-path /StatusNotifierWatcher --method org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems | grep -o "org.kde.StatusNotifierItem-[0-9]*-[0-9]*" | head -1)
mark "tray item: ${ITEM:-none}"
if [ -n "$ITEM" ]; then
	{ gdbus call --session --dest "$ITEM" --object-path /StatusNotifierItem --method org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierItem ToolTip
	  gdbus call --session --dest "$ITEM" --object-path /MenuBar --method com.canonical.dbusmenu.GetLayout 0 -1 '[]'; } > "$CASE/tray-locale.txt" 2>&1
fi
shot locale
