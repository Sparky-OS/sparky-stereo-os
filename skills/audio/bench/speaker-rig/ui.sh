# ui.sh RESULT_SUBDIR STEP... : the real Sound page in System Settings in the private session (Xvfb, AT-SPI), driven by xdotool
set -u
export DISPLAY=:20 QT_QPA_PLATFORM=xcb QT_QUICK_BACKEND=software LIBGL_ALWAYS_SOFTWARE=1 QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 QT_ACCESSIBILITY=1
export LC_ALL=${SP_LANG:-C.UTF-8} LANGUAGE=${SP_LANGUAGE:-} QT_SCALE_FACTOR=${SP_SCALE:-1}
Xvfb :20 -screen 0 1500x1500x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
sleep 1
gdbus call --session --dest org.a11y.Bus --object-path /org/a11y/bus --method org.a11y.Bus.GetAddress >/dev/null
R=/ev/$1; shift; mkdir -p $R
systemsettings kcm_pulseaudio >$R/kcm.log 2>&1 &
sleep 6
PG_W=${PG_W:-1300} PG_H=${PG_H:-1450} python3 /src/ui.py $R "$@"
