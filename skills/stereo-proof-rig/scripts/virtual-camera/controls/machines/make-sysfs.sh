#!/bin/sh
# A fake sysfs for fixture (e): this computer is a Sony VAIO Duo 13 (DMI product SVD13217CBW) and /dev/video34 is its USB camera
# 0bda:5722. The real known-machines command reads it with --sysfs-root; sparky-stereo-camera with SPARKY_STEREO_CAMERA_SYSFS.
# Usage: make-sysfs.sh DIR [vaio|other]
set -eu
root=$1; kind=${2:-vaio}
rm -rf "$root"; mkdir -p "$root/class/dmi/id" "$root/bus/usb/devices/1-7/1-7:1.0" "$root/class/video4linux/video34"
[ "$kind" = vaio ] && echo SVD13217CBW >"$root/class/dmi/id/product_name" || echo "Other Laptop" >"$root/class/dmi/id/product_name"
echo 0bda >"$root/bus/usb/devices/1-7/idVendor"; echo 5722 >"$root/bus/usb/devices/1-7/idProduct"
ln -s ../../../bus/usb/devices/1-7/1-7:1.0 "$root/class/video4linux/video34/device"
