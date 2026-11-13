# A real two-layer Vulkan client on software Vulkan: SWAPCHAINS swapchains of FRAMES frames each, every commit recorded.
setmode sbs-full
mkdir -p /mnt/wl
env NODEVICE_SELECT=1 LD_PRELOAD=/mnt/wlrec.so WLREC_DIR=/mnt/wl WLREC_MAX=40 SWAPCHAINS=${SWAPCHAINS:-3} FRAMES=${FRAMES:-3} HOLD=30 WAYLAND_DEBUG=client /mnt/vk2layer > /mnt/app.out 2> /mnt/app.err &
ap=$!
sleep 14
grab app
passes app
kill -0 $ap 2>/dev/null && log "app alive" || log "app gone"
kill $ap 2>/dev/null
sleep 1
