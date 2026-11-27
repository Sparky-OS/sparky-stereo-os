#!/bin/bash
# SPDX-License-Identifier: MIT
# real-login-kit.sh (run as root on a test machine, under its bench lock: flock -w 14400 LOCK sudo -n env PERSON=...
# DEB=... bash real-login-kit.sh): a real Plasma login of a fresh account starts the autostart entry of the staged
# sparky-stereo-systemmonitor. The machine's state first. SDDM's autologin is switched to the account by a drop-in in
# /etc/sddm.conf.d that links to a file in /run, so a restart of the machine midway falls back to its own autologin. In
# that session: the autostart unit's record, the user journal, the pages written, then System Monitor opened with
# accessibility on, put in full screen, read through AT-SPI and captured. Then the package is purged first (with its
# autostart entry installed, the machine's own session would run the probe when it returns), SDDM's own autologin put
# back, the account removed, and the state compared with the first one. Results in $KIT/out.
# PERSON: the machine's own autologin account (its System Monitor files are compared); ACCOUNT: the test account; KIT:
# the kit's folder (atspi_dump.py, capture.py and kwin_script.py beside this script; nothing in a home folder).
# Run on the A10 on 2026-11-27 as kit.sh with these names written in (PERSON its owner, ACCOUNT $ACCOUNT, KIT
# $KIT).
set -uo pipefail
PERSON=${PERSON:?set PERSON to the autologin account of the machine}
ACCOUNT=${ACCOUNT:-$ACCOUNT}
KIT=${KIT:-$KIT}
PHOME=$(getent passwd "$PERSON" | cut -d: -f6)
K=$KIT
O=$KIT/out
H=$KIT/home
DEB=${DEB:?set DEB to the staged sparky-stereo-systemmonitor package}
UNIT='app-sparky\x2dstereo\x2dsystemmonitor\x2dpages@autostart.service'
mkdir -p $KIT/out/start1 $KIT/out/pages
exec > $KIT/out/kit.log 2>&1
T0=$(date -Is)
step() { echo "== $(date -Is) $*"; }
as_user() {
	local u=$1 id; shift; id=$(id -u "$u")
	runuser -u "$u" -- env XDG_RUNTIME_DIR="/run/user/$id" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$id/bus" \
		WAYLAND_DISPLAY="${WL:-wayland-0}" "$@"
}
session_of() { loginctl list-sessions --no-legend | awk -v u="$1" '$3 == u && $4 == "seat0" {print $1}' | head -n 1; }
wait_for() {
	local i sid
	for i in $(seq 90); do
		sid=$(session_of "$1")
		if [ -n "$sid" ] && pgrep -u "$1" -x plasmashell > /dev/null; then echo "seat0 session $sid of $1, plasmashell up, after $((i * 2)) s"; return 0; fi
		sleep 2
	done
	echo "no seat0 session with plasmashell for $1 after 180 s"; loginctl list-sessions --no-legend; return 1
}
state() {
	{
		echo "packages installed: $(dpkg-query -W -f '${db:Status-Abbrev}\n' | grep -c '^ii')"
		dpkg-query -W sparky-stereo-systemmonitor sparky-stereo-systemmonitor-lc-hr 2>&1
		getent passwd $ACCOUNT || echo "no account $ACCOUNT"
		sha256sum /etc/sddm.conf /etc/sddm.conf.d/* /var/lib/sddm/state.conf 2>&1
		echo "sddm.conf.d: $(ls /etc/sddm.conf.d | tr '\n' ' ')"
		echo "autostart entries: $(ls /etc/xdg/autostart | wc -l), list $(ls /etc/xdg/autostart | sha256sum | cut -c1-16)"
		sha256sum "$PHOME"/.config/systemmonitorrc "$PHOME"/.local/share/plasma-systemmonitor/* 2>&1
		ls -d "$PHOME"/.local/state/sparky-stereo-systemmonitor 2>&1
		# the boot files sparky-stereo-boot writes from the seat0 session's display settings
		sha256sum /etc/default/sparky-stereo-boot /etc/default/grub.d/30-sparky-stereo-boot.cfg /boot/grub/grubenv 2>&1
		find /var/lib/sparky-stereo-boot /var/lib/sparky-stereo-problems -type f -exec sha256sum {} + 2>&1 | sort -k2
		echo "AccountsService users: $(ls -A /var/lib/AccountsService/users | tr '\n' ' ')"
		echo "failed units: $(systemctl --failed --no-legend | wc -l)"; systemctl --failed --no-legend
	} > "$1"
}
restore() {
	[ -n "${RESTORED:-}" ] && return; RESTORED=1
	step "restore"
	# the package goes first: with its autostart entry still installed, the machine's own autologin session would run
	# the probe into the person's folder when it returns (found on the first run of this kit, 2026-11-27)
	if [ -n "${INSTALLED:-}" ]; then
		DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 purge -y sparky-stereo-systemmonitor > "$O/apt-purge.txt" 2>&1
		echo "purge exit $?"
	fi
	if [ -n "${SWITCHED:-}" ]; then
		rm -f /etc/sddm.conf.d/zz-sm182-autologin.conf /run/sm182-autologin.conf
		systemctl restart sddm
		wait_for "$PERSON"
		loginctl list-sessions --no-legend > "$O/sessions-restored.txt"
	fi
	if [ -n "${CREATED:-}" ]; then
		loginctl terminate-user $ACCOUNT 2> /dev/null; sleep 5
		pkill -KILL -u $ACCOUNT 2> /dev/null; sleep 1
		userdel -r $ACCOUNT 2>&1 | grep -v 'mail spool' || true
		rm -f /var/lib/AccountsService/users/$ACCOUNT /var/lib/AccountsService/icons/$ACCOUNT
		find /tmp /dev/shm /run -xdev -maxdepth 2 -uid "$TUID" -print -delete 2> /dev/null > "$O/removed-uid-tmp.txt"
		find / /home -xdev -uid "$TUID" -not -path '$KIT/*' 2> /dev/null | head -n 50 > "$O/leftovers-uid.txt"
		echo "files of uid $TUID left: $(wc -l < "$O/leftovers-uid.txt")"
	fi
	if [ -f $KIT/state.conf.before ] && ! cmp -s $KIT/state.conf.before /var/lib/sddm/state.conf; then
		echo "sddm state.conf changed by the logins:"; diff $KIT/state.conf.before /var/lib/sddm/state.conf
		cp -p $KIT/state.conf.before /var/lib/sddm/state.conf; echo "state.conf put back"
	fi
	sleep 20
	state "$O/after.txt"
	if diff "$O/base.txt" "$O/after.txt" > "$O/state-diff.txt"; then echo "STATE EQUAL to the baseline"; else echo "STATE DIFFERS:"; cat "$O/state-diff.txt"; fi
	WL=wayland-0 as_user "$PERSON" sparky-stereo-problems list > "$O/problems-after.txt" 2>&1
	coredumpctl list --no-legend --since "$T0" > "$O/coredumps.txt" 2>&1
	echo "core dumps since $T0: $(grep -vc '^No coredumps' "$O/coredumps.txt")"
	chown -R "$PERSON:" $KIT/out
	step "done"
	touch $KIT/out/DONE
}
trap restore EXIT

step "baseline (bench lock taken)"
state "$O/base.txt"
cp -p /var/lib/sddm/state.conf $KIT/state.conf.before 2> /dev/null
{
	date -Is; uptime; uname -r; loginctl list-sessions --no-legend
	echo "--- /etc/sddm.conf.d/kde_settings.conf"; cat /etc/sddm.conf.d/kde_settings.conf
	for s in /sys/class/drm/card*-*/status; do echo "$s $(cat "$s")"; done
} > "$O/context.txt"
WL=wayland-0 as_user "$PERSON" sparky-stereo-problems list > "$O/problems-before.txt" 2>&1
cat "$O/base.txt"

step "install the staged package"
apt-get -o DPkg::Lock::Timeout=600 -s install --no-install-recommends "$DEB" > "$O/apt-plan.txt" 2>&1
grep -E '^[0-9]+ upgraded' "$O/apt-plan.txt"
grep -q ' 0 to remove' "$O/apt-plan.txt" || { echo "the apt plan removes packages: stop"; exit 1; }
DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y --no-install-recommends "$DEB" > "$O/apt-install.txt" 2>&1 || { echo "install failed"; exit 1; }
INSTALLED=1
dpkg-query -W sparky-stereo-systemmonitor >> "$O/apt-install.txt"
sha256sum /usr/libexec/sparky-stereo-systemmonitor/overview-pages /etc/xdg/autostart/sparky-stereo-systemmonitor-pages.desktop >> "$O/apt-install.txt"
tail -n 3 "$O/apt-install.txt"

step "fresh account"
useradd -m -d $KIT/home -s /bin/bash -c "row 182 test" -G video,render $ACCOUNT || { echo "useradd failed"; exit 1; }
CREATED=1; TUID=$(id -u $ACCOUNT); id $ACCOUNT
# capture only: KWin lets a client take screenshots in this account's session (its own environment script)
install -d -o $ACCOUNT -g $ACCOUNT $KIT/home/.config/plasma-workspace/env $KIT/home/cap
printf 'export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1\n' > $KIT/home/.config/plasma-workspace/env/sm182-capture.sh
chown $ACCOUNT:$ACCOUNT $KIT/home/.config/plasma-workspace/env/sm182-capture.sh
find $KIT/home -printf '%M %u %p\n' | sort -k3 > "$O/home-before-login.txt"

step "autologin switched to $ACCOUNT, SDDM restarted"
printf '[Autologin]\nUser=$ACCOUNT\nSession=plasma\nRelogin=false\n' > /run/sm182-autologin.conf
ln -s /run/sm182-autologin.conf /etc/sddm.conf.d/zz-sm182-autologin.conf
SWITCHED=1
T1=$(date -Is)
systemctl restart sddm
wait_for $ACCOUNT || exit 1
sleep 30

step "the session and its autostart"
SID=$(session_of $ACCOUNT)
loginctl show-session "$SID" -p Name -p Type -p Class -p Desktop -p Service -p Seat -p VTNr -p Active -p State -p Remote > "$O/session.txt"
cat "$O/session.txt"
systemctl --user -M $ACCOUNT@ show-environment > "$O/user-env-all.txt" 2>&1
grep -E '^(XDG_CURRENT_DESKTOP|XDG_SESSION_TYPE|XDG_SESSION_DESKTOP|DESKTOP_SESSION|WAYLAND_DISPLAY|LANG|KDE_FULL_SESSION|KWIN_SCREENSHOT_NO_PERMISSION_CHECKS)=' "$O/user-env-all.txt" | tee "$O/user-env.txt"
WL=$(sed -n 's/^WAYLAND_DISPLAY=//p' "$O/user-env-all.txt"); WL=${WL:-wayland-0}
systemctl --user -M $ACCOUNT@ show "$UNIT" -p Id -p LoadState -p ActiveState -p SubState -p Result -p ExecMainStatus \
	-p ExecMainStartTimestamp -p ExecMainExitTimestamp -p SourcePath -p Description > "$O/autostart-unit.txt" 2>&1
cat "$O/autostart-unit.txt"
systemctl --user -M $ACCOUNT@ list-units --all --no-legend 'app-*@autostart.service' > "$O/autostart-units.txt" 2>&1
journalctl -b --since "$T1" _UID="$TUID" --no-pager -o short-iso > "$O/user-journal.txt" 2>&1
grep -E 'systemmonitor|overview-pages' "$O/user-journal.txt" > "$O/user-journal-ours.txt"; cat "$O/user-journal-ours.txt"
find $KIT/home/.local $KIT/home/.config -path '*plasma-systemmonitor*' -o -name systemmonitorrc -o -path '*sparky-stereo-systemmonitor*' 2> /dev/null \
	| xargs -r ls -la --time-style=full-iso > "$O/written.txt" 2>&1
cat "$O/written.txt"
cp -p $KIT/home/.local/share/plasma-systemmonitor/*.page "$O/pages/" 2> /dev/null
cp -p $KIT/home/.config/systemmonitorrc "$O/systemmonitorrc.login" 2> /dev/null
cp -rp $KIT/home/.local/state/sparky-stereo-systemmonitor "$O/state" 2> /dev/null
as_user $ACCOUNT /usr/libexec/sparky-stereo-systemmonitor/overview-pages --explain > "$O/explain.txt" 2>&1

step "System Monitor opened in the session"
systemd-run --user -M $ACCOUNT@ --unit=sm182-sysmon --setenv=QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 /usr/bin/plasma-systemmonitor
sleep 15
# full screen, so the window's surface starts at the screen's corner and AT-SPI's window boxes are screen positions (the
# atspi dump's frame box then equals the screen's size); a KWin script through the session's own D-Bus
as_user $ACCOUNT python3 $KIT/kwin_script.py x 'for (const w of workspace.windowList()) { if (w.resourceClass.indexOf("systemmonitor") >= 0) { w.fullScreen = true; workspace.activeWindow = w; } }' > "$O/start1/fullscreen.log" 2>&1
sleep 10
as_user $ACCOUNT kreadconfig6 --file kdeglobals --group General --key font > "$O/session-font.txt" 2>&1
cp -p $KIT/home/.config/kdeglobals "$O/session-kdeglobals" 2> /dev/null
as_user $ACCOUNT python3 $KIT/atspi_dump.py plasma-systemmonitor $KIT/home/cap/atspi.json > "$O/start1/atspi.log" 2>&1
as_user $ACCOUNT python3 $KIT/capture.py $KIT/home/cap/screen.png > "$O/start1/capture.log" 2>&1
as_user $ACCOUNT kstatsviewer --list > $KIT/home/cap/sensors-all.txt 2> "$O/kstatsviewer.err"
as_user $ACCOUNT sparky-stereo-problems list > "$O/problems-session.txt" 2>&1
cp $KIT/home/cap/atspi.json $KIT/home/cap/screen.png "$O/start1/" 2> /dev/null
cp $KIT/home/cap/sensors-all.txt "$O/sensors-all.txt"
grep -E '^(gpu|memory|cpu/(all|cpu[0-9]+)/usage)' "$O/sensors-all.txt" > "$O/sensors.txt"
cp -p $KIT/home/.config/systemmonitorrc "$O/start1/systemmonitorrc" 2> /dev/null
for p in $(pgrep -u $ACCOUNT -x ksystemstats); do echo "pid $p ppid $(ps -o ppid= -p "$p")"; done > "$O/start1/ksystemstats-ps.txt"
ls -la "$O/start1"
systemctl --user -M $ACCOUNT@ stop sm182-sysmon
exit 0
