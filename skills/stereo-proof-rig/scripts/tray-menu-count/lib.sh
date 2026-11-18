export DOCKER_HOST=unix:///K3D/partners/queue/gaming-rig-steps-108/docker.sock
M=/var/tmp/gaming-rig-steps-108/m12
X() { docker exec -u rig "$C" bash -c ". /home/rig/env.sh; $*"; }
D() { docker exec -u rig "$C" bash /t2/"$@"; }
crop() { python3 -c "
from PIL import Image
Image.open('$M/out/$C/$1.png').crop(($2,$3,$4,$5)).save('$M/out/$C/$1c.png')"; }
prep() { # all three entries always shown in the tray, plasmashell restarted
 X 'pkill -x plasmashell; sleep 3; f=~/.config/plasma-org.kde.plasma.desktop-appletsrc; grep -q shownItems $f || sed -i "/^\[Containments\]\[[0-9]*\]\[Applets\]\[[0-9]*\]\[General\]/a shownItems=org.kde.plasma.clipboard,org.kde.plasma.devicenotifier,org.sparky.stereo.headset" $f; (env XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 XDG_SESSION_TYPE=wayland QT_QPA_PLATFORM=wayland plasmashell >/tmp/ps.log 2>&1 &); sleep 15'
}
popups() { docker exec "$C" bash -c 'grep -c "POPUPLOG.*menu=true" /tmp/xdg-rig/kwin.log'; }
# menus of the applet = popup windows that are not the tray's own three-line menu (218x100)
appmenus() { docker exec "$C" bash -c 'grep POPUPLOG /tmp/xdg-rig/kwin.log | grep "popup=true" | grep -vc "w=218 h=100"'; }
trays() { docker exec "$C" bash -c 'grep POPUPLOG /tmp/xdg-rig/kwin.log | grep -c "w=218 h=100"'; }
# scenarios: NAME X [SELX SELY]; counts menus of the entry (applet menus), from KWin's log of popup windows
S1() { local B=$(appmenus); local Q="m:900,500 s:300 m:$(( $2 - 1 )),871 s:300 m:$2,870 b:273 s:1500 k:1 s:800"; D click.sh $Q $Q $Q $Q $Q $Q $Q $Q $Q $Q >/dev/null 2>&1; echo "$1 ten right clicks in a row: $(( $(appmenus) - B )) menus of 10"; }
S2() { local B=$(appmenus); local Q="m:900,500 s:300 m:$(( $2 - 1 )),871 s:300 m:$2,870 b:273 s:1500 k:1 s:800 m:$(( $2 - 1 )),871 s:300 m:$2,870 b:272 s:1800 k:1 s:800"; D click.sh $Q $Q $Q $Q $Q $Q $Q $Q $Q $Q >/dev/null 2>&1; echo "$1 right click after a left click, 10 rounds: $(( $(appmenus) - B )) menus of 10"; }
S3() { local B=$(appmenus); local Q="m:900,500 s:300 m:$(( $2 - 1 )),871 s:300 m:$2,870 b:273 s:1500 m:$3,$4 s:400 b:272 s:1500"; D click.sh $Q $Q $Q $Q $Q $Q $Q $Q $Q $Q >/dev/null 2>&1; D click.sh k:1 s:400 k:1 s:400 >/dev/null 2>&1; echo "$1 right click then choose a menu entry, 10 rounds: $(( $(appmenus) - B )) menus of 10"; }
# NOT the default: counting windows of an exact menu size read 0 for two entries in a fresh shell (the size of a menu changes with what the shell has
# loaded). The size-independent count above (S1, S2, S3 with appmenus and trays) is the one to keep; trays counts the tray's own 218x100 menu, the
# complement of the applet's menus in S1. In S2 the popup of the left click is a window too (read 11 for 10 rounds).
