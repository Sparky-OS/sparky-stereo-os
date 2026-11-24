#!/bin/sh
# A virtual camera for the rig: a PipeWire Video/Source node provided by GStreamer's pipewiresink.
# Usage: virtual-camera.sh a|b|sbs|held|jpeg   (a: many formats and sizes; b: one fixed mode; sbs: a packed side-by-side picture, left red, right blue; held: a camera whose stream another program holds, so it refuses a new size; jpeg: a camera that offers only 8-bit grey pictures, which the preview does not take, so it cannot start)
# A non-breaking space in a description: gst-launch splits its arguments at every plain space.
# The node carries api.v4l2.path, the property PipeWire's V4L2 source gives a real camera, so the page finds its controls.
set -eu
. "$XDG_RUNTIME_DIR/env.sh"
kind=$1
case $kind in
a)
	exec gst-launch-1.0 videotestsrc is-live=true pattern=smpte ! 'video/x-raw,format={YUY2,NV12,I420,BGRx},width=[160,1920],height=[120,1080],framerate=[1/1,60/1]' ! pipewiresink mode=provide use-bufferpool=false stream-properties='props,media.class=Video/Source,node.name=cam-a,node.description="Virtual camera A",api.v4l2.path=/dev/video20,object.path=v4l2:/dev/video20,device.api=v4l2' ;;
b)
	exec gst-launch-1.0 videotestsrc is-live=true pattern=ball ! 'video/x-raw,format=BGRx,width=640,height=480,framerate=30/1' ! pipewiresink mode=provide use-bufferpool=false stream-properties='props,media.class=Video/Source,node.name=cam-b,node.description="Virtual camera B",api.v4l2.path=/dev/video21,object.path=v4l2:/dev/video21,device.api=v4l2' ;;
held)
	exec gst-launch-1.0 videotestsrc is-live=true pattern=snow ! 'video/x-raw,format=BGRx,width=640,height=480,framerate=30/1' ! pipewiresink mode=provide use-bufferpool=false stream-properties='props,media.class=Video/Source,node.name=cam-held,node.description="Virtual camera held",api.v4l2.path=/dev/video23,object.path=v4l2:/dev/video23,device.api=v4l2' ;;
jpeg)
	exec gst-launch-1.0 videotestsrc is-live=true pattern=ball ! 'video/x-raw,format=GRAY8,width=640,height=480,framerate=30/1' ! pipewiresink mode=provide use-bufferpool=false stream-properties='props,media.class=Video/Source,node.name=cam-jpeg,node.description="Virtual camera JPEG",api.v4l2.path=/dev/video24,object.path=v4l2:/dev/video24,device.api=v4l2' ;;
sbs)
	exec gst-launch-1.0 compositor name=m sink_1::xpos=640 ! 'video/x-raw,format=BGRx,width=1280,height=480,framerate=30/1' ! pipewiresink mode=provide use-bufferpool=false stream-properties='props,media.class=Video/Source,node.name=cam-sbs,node.description="Virtual two-lens camera",api.v4l2.path=/dev/video22,object.path=v4l2:/dev/video22,device.api=v4l2' videotestsrc is-live=true pattern=red ! 'video/x-raw,width=640,height=480,framerate=30/1' ! textoverlay text=LEFT font-desc="Sans 60" ! m.sink_0 videotestsrc is-live=true pattern=blue ! 'video/x-raw,width=640,height=480,framerate=30/1' ! textoverlay text=RIGHT font-desc="Sans 60" ! m.sink_1 ;;
esac
