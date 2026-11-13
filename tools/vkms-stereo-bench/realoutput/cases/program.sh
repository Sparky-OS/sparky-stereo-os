# Any program of the root: PROGRAM (its command line), APPENV (extra NAME=VALUE words), APPWAIT (seconds before the grab).
# Every buffer it commits on a declared surface is recorded (raise WLREC_MAX until the log ends before the limit).
setmode sbs-full
mkdir -p /mnt/wl
env NODEVICE_SELECT=1 LD_PRELOAD=/mnt/wlrec.so WLREC_DIR=/mnt/wl WLREC_MAX=${WLREC_MAX:-64} ${APPENV:-} WAYLAND_DEBUG=client ${PROGRAM:?} > /mnt/app.out 2> /mnt/app.err &
ap=$!
sleep ${APPWAIT:-70}
grab app
passes app
kill -0 $ap 2>/dev/null && log "app alive" || log "app gone"
kill $ap 2>/dev/null
sleep 1
