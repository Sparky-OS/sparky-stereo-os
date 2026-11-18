# ui.sh RESULT_SUBDIR STEP... : the real page in the private session (Xvfb, AT-SPI), driven by xdotool
set -u
export DISPLAY=:20 QT_QPA_PLATFORM=xcb QT_QUICK_BACKEND=software LIBGL_ALWAYS_SOFTWARE=1 QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 QT_ACCESSIBILITY=1
export LC_ALL=${PG_LANG:-C.UTF-8} LANGUAGE=${PG_LANGUAGE:-}
Xvfb :20 -screen 0 1500x1500x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
sleep 1
sleep 1
gdbus call --session --dest org.a11y.Bus --object-path /org/a11y/bus --method org.a11y.Bus.GetAddress >/dev/null
R=/ev/$1; shift; mkdir -p $R
mkdir -p $R
systemsettings kcm_pulseaudio >$R/kcm.log 2>&1 &
sleep 6
python3 /src/ui.py $R "$@"
